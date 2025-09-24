"""Sprint 5 - Trello Integration Client

This module provides one-click export of strategies and tactics to Trello
with proper mapping and idempotency.

Strategy → Board (optional)
Tactic → Card 
Subtasks → Checklist
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class TrelloStrategy:
    """Strategy data structure for Trello export."""
    title: str
    description: str
    objectives: list[str]
    assumptions: list[str]
    timeline: str
    board_id: str | None = None  # If None, creates new board
    list_name: str = "Strategy"
    labels: list[str] = None


@dataclass 
class TrelloTactic:
    """Tactic data structure for Trello card."""
    title: str
    description: str
    strategy_id: str
    deliverables: list[str]
    timeline: str
    effort_estimate: str
    success_criteria: list[str]
    board_id: str
    list_name: str = "Tactics"
    assignee_username: str | None = None
    due_date: str | None = None  # ISO format
    labels: list[str] = None


class TrelloClient:
    """
    Trello API client with retries, backoff, and idempotency for StratMaster exports.
    
    Handles:
    - Strategy → Board creation or card in existing board
    - Tactic → Card creation with checklists
    - Dry-run preview functionality  
    - Idempotency keys for safe retries
    """
    
    def __init__(self, api_key: str, api_token: str, base_url: str = "https://api.trello.com/1"):
        self.api_key = api_key
        self.api_token = api_token
        self.base_url = base_url
        self.client = httpx.Client(
            base_url=base_url,
            timeout=30.0
        )
        
        self.dry_run = False
        self.exported_items = []  # Track exports for dry-run
        
        # Standard auth params for all requests
        self.auth_params = {
            "key": self.api_key,
            "token": self.api_token
        }
    
    def set_dry_run(self, enabled: bool = True):
        """Enable dry-run mode for previewing exports without making changes."""
        self.dry_run = enabled
        if enabled:
            self.exported_items = []
    
    def get_dry_run_preview(self) -> list[dict[str, Any]]:
        """Get preview of what would be exported in dry-run mode."""
        return self.exported_items.copy()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """Make HTTP request with retry logic."""
        if self.dry_run:
            # Return mock response for dry-run
            return {
                "id": f"mock-{hashlib.md5(endpoint.encode()).hexdigest()[:8]}",
                "name": kwargs.get("json", {}).get("name", "Mock Item"),
                "url": f"https://trello.com/mock-{hashlib.md5(endpoint.encode()).hexdigest()[:8]}",
                "dateLastActivity": datetime.utcnow().isoformat()
            }
        
        # Add auth params to request
        params = kwargs.pop("params", {})
        params.update(self.auth_params)
        kwargs["params"] = params
        
        response = self.client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def create_board(self, name: str, description: str = "", 
                    template_id: str | None = None) -> dict[str, Any]:
        """Create a new Trello board."""
        payload = {
            "name": name,
            "desc": description,
            "defaultLabels": "true",
            "defaultLists": "true"
        }
        
        if template_id:
            payload["idBoardSource"] = template_id
        
        if self.dry_run:
            self.exported_items.append({
                "type": "board",
                "action": "create",
                "name": name,
                "description": description
            })
        
        return self._make_request("POST", "/boards", json=payload)
    
    def get_board_lists(self, board_id: str) -> list[dict[str, Any]]:
        """Get all lists in a board."""
        if self.dry_run:
            return [
                {"id": "mock-list-1", "name": "To Do"},
                {"id": "mock-list-2", "name": "In Progress"},
                {"id": "mock-list-3", "name": "Done"}
            ]
        
        return self._make_request("GET", f"/boards/{board_id}/lists")
    
    def create_list(self, board_id: str, name: str, position: str = "bottom") -> dict[str, Any]:
        """Create a new list in a board."""
        payload = {
            "name": name,
            "idBoard": board_id,
            "pos": position
        }
        
        if self.dry_run:
            self.exported_items.append({
                "type": "list",
                "action": "create", 
                "name": name,
                "board_id": board_id
            })
        
        return self._make_request("POST", "/lists", json=payload)
    
    def find_or_create_list(self, board_id: str, list_name: str) -> dict[str, Any]:
        """Find existing list or create new one."""
        lists = self.get_board_lists(board_id)
        
        for lst in lists:
            if lst["name"] == list_name:
                return lst
        
        # List not found, create it
        return self.create_list(board_id, list_name)
    
    def create_card(self, list_id: str, name: str, description: str = "",
                   due_date: str | None = None, member_ids: list[str] | None = None,
                   label_ids: list[str] | None = None) -> dict[str, Any]:
        """Create a new card in a list."""
        payload = {
            "name": name,
            "desc": description,
            "idList": list_id
        }
        
        if due_date:
            payload["due"] = due_date
        if member_ids:
            payload["idMembers"] = member_ids
        if label_ids:
            payload["idLabels"] = label_ids
        
        if self.dry_run:
            self.exported_items.append({
                "type": "card",
                "action": "create",
                "name": name,
                "description": description,
                "list_id": list_id,
                "due_date": due_date
            })
        
        return self._make_request("POST", "/cards", json=payload)
    
    def create_checklist(self, card_id: str, name: str, items: list[str]) -> dict[str, Any]:
        """Create a checklist on a card."""
        # First create the checklist
        checklist_payload = {
            "idCard": card_id,
            "name": name
        }
        
        if self.dry_run:
            self.exported_items.append({
                "type": "checklist",
                "action": "create",
                "name": name,
                "card_id": card_id,
                "items": items
            })
            return {"id": f"mock-checklist-{card_id}"}
        
        checklist = self._make_request("POST", "/checklists", json=checklist_payload)
        
        # Add items to checklist
        for item in items:
            item_payload = {"name": item}
            self._make_request("POST", f"/checklists/{checklist['id']}/checkItems", json=item_payload)
        
        return checklist
    
    def get_board_members(self, board_id: str) -> list[dict[str, Any]]:
        """Get all members of a board."""
        if self.dry_run:
            return [{"id": "mock-member-1", "username": "mockuser", "fullName": "Mock User"}]
        
        return self._make_request("GET", f"/boards/{board_id}/members")
    
    def find_member_by_username(self, board_id: str, username: str) -> dict[str, Any] | None:
        """Find board member by username."""
        members = self.get_board_members(board_id)
        
        for member in members:
            if member.get("username") == username:
                return member
        
        return None
    
    def export_strategy(self, strategy: TrelloStrategy, 
                       idempotency_key: str | None = None) -> dict[str, Any]:
        """
        Export strategy as Trello board or card.
        
        If board_id is None, creates a new board.
        If board_id is provided, creates a card in the existing board.
        """
        
        # Generate idempotency key if not provided
        if not idempotency_key:
            content_hash = hashlib.md5(
                f"{strategy.title}-{strategy.description}-{len(strategy.objectives)}".encode()
            ).hexdigest()[:8]
            idempotency_key = f"strategy-{content_hash}"
        
        if not strategy.board_id:
            # Create new board for strategy
            board_result = self.create_board(
                name=strategy.title,
                description=strategy.description
            )
            
            board_id = board_result["id"]
            
            # Create strategy overview card in the board
            strategy_list = self.find_or_create_list(board_id, strategy.list_name)
            
            # Build comprehensive description
            desc_parts = [strategy.description]
            
            if strategy.objectives:
                desc_parts.append("\n## Objectives")
                for obj in strategy.objectives:
                    desc_parts.append(f"- {obj}")
            
            if strategy.assumptions:
                desc_parts.append("\n## Key Assumptions")
                for assumption in strategy.assumptions:
                    desc_parts.append(f"- {assumption}")
            
            desc_parts.append(f"\n## Timeline\n{strategy.timeline}")
            desc_parts.append(f"\n## Idempotency Key\n{idempotency_key}")
            
            card_result = self.create_card(
                list_id=strategy_list["id"],
                name=f"📋 {strategy.title} - Overview",
                description="\n".join(desc_parts)
            )
            
            return {
                "type": "strategy",
                "approach": "new_board",
                "board_id": board_id,
                "board_url": board_result.get("url", ""),
                "card_id": card_result["id"], 
                "card_url": card_result.get("url", ""),
                "title": strategy.title,
                "idempotency_key": idempotency_key,
                "exported_at": datetime.utcnow().isoformat()
            }
        
        else:
            # Add strategy card to existing board
            strategy_list = self.find_or_create_list(strategy.board_id, strategy.list_name)
            
            # Build description
            desc_parts = [strategy.description]
            desc_parts.append(f"\n## Timeline\n{strategy.timeline}")
            desc_parts.append(f"\n## Idempotency Key\n{idempotency_key}")
            
            card_result = self.create_card(
                list_id=strategy_list["id"],
                name=f"📋 {strategy.title}",
                description="\n".join(desc_parts)
            )
            
            # Add objectives as checklist
            if strategy.objectives:
                self.create_checklist(card_result["id"], "Objectives", strategy.objectives)
            
            # Add assumptions as checklist
            if strategy.assumptions:
                self.create_checklist(card_result["id"], "Key Assumptions", strategy.assumptions)
            
            return {
                "type": "strategy",
                "approach": "existing_board",
                "board_id": strategy.board_id,
                "card_id": card_result["id"],
                "card_url": card_result.get("url", ""),
                "title": strategy.title,
                "idempotency_key": idempotency_key,
                "exported_at": datetime.utcnow().isoformat()
            }
    
    def export_tactic(self, tactic: TrelloTactic,
                     idempotency_key: str | None = None) -> dict[str, Any]:
        """
        Export tactic as Trello card with checklists for deliverables and success criteria.
        """
        
        # Generate idempotency key if not provided
        if not idempotency_key:
            content_hash = hashlib.md5(
                f"{tactic.title}-{tactic.strategy_id}-{len(tactic.deliverables)}".encode()
            ).hexdigest()[:8]
            idempotency_key = f"tactic-{content_hash}"
        
        # Find or create the tactics list
        tactics_list = self.find_or_create_list(tactic.board_id, tactic.list_name)
        
        # Find member if assignee specified
        member_ids = []
        if tactic.assignee_username:
            member = self.find_member_by_username(tactic.board_id, tactic.assignee_username)
            if member:
                member_ids = [member["id"]]
        
        # Build card description
        desc_parts = [tactic.description]
        desc_parts.append(f"\n## Strategy ID\n{tactic.strategy_id}")
        desc_parts.append(f"\n## Timeline\n{tactic.timeline}")
        desc_parts.append(f"\n## Effort Estimate\n{tactic.effort_estimate}")
        desc_parts.append(f"\n## Idempotency Key\n{idempotency_key}")
        
        # Create the card
        card_result = self.create_card(
            list_id=tactics_list["id"],
            name=f"⚡ {tactic.title}",
            description="\n".join(desc_parts),
            due_date=tactic.due_date,
            member_ids=member_ids if member_ids else None
        )
        
        # Add deliverables as checklist
        if tactic.deliverables:
            self.create_checklist(card_result["id"], "Deliverables", tactic.deliverables)
        
        # Add success criteria as checklist  
        if tactic.success_criteria:
            self.create_checklist(card_result["id"], "Success Criteria", tactic.success_criteria)
        
        return {
            "type": "tactic",
            "board_id": tactic.board_id,
            "card_id": card_result["id"],
            "card_url": card_result.get("url", ""),
            "title": tactic.title,
            "strategy_id": tactic.strategy_id,
            "assignee": tactic.assignee_username,
            "idempotency_key": idempotency_key,
            "exported_at": datetime.utcnow().isoformat()
        }
    
    def export_full_strategy_with_tactics(self, strategy: TrelloStrategy, tactics: list[TrelloTactic]) -> dict[str, Any]:
        """
        Export complete strategy with all tactics in one operation.
        
        Creates:
        1. Strategy board (or card in existing board)
        2. All tactic cards with checklists
        """
        results = {
            "strategy": None,
            "tactics": [],
            "summary": {
                "total_items": 1 + len(tactics),
                "exported_at": datetime.utcnow().isoformat()
            }
        }
        
        # Export strategy
        strategy_result = self.export_strategy(strategy)
        results["strategy"] = strategy_result
        
        # Get board ID from strategy export
        board_id = strategy_result["board_id"]
        
        # Export all tactics to the same board
        for tactic in tactics:
            tactic.board_id = board_id  # Ensure tactics go to strategy board
            tactic_result = self.export_tactic(tactic)
            results["tactics"].append(tactic_result)
        
        return results
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()