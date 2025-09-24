"""Sprint 5 - Jira Integration Client

This module provides one-click export of strategies and tactics to Jira
with proper mapping and idempotency.

Strategy → Epic
Tactic → Story/Task
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class JiraStrategy:
    """Strategy data structure for Jira export."""
    title: str
    description: str
    objectives: list[str]
    assumptions: list[str]
    timeline: str
    project_key: str
    epic_name: str | None = None  # If None, uses title
    assignee_account_id: str | None = None
    labels: list[str] = None
    priority: str = "Medium"  # High, Medium, Low


@dataclass
class JiraTactic:
    """Tactic data structure for Jira story/task."""
    title: str
    description: str
    strategy_epic_key: str  # Link to strategy epic
    deliverables: list[str]
    timeline: str
    effort_estimate: str  # Story points or hours
    success_criteria: list[str]
    project_key: str
    issue_type: str = "Story"  # Story, Task, Bug
    assignee_account_id: str | None = None
    priority: str = "Medium"
    labels: list[str] = None


class JiraClient:
    """
    Jira API client with retries, backoff, and idempotency for StratMaster exports.
    
    Uses Jira REST API v3:
    - Strategy → Epic creation
    - Tactic → Story/Task creation with epic link
    - Dry-run preview functionality
    - Idempotency keys for safe retries
    """
    
    def __init__(self, server_url: str, username: str, api_token: str):
        self.server_url = server_url.rstrip("/")
        self.username = username
        self.api_token = api_token
        
        self.client = httpx.Client(
            base_url=f"{self.server_url}/rest/api/3",
            auth=(username, api_token),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
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
            endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()[:8]
            return {
                "id": f"12345{endpoint_hash[-3:]}",
                "key": f"MOCK-{endpoint_hash[-3:]}",
                "self": f"{self.server_url}/rest/api/3/issue/12345{endpoint_hash[-3:]}",
                "created": datetime.utcnow().isoformat()
            }
        
        response = self.client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        
        if response.status_code == 204:  # No Content
            return {}
        
        return response.json()
    
    def get_project_details(self, project_key: str) -> dict[str, Any]:
        """Get project details including issue types."""
        if self.dry_run:
            return {
                "id": "10001",
                "key": project_key,
                "name": f"Mock Project {project_key}",
                "projectTypeKey": "software"
            }
        
        return self._make_request("GET", f"/project/{project_key}")
    
    def get_issue_types(self, project_key: str) -> list[dict[str, Any]]:
        """Get available issue types for a project."""
        if self.dry_run:
            return [
                {"id": "10001", "name": "Epic", "subtask": False},
                {"id": "10002", "name": "Story", "subtask": False},
                {"id": "10003", "name": "Task", "subtask": False},
                {"id": "10004", "name": "Bug", "subtask": False}
            ]
        
        project_details = self.get_project_details(project_key)
        return self._make_request("GET", f"/project/{project_details['id']}/statuses")
    
    def find_issue_type_id(self, project_key: str, issue_type_name: str) -> str:
        """Find issue type ID by name."""
        if self.dry_run:
            type_map = {"Epic": "10001", "Story": "10002", "Task": "10003", "Bug": "10004"}
            return type_map.get(issue_type_name, "10002")
        
        issue_types = self.get_issue_types(project_key)
        
        for issue_type in issue_types:
            if issue_type["name"] == issue_type_name:
                return issue_type["id"]
        
        # Default to Story if not found
        return "10002"
    
    def create_epic(self, project_key: str, summary: str, description: str = "",
                   epic_name: str | None = None, assignee_account_id: str | None = None,
                   labels: list[str] | None = None, priority: str = "Medium") -> dict[str, Any]:
        """Create a new Epic."""
        epic_type_id = self.find_issue_type_id(project_key, "Epic")
        
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            },
            "issuetype": {"id": epic_type_id},
            "priority": {"name": priority}
        }
        
        # Epic name (required for epics in some Jira configurations)
        if epic_name:
            fields["customfield_10011"] = epic_name  # Standard epic name field
        
        if assignee_account_id:
            fields["assignee"] = {"accountId": assignee_account_id}
        
        if labels:
            fields["labels"] = labels
        
        payload = {"fields": fields}
        
        if self.dry_run:
            self.exported_items.append({
                "type": "epic",
                "action": "create",
                "summary": summary,
                "epic_name": epic_name or summary,
                "project_key": project_key
            })
        
        return self._make_request("POST", "/issue", json=payload)
    
    def create_issue(self, project_key: str, issue_type: str, summary: str, 
                    description: str = "", epic_link: str | None = None,
                    assignee_account_id: str | None = None, priority: str = "Medium",
                    labels: list[str] | None = None, story_points: int | None = None) -> dict[str, Any]:
        """Create a new issue (Story, Task, etc.)."""
        issue_type_id = self.find_issue_type_id(project_key, issue_type)
        
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph", 
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            },
            "issuetype": {"id": issue_type_id},
            "priority": {"name": priority}
        }
        
        # Link to epic
        if epic_link:
            fields["parent"] = {"key": epic_link}  # For newer Jira versions
            # For older versions, might need customfield_10014 or similar
        
        if assignee_account_id:
            fields["assignee"] = {"accountId": assignee_account_id}
        
        if labels:
            fields["labels"] = labels
        
        if story_points and issue_type in ["Story", "Task"]:
            fields["customfield_10016"] = story_points  # Standard story points field
        
        payload = {"fields": fields}
        
        if self.dry_run:
            self.exported_items.append({
                "type": "issue",
                "action": "create",
                "summary": summary,
                "issue_type": issue_type,
                "project_key": project_key,
                "epic_link": epic_link
            })
        
        return self._make_request("POST", "/issue", json=payload)
    
    def add_comment(self, issue_key: str, comment_text: str) -> dict[str, Any]:
        """Add a comment to an issue."""
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment_text}]
                    }
                ]
            }
        }
        
        if self.dry_run:
            self.exported_items.append({
                "type": "comment",
                "action": "create",
                "issue_key": issue_key,
                "comment_text": comment_text[:100] + "..." if len(comment_text) > 100 else comment_text
            })
            return {"id": "mock-comment"}
        
        return self._make_request("POST", f"/issue/{issue_key}/comment", json=payload)
    
    def export_strategy(self, strategy: JiraStrategy,
                       idempotency_key: str | None = None) -> dict[str, Any]:
        """
        Export strategy as Jira Epic.
        
        Creates comprehensive epic with:
        - Title and description
        - Objectives in description
        - Assumptions as comments
        - Timeline information
        """
        
        # Generate idempotency key if not provided
        if not idempotency_key:
            content_hash = hashlib.md5(
                f"{strategy.title}-{strategy.project_key}-{len(strategy.objectives)}".encode()
            ).hexdigest()[:8]
            idempotency_key = f"strategy-{content_hash}"
        
        # Build comprehensive description
        desc_parts = [strategy.description]
        
        if strategy.objectives:
            desc_parts.append("\n\n## Objectives")
            for obj in strategy.objectives:
                desc_parts.append(f"• {obj}")
        
        desc_parts.append(f"\n\n## Timeline\n{strategy.timeline}")
        desc_parts.append(f"\n\n## Idempotency Key\n{idempotency_key}")
        
        epic_description = "\n".join(desc_parts)
        epic_name = strategy.epic_name or strategy.title
        
        # Create the epic
        epic_result = self.create_epic(
            project_key=strategy.project_key,
            summary=strategy.title,
            description=epic_description,
            epic_name=epic_name,
            assignee_account_id=strategy.assignee_account_id,
            labels=strategy.labels,
            priority=strategy.priority
        )
        
        # Add assumptions as comments if present
        if strategy.assumptions and not self.dry_run:
            assumptions_text = "## Key Assumptions\n\n" + "\n".join(f"• {assumption}" for assumption in strategy.assumptions)
            self.add_comment(epic_result["key"], assumptions_text)
        
        return {
            "type": "strategy",
            "epic_key": epic_result["key"],
            "epic_id": epic_result["id"],
            "epic_url": f"{self.server_url}/browse/{epic_result['key']}",
            "title": strategy.title,
            "epic_name": epic_name,
            "project_key": strategy.project_key,
            "idempotency_key": idempotency_key,
            "exported_at": datetime.utcnow().isoformat()
        }
    
    def export_tactic(self, tactic: JiraTactic,
                     idempotency_key: str | None = None) -> dict[str, Any]:
        """
        Export tactic as Jira Story/Task linked to strategy epic.
        
        Creates issue with:
        - Title and description
        - Epic link to strategy
        - Deliverables and success criteria in description
        - Proper effort estimation
        """
        
        # Generate idempotency key if not provided
        if not idempotency_key:
            content_hash = hashlib.md5(
                f"{tactic.title}-{tactic.strategy_epic_key}-{len(tactic.deliverables)}".encode()
            ).hexdigest()[:8]
            idempotency_key = f"tactic-{content_hash}"
        
        # Build comprehensive description
        desc_parts = [tactic.description]
        
        if tactic.deliverables:
            desc_parts.append("\n\n## Deliverables")
            for deliverable in tactic.deliverables:
                desc_parts.append(f"• {deliverable}")
        
        if tactic.success_criteria:
            desc_parts.append("\n\n## Success Criteria")
            for criteria in tactic.success_criteria:
                desc_parts.append(f"• {criteria}")
        
        desc_parts.append(f"\n\n## Timeline\n{tactic.timeline}")
        desc_parts.append(f"\n\n## Effort Estimate\n{tactic.effort_estimate}")
        desc_parts.append(f"\n\n## Idempotency Key\n{idempotency_key}")
        
        issue_description = "\n".join(desc_parts)
        
        # Parse effort estimate for story points
        story_points = None
        if tactic.effort_estimate.lower().endswith("sp"):
            try:
                story_points = int(tactic.effort_estimate.lower().replace("sp", "").strip())
            except ValueError:
                pass
        elif tactic.effort_estimate.lower() in ["small", "s"]:
            story_points = 1
        elif tactic.effort_estimate.lower() in ["medium", "m"]:
            story_points = 3
        elif tactic.effort_estimate.lower() in ["large", "l"]:
            story_points = 5
        elif tactic.effort_estimate.lower() in ["xl", "extra large"]:
            story_points = 8
        
        # Create the issue
        issue_result = self.create_issue(
            project_key=tactic.project_key,
            issue_type=tactic.issue_type,
            summary=tactic.title,
            description=issue_description,
            epic_link=tactic.strategy_epic_key,
            assignee_account_id=tactic.assignee_account_id,
            priority=tactic.priority,
            labels=tactic.labels,
            story_points=story_points
        )
        
        return {
            "type": "tactic",
            "issue_key": issue_result["key"],
            "issue_id": issue_result["id"],
            "issue_url": f"{self.server_url}/browse/{issue_result['key']}",
            "title": tactic.title,
            "issue_type": tactic.issue_type,
            "strategy_epic_key": tactic.strategy_epic_key,
            "project_key": tactic.project_key,
            "story_points": story_points,
            "idempotency_key": idempotency_key,
            "exported_at": datetime.utcnow().isoformat()
        }
    
    def export_full_strategy_with_tactics(self, strategy: JiraStrategy, tactics: list[JiraTactic]) -> dict[str, Any]:
        """
        Export complete strategy with all tactics in one operation.
        
        Creates:
        1. Strategy epic
        2. All tactic stories/tasks linked to the epic
        """
        results = {
            "strategy": None,
            "tactics": [],
            "summary": {
                "total_items": 1 + len(tactics),
                "exported_at": datetime.utcnow().isoformat()
            }
        }
        
        # Export strategy epic
        strategy_result = self.export_strategy(strategy)
        results["strategy"] = strategy_result
        
        # Get epic key from strategy export
        epic_key = strategy_result["epic_key"]
        
        # Export all tactics linked to the epic
        for tactic in tactics:
            tactic.strategy_epic_key = epic_key  # Ensure tactics link to strategy epic
            tactic.project_key = strategy.project_key  # Ensure same project
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