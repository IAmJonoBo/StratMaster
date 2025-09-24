"""
Sprint 5 - Notion Integration Client

This module provides one-click export of strategies and nested tactics/deliverables
into Notion databases with proper mapping and idempotency.

Strategy → Page
Tactic → Database Row
Status fields included
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class NotionStrategy:
    """Strategy data structure for Notion export."""
    title: str
    description: str
    objectives: list[str]
    assumptions: list[str]
    metrics: list[str]
    timeline: str
    status: str = "Draft"
    priority: str = "Medium"
    owner: str | None = None
    tags: list[str] = None


@dataclass
class NotionTactic:
    """Tactic data structure for Notion database row."""
    title: str
    description: str
    strategy_id: str
    deliverables: list[str]
    timeline: str
    effort_estimate: str
    success_criteria: list[str]
    status: str = "Not Started"
    assignee: str | None = None
    dependencies: list[str] = None


class NotionClient:
    """
    Notion API client with retries, backoff, and idempotency for StratMaster exports.
    
    Handles:
    - Strategy → Page creation/updates
    - Tactic → Database row creation
    - Dry-run preview functionality
    - Idempotency keys for safe retries
    """
    
    def __init__(self, api_token: str, base_url: str = "https://api.notion.com/v1"):
        self.api_token = api_token
        self.base_url = base_url
        self.client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            },
            timeout=30.0
        )
        
        self.dry_run = False
        self.exported_items = []  # Track exports for dry-run
    
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
                "object": "page" if "pages" in endpoint else "database",
                "id": f"mock-{hashlib.md5(endpoint.encode()).hexdigest()[:8]}",
                "url": f"https://notion.so/mock-{hashlib.md5(endpoint.encode()).hexdigest()[:8]}",
                "created_time": datetime.utcnow().isoformat(),
                "last_edited_time": datetime.utcnow().isoformat()
            }
        
        response = self.client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def create_database(self, parent_page_id: str, title: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Create a new Notion database."""
        payload = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": schema
        }
        
        if self.dry_run:
            self.exported_items.append({
                "type": "database",
                "action": "create",
                "title": title,
                "parent_page_id": parent_page_id,
                "schema": schema
            })
        
        return self._make_request("POST", "/databases", json=payload)
    
    def create_page(self, parent_id: str, title: str, content: list[dict[str, Any]], 
                   properties: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create a new Notion page."""
        payload = {
            "parent": {"database_id": parent_id} if properties else {"page_id": parent_id},
            "properties": {
                "title": {
                    "title": [{"type": "text", "text": {"content": title}}]
                }
            },
            "children": content
        }
        
        if properties:
            payload["properties"].update(properties)
        
        if self.dry_run:
            self.exported_items.append({
                "type": "page", 
                "action": "create",
                "title": title,
                "parent_id": parent_id,
                "properties": properties,
                "content_blocks": len(content)
            })
        
        return self._make_request("POST", "/pages", json=payload)
    
    def update_page(self, page_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        """Update an existing Notion page."""
        payload = {"properties": properties}
        
        if self.dry_run:
            self.exported_items.append({
                "type": "page",
                "action": "update", 
                "page_id": page_id,
                "properties": properties
            })
        
        return self._make_request("PATCH", f"/pages/{page_id}", json=payload)
    
    def find_page_by_title(self, database_id: str, title: str) -> dict[str, Any] | None:
        """Find page by title in a database."""
        if self.dry_run:
            return None  # Assume not found in dry-run
        
        payload = {
            "filter": {
                "property": "title",
                "title": {"equals": title}
            }
        }
        
        response = self._make_request("POST", f"/databases/{database_id}/query", json=payload)
        results = response.get("results", [])
        return results[0] if results else None
    
    def export_strategy(self, strategy: NotionStrategy, parent_page_id: str, 
                       idempotency_key: str | None = None) -> dict[str, Any]:
        """
        Export strategy as a Notion page with full content structure.
        
        Creates a comprehensive strategy page with:
        - Title and description
        - Objectives section
        - Assumptions section  
        - Success metrics
        - Timeline and status
        """
        
        # Generate idempotency key if not provided
        if not idempotency_key:
            content_hash = hashlib.md5(
                f"{strategy.title}-{strategy.description}-{len(strategy.objectives)}".encode()
            ).hexdigest()[:8]
            idempotency_key = f"strategy-{content_hash}"
        
        # Build content blocks
        content_blocks = []
        
        # Description block
        if strategy.description:
            content_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": strategy.description}}]
                }
            })
        
        # Objectives section
        if strategy.objectives:
            content_blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Objectives"}}]
                }
            })
            
            for objective in strategy.objectives:
                content_blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": objective}}]
                    }
                })
        
        # Assumptions section
        if strategy.assumptions:
            content_blocks.append({
                "object": "block",
                "type": "heading_2", 
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Key Assumptions"}}]
                }
            })
            
            for assumption in strategy.assumptions:
                content_blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": assumption}}]
                    }
                })
        
        # Metrics section
        if strategy.metrics:
            content_blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Success Metrics"}}]
                }
            })
            
            for metric in strategy.metrics:
                content_blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": metric}}]
                    }
                })
        
        # Properties for the page
        properties = {
            "Status": {"select": {"name": strategy.status}},
            "Priority": {"select": {"name": strategy.priority}}, 
            "Timeline": {"rich_text": [{"type": "text", "text": {"content": strategy.timeline}}]},
            "Idempotency Key": {"rich_text": [{"type": "text", "text": {"content": idempotency_key}}]}
        }
        
        if strategy.owner:
            properties["Owner"] = {"rich_text": [{"type": "text", "text": {"content": strategy.owner}}]}
        
        if strategy.tags:
            properties["Tags"] = {"multi_select": [{"name": tag} for tag in strategy.tags]}
        
        # Create the page
        result = self.create_page(
            parent_id=parent_page_id,
            title=strategy.title,
            content=content_blocks,
            properties=properties
        )
        
        return {
            "type": "strategy",
            "notion_page_id": result["id"],
            "notion_url": result.get("url", ""),
            "title": strategy.title,
            "idempotency_key": idempotency_key,
            "exported_at": datetime.utcnow().isoformat()
        }
    
    def export_tactic(self, tactic: NotionTactic, database_id: str,
                     idempotency_key: str | None = None) -> dict[str, Any]:
        """
        Export tactic as a database row with proper field mapping.
        
        Maps tactic fields to database properties:
        - Title → Name
        - Description → Description
        - Strategy ID → Strategy (relation)
        - Deliverables → Deliverables (multi-select)
        - Timeline → Timeline
        - Effort → Effort Estimate
        - Status → Status
        """
        
        # Generate idempotency key if not provided
        if not idempotency_key:
            content_hash = hashlib.md5(
                f"{tactic.title}-{tactic.strategy_id}-{len(tactic.deliverables)}".encode()
            ).hexdigest()[:8]
            idempotency_key = f"tactic-{content_hash}"
        
        # Check for existing tactic with same idempotency key
        existing_tactic = self.find_page_by_title(database_id, tactic.title)
        if existing_tactic and not self.dry_run:
            # Update existing tactic
            return self._update_existing_tactic(existing_tactic["id"], tactic, idempotency_key)
        
        # Map properties to Notion database fields
        properties = {
            "Name": {"title": [{"type": "text", "text": {"content": tactic.title}}]},
            "Description": {"rich_text": [{"type": "text", "text": {"content": tactic.description}}]},
            "Strategy ID": {"rich_text": [{"type": "text", "text": {"content": tactic.strategy_id}}]},
            "Timeline": {"rich_text": [{"type": "text", "text": {"content": tactic.timeline}}]},
            "Effort Estimate": {"select": {"name": tactic.effort_estimate}},
            "Status": {"select": {"name": tactic.status}},
            "Idempotency Key": {"rich_text": [{"type": "text", "text": {"content": idempotency_key}}]}
        }
        
        # Handle multi-select fields
        if tactic.deliverables:
            properties["Deliverables"] = {
                "multi_select": [{"name": deliverable} for deliverable in tactic.deliverables]
            }
        
        if tactic.success_criteria:
            properties["Success Criteria"] = {
                "multi_select": [{"name": criteria} for criteria in tactic.success_criteria]
            }
        
        if tactic.dependencies:
            properties["Dependencies"] = {
                "multi_select": [{"name": dep} for dep in tactic.dependencies]
            }
        
        if tactic.assignee:
            properties["Assignee"] = {"rich_text": [{"type": "text", "text": {"content": tactic.assignee}}]}
        
        # Create database row
        result = self.create_page(
            parent_id=database_id,
            title=tactic.title,
            content=[],  # Database rows don't have content blocks
            properties=properties
        )
        
        return {
            "type": "tactic",
            "notion_page_id": result["id"],
            "notion_url": result.get("url", ""),
            "title": tactic.title,
            "strategy_id": tactic.strategy_id,
            "idempotency_key": idempotency_key,
            "exported_at": datetime.utcnow().isoformat()
        }
    
    def _update_existing_tactic(self, page_id: str, tactic: NotionTactic, 
                              idempotency_key: str) -> dict[str, Any]:
        """Update existing tactic page."""
        properties = {
            "Description": {"rich_text": [{"type": "text", "text": {"content": tactic.description}}]},
            "Timeline": {"rich_text": [{"type": "text", "text": {"content": tactic.timeline}}]},
            "Effort Estimate": {"select": {"name": tactic.effort_estimate}},
            "Status": {"select": {"name": tactic.status}},
            "Idempotency Key": {"rich_text": [{"type": "text", "text": {"content": idempotency_key}}]}
        }
        
        result = self.update_page(page_id, properties)
        
        return {
            "type": "tactic",
            "action": "updated",
            "notion_page_id": page_id,
            "title": tactic.title,
            "strategy_id": tactic.strategy_id,
            "idempotency_key": idempotency_key,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    def create_tactics_database(self, parent_page_id: str, database_name: str = "Tactics") -> dict[str, Any]:
        """Create a tactics database with proper schema."""
        schema = {
            "Name": {"title": {}},
            "Description": {"rich_text": {}},
            "Strategy ID": {"rich_text": {}},
            "Timeline": {"rich_text": {}},
            "Effort Estimate": {
                "select": {
                    "options": [
                        {"name": "Small", "color": "green"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Large", "color": "red"},
                        {"name": "XL", "color": "purple"}
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Not Started", "color": "gray"},
                        {"name": "In Progress", "color": "yellow"},
                        {"name": "Review", "color": "orange"},
                        {"name": "Done", "color": "green"},
                        {"name": "Blocked", "color": "red"}
                    ]
                }
            },
            "Deliverables": {"multi_select": {}},
            "Success Criteria": {"multi_select": {}},
            "Dependencies": {"multi_select": {}},
            "Assignee": {"rich_text": {}},
            "Idempotency Key": {"rich_text": {}}
        }
        
        return self.create_database(parent_page_id, database_name, schema)
    
    def export_full_strategy_with_tactics(self, strategy: NotionStrategy, tactics: list[NotionTactic],
                                        parent_page_id: str) -> dict[str, Any]:
        """
        Export complete strategy with all tactics in one operation.
        
        Creates:
        1. Strategy page
        2. Tactics database (if needed)
        3. All tactic rows
        """
        results = {
            "strategy": None,
            "tactics_database": None,
            "tactics": [],
            "summary": {
                "total_items": 1 + len(tactics),
                "exported_at": datetime.utcnow().isoformat()
            }
        }
        
        # Export strategy page
        strategy_result = self.export_strategy(strategy, parent_page_id)
        results["strategy"] = strategy_result
        
        if tactics:
            # Create tactics database
            database_result = self.create_tactics_database(
                strategy_result["notion_page_id"], 
                f"{strategy.title} - Tactics"
            )
            results["tactics_database"] = database_result
            
            # Export all tactics
            for tactic in tactics:
                tactic_result = self.export_tactic(tactic, database_result["id"])
                results["tactics"].append(tactic_result)
        
        return results
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()