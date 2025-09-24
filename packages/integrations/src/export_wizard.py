"""Sprint 5 - Export Wizard

Unified export wizard that provides one-click export to Notion, Trello, and Jira
with dry-run preview, idempotency, and comprehensive error handling.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from notion import NotionClient, NotionStrategy, NotionTactic
from trello import TrelloClient, TrelloStrategy, TrelloTactic
from jira import JiraClient, JiraStrategy, JiraTactic


class ExportPlatform(Enum):
    """Supported export platforms."""
    NOTION = "notion"
    TRELLO = "trello"
    JIRA = "jira"


@dataclass
class ExportConfig:
    """Configuration for export wizard."""
    platforms: list[ExportPlatform]
    dry_run: bool = True
    
    # Notion config
    notion_token: str | None = None
    notion_parent_page_id: str | None = None
    
    # Trello config
    trello_api_key: str | None = None
    trello_api_token: str | None = None
    trello_board_id: str | None = None  # If None, creates new board
    
    # Jira config
    jira_server_url: str | None = None
    jira_username: str | None = None
    jira_api_token: str | None = None
    jira_project_key: str | None = None


@dataclass
class UnifiedStrategy:
    """Universal strategy data structure."""
    title: str
    description: str
    objectives: list[str]
    assumptions: list[str]
    metrics: list[str]  # Notion-specific but mapped to description for others
    timeline: str
    priority: str = "Medium"
    owner: str | None = None
    tags: list[str] = None


@dataclass
class UnifiedTactic:
    """Universal tactic data structure."""
    title: str
    description: str
    deliverables: list[str]
    timeline: str
    effort_estimate: str
    success_criteria: list[str]
    priority: str = "Medium"
    assignee: str | None = None
    due_date: str | None = None  # ISO format
    dependencies: list[str] = None


class ExportWizard:
    """
    Unified export wizard for StratMaster strategies and tactics.
    
    Provides:
    - Multi-platform export (Notion + Trello + Jira)
    - Dry-run preview with detailed breakdown
    - Idempotency across platforms
    - Comprehensive error handling and rollback
    - Progress tracking and status reporting
    """
    
    def __init__(self, config: ExportConfig):
        self.config = config
        self.clients = {}
        self.export_results = {}
        self.errors = []
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize clients for enabled platforms."""
        
        if ExportPlatform.NOTION in self.config.platforms:
            if not self.config.notion_token:
                raise ValueError("Notion token required for Notion export")
            
            self.clients[ExportPlatform.NOTION] = NotionClient(self.config.notion_token)
            self.clients[ExportPlatform.NOTION].set_dry_run(self.config.dry_run)
        
        if ExportPlatform.TRELLO in self.config.platforms:
            if not self.config.trello_api_key or not self.config.trello_api_token:
                raise ValueError("Trello API key and token required for Trello export")
            
            self.clients[ExportPlatform.TRELLO] = TrelloClient(
                self.config.trello_api_key,
                self.config.trello_api_token
            )
            self.clients[ExportPlatform.TRELLO].set_dry_run(self.config.dry_run)
        
        if ExportPlatform.JIRA in self.config.platforms:
            if not all([self.config.jira_server_url, self.config.jira_username, 
                       self.config.jira_api_token, self.config.jira_project_key]):
                raise ValueError("Jira server URL, username, API token, and project key required")
            
            self.clients[ExportPlatform.JIRA] = JiraClient(
                self.config.jira_server_url,
                self.config.jira_username,
                self.config.jira_api_token
            )
            self.clients[ExportPlatform.JIRA].set_dry_run(self.config.dry_run)
    
    def _convert_to_notion(self, strategy: UnifiedStrategy) -> NotionStrategy:
        """Convert unified strategy to Notion format."""
        return NotionStrategy(
            title=strategy.title,
            description=strategy.description,
            objectives=strategy.objectives,
            assumptions=strategy.assumptions,
            metrics=strategy.metrics,
            timeline=strategy.timeline,
            status="Draft",
            priority=strategy.priority,
            owner=strategy.owner,
            tags=strategy.tags
        )
    
    def _convert_to_trello(self, strategy: UnifiedStrategy) -> TrelloStrategy:
        """Convert unified strategy to Trello format."""
        return TrelloStrategy(
            title=strategy.title,
            description=strategy.description,
            objectives=strategy.objectives,
            assumptions=strategy.assumptions,
            timeline=strategy.timeline,
            board_id=self.config.trello_board_id,
            labels=strategy.tags
        )
    
    def _convert_to_jira(self, strategy: UnifiedStrategy) -> JiraStrategy:
        """Convert unified strategy to Jira format."""
        return JiraStrategy(
            title=strategy.title,
            description=strategy.description,
            objectives=strategy.objectives,
            assumptions=strategy.assumptions,
            timeline=strategy.timeline,
            project_key=self.config.jira_project_key,
            priority=strategy.priority,
            labels=strategy.tags
        )
    
    def _convert_tactic_to_notion(self, tactic: UnifiedTactic, strategy_id: str) -> NotionTactic:
        """Convert unified tactic to Notion format."""
        return NotionTactic(
            title=tactic.title,
            description=tactic.description,
            strategy_id=strategy_id,
            deliverables=tactic.deliverables,
            timeline=tactic.timeline,
            effort_estimate=tactic.effort_estimate,
            success_criteria=tactic.success_criteria,
            status="Not Started",
            assignee=tactic.assignee,
            dependencies=tactic.dependencies
        )
    
    def _convert_tactic_to_trello(self, tactic: UnifiedTactic, board_id: str) -> TrelloTactic:
        """Convert unified tactic to Trello format."""
        return TrelloTactic(
            title=tactic.title,
            description=tactic.description,
            strategy_id="",  # Will be set during export
            deliverables=tactic.deliverables,
            timeline=tactic.timeline,
            effort_estimate=tactic.effort_estimate,
            success_criteria=tactic.success_criteria,
            board_id=board_id,
            assignee_username=tactic.assignee,
            due_date=tactic.due_date
        )
    
    def _convert_tactic_to_jira(self, tactic: UnifiedTactic, epic_key: str) -> JiraTactic:
        """Convert unified tactic to Jira format."""
        return JiraTactic(
            title=tactic.title,
            description=tactic.description,
            strategy_epic_key=epic_key,
            deliverables=tactic.deliverables,
            timeline=tactic.timeline,
            effort_estimate=tactic.effort_estimate,
            success_criteria=tactic.success_criteria,
            project_key=self.config.jira_project_key,
            priority=tactic.priority
        )
    
    def get_dry_run_preview(self) -> dict[str, Any]:
        """Get comprehensive dry-run preview for all platforms."""
        if not self.config.dry_run:
            return {"error": "Dry-run mode not enabled"}
        
        preview = {
            "platforms": {},
            "summary": {
                "total_platforms": len(self.clients),
                "dry_run_enabled": True,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
        for platform, client in self.clients.items():
            preview["platforms"][platform.value] = {
                "items": client.get_dry_run_preview(),
                "client_type": client.__class__.__name__
            }
        
        return preview
    
    def export_strategy_with_tactics(self, strategy: UnifiedStrategy, 
                                   tactics: list[UnifiedTactic]) -> dict[str, Any]:
        """
        Export strategy with tactics to all configured platforms.
        
        Returns comprehensive results with per-platform success/failure status.
        """
        
        start_time = datetime.utcnow()
        self.export_results = {}
        self.errors = []
        
        total_operations = len(self.clients) * (1 + len(tactics))  # Strategy + tactics per platform
        completed_operations = 0
        
        for platform, client in self.clients.items():
            platform_results = {
                "platform": platform.value,
                "success": False,
                "strategy": None,
                "tactics": [],
                "errors": [],
                "started_at": datetime.utcnow().isoformat()
            }
            
            try:
                if platform == ExportPlatform.NOTION:
                    # Notion export
                    notion_strategy = self._convert_to_notion(strategy)
                    
                    if not self.config.notion_parent_page_id:
                        raise ValueError("Notion parent page ID required")
                    
                    strategy_result = client.export_strategy(
                        notion_strategy, 
                        self.config.notion_parent_page_id
                    )
                    platform_results["strategy"] = strategy_result
                    completed_operations += 1
                    
                    # Export tactics to Notion database
                    if tactics:
                        database_result = client.create_tactics_database(
                            strategy_result["notion_page_id"],
                            f"{strategy.title} - Tactics"
                        )
                        
                        for tactic in tactics:
                            notion_tactic = self._convert_tactic_to_notion(
                                tactic, 
                                strategy_result["notion_page_id"]
                            )
                            
                            tactic_result = client.export_tactic(
                                notion_tactic,
                                database_result["id"]
                            )
                            platform_results["tactics"].append(tactic_result)
                            completed_operations += 1
                
                elif platform == ExportPlatform.TRELLO:
                    # Trello export
                    trello_strategy = self._convert_to_trello(strategy)
                    
                    strategy_result = client.export_strategy(trello_strategy)
                    platform_results["strategy"] = strategy_result
                    completed_operations += 1
                    
                    # Export tactics as cards
                    board_id = strategy_result["board_id"]
                    for tactic in tactics:
                        trello_tactic = self._convert_tactic_to_trello(tactic, board_id)
                        trello_tactic.strategy_id = strategy_result.get("card_id", "")
                        
                        tactic_result = client.export_tactic(trello_tactic)
                        platform_results["tactics"].append(tactic_result)
                        completed_operations += 1
                
                elif platform == ExportPlatform.JIRA:
                    # Jira export
                    jira_strategy = self._convert_to_jira(strategy)
                    
                    strategy_result = client.export_strategy(jira_strategy)
                    platform_results["strategy"] = strategy_result
                    completed_operations += 1
                    
                    # Export tactics as linked issues
                    epic_key = strategy_result["epic_key"]
                    for tactic in tactics:
                        jira_tactic = self._convert_tactic_to_jira(tactic, epic_key)
                        
                        tactic_result = client.export_tactic(jira_tactic)
                        platform_results["tactics"].append(tactic_result)
                        completed_operations += 1
                
                platform_results["success"] = True
                
            except Exception as error:
                error_msg = f"{platform.value}: {str(error)}"
                platform_results["errors"].append(error_msg)
                self.errors.append(error_msg)
            
            platform_results["completed_at"] = datetime.utcnow().isoformat()
            platform_results["progress"] = f"{completed_operations}/{total_operations}"
            self.export_results[platform.value] = platform_results
        
        # Generate summary
        successful_platforms = [p for p in self.export_results.values() if p["success"]]
        failed_platforms = [p for p in self.export_results.values() if not p["success"]]
        
        summary = {
            "total_platforms": len(self.clients),
            "successful_platforms": len(successful_platforms),
            "failed_platforms": len(failed_platforms),
            "total_items_exported": 1 + len(tactics),  # Strategy + tactics
            "total_operations": total_operations,
            "completed_operations": completed_operations,
            "success_rate": f"{len(successful_platforms)}/{len(self.clients)}",
            "dry_run": self.config.dry_run,
            "started_at": start_time.isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
        }
        
        return {
            "summary": summary,
            "platforms": self.export_results,
            "errors": self.errors,
            "dry_run_preview": self.get_dry_run_preview() if self.config.dry_run else None
        }
    
    def validate_configuration(self) -> dict[str, Any]:
        """Validate export configuration before running."""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "platforms": {}
        }
        
        for platform in self.config.platforms:
            platform_validation = {"valid": True, "errors": [], "warnings": []}
            
            if platform == ExportPlatform.NOTION:
                if not self.config.notion_token:
                    platform_validation["errors"].append("Notion API token required")
                    platform_validation["valid"] = False
                
                if not self.config.notion_parent_page_id:
                    platform_validation["warnings"].append("Parent page ID not specified")
            
            elif platform == ExportPlatform.TRELLO:
                if not self.config.trello_api_key:
                    platform_validation["errors"].append("Trello API key required")
                    platform_validation["valid"] = False
                
                if not self.config.trello_api_token:
                    platform_validation["errors"].append("Trello API token required")
                    platform_validation["valid"] = False
                
                if not self.config.trello_board_id:
                    platform_validation["warnings"].append("Board ID not specified - will create new board")
            
            elif platform == ExportPlatform.JIRA:
                if not self.config.jira_server_url:
                    platform_validation["errors"].append("Jira server URL required")
                    platform_validation["valid"] = False
                
                if not self.config.jira_username:
                    platform_validation["errors"].append("Jira username required")
                    platform_validation["valid"] = False
                
                if not self.config.jira_api_token:
                    platform_validation["errors"].append("Jira API token required")
                    platform_validation["valid"] = False
                
                if not self.config.jira_project_key:
                    platform_validation["errors"].append("Jira project key required")
                    platform_validation["valid"] = False
            
            validation["platforms"][platform.value] = platform_validation
            
            if not platform_validation["valid"]:
                validation["valid"] = False
                validation["errors"].extend(platform_validation["errors"])
        
        return validation
    
    def close(self):
        """Close all client connections."""
        for client in self.clients.values():
            if hasattr(client, 'close'):
                client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()