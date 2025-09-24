"""
Sprint 5 - Tests for Export Integrations

Tests for Notion, Trello, and Jira integrations with dry-run validation,
idempotency, and round-trip verification.
"""

import sys
import os

# Add integrations to path
sys.path.append('/home/runner/work/StratMaster/StratMaster/packages/integrations/src')

from notion import NotionClient, NotionStrategy, NotionTactic
from trello import TrelloClient, TrelloStrategy, TrelloTactic
from jira import JiraClient, JiraStrategy, JiraTactic


class TestNotionIntegration:
    """Test suite for Notion integration."""

    def setup_method(self):
        """Setup for each test."""
        self.client = NotionClient("test-token")
        self.client.set_dry_run(True)

    def test_export_strategy_dry_run(self):
        """Test strategy export in dry-run mode."""
        strategy = NotionStrategy(
            title="AI Implementation Strategy",
            description="Comprehensive strategy for AI adoption",
            objectives=["Increase automation by 50%", "Reduce manual tasks"],
            assumptions=["Budget approved", "Team trained"],
            metrics=["Automation rate", "Process efficiency"],
            timeline="Q1-Q2 2024"
        )

        result = self.client.export_strategy(strategy, "test-page-id")
        
        assert result["type"] == "strategy"
        assert result["title"] == "AI Implementation Strategy"
        assert "idempotency_key" in result
        assert result["exported_at"]

        # Verify dry-run tracking
        preview = self.client.get_dry_run_preview()
        assert len(preview) == 1
        assert preview[0]["type"] == "page"
        assert preview[0]["title"] == "AI Implementation Strategy"

    def test_export_tactic_dry_run(self):
        """Test tactic export in dry-run mode."""
        tactic = NotionTactic(
            title="Implement ML Pipeline",
            description="Build automated ML training pipeline",
            strategy_id="strategy-123",
            deliverables=["Pipeline code", "Documentation", "Tests"],
            timeline="2 weeks",
            effort_estimate="Large",
            success_criteria=["Pipeline runs daily", "99% uptime"]
        )

        result = self.client.export_tactic(tactic, "test-database-id")
        
        assert result["type"] == "tactic"
        assert result["title"] == "Implement ML Pipeline"
        assert result["strategy_id"] == "strategy-123"
        assert "idempotency_key" in result

    def test_full_export_dry_run(self):
        """Test full strategy with tactics export."""
        strategy = NotionStrategy(
            title="Digital Transformation",
            description="Transform business processes",
            objectives=["Modernize systems", "Improve efficiency"],
            assumptions=["Leadership support"],
            metrics=["System uptime", "User satisfaction"],
            timeline="6 months"
        )

        tactics = [
            NotionTactic(
                title="Migrate to Cloud",
                description="Move infrastructure to cloud",
                strategy_id="dt-001",
                deliverables=["Migration plan", "Cloud setup"],
                timeline="1 month",
                effort_estimate="Medium",
                success_criteria=["Zero downtime migration"]
            )
        ]

        result = self.client.export_full_strategy_with_tactics(strategy, tactics, "parent-page")
        
        assert result["strategy"]["title"] == "Digital Transformation"
        assert len(result["tactics"]) == 1
        assert result["tactics"][0]["title"] == "Migrate to Cloud"
        assert result["summary"]["total_items"] == 2


class TestTrelloIntegration:
    """Test suite for Trello integration."""

    def setup_method(self):
        """Setup for each test."""
        self.client = TrelloClient("test-key", "test-token")
        self.client.set_dry_run(True)

    def test_export_strategy_new_board(self):
        """Test strategy export to new board."""
        strategy = TrelloStrategy(
            title="Product Launch Strategy",
            description="Launch new product line",
            objectives=["Capture 10% market share", "Generate $1M revenue"],
            assumptions=["Market demand exists", "Competition remains stable"],
            timeline="3 months"
        )

        result = self.client.export_strategy(strategy)
        
        assert result["type"] == "strategy"
        assert result["approach"] == "new_board"
        assert result["title"] == "Product Launch Strategy"
        assert "board_id" in result
        assert "card_id" in result

        # Verify dry-run items
        preview = self.client.get_dry_run_preview()
        board_items = [item for item in preview if item["type"] == "board"]
        assert len(board_items) == 1

    def test_export_tactic_to_board(self):
        """Test tactic export to board."""
        tactic = TrelloTactic(
            title="Market Research Phase",
            description="Conduct comprehensive market analysis",
            strategy_id="product-launch-001", 
            deliverables=["Market report", "Competitive analysis"],
            timeline="2 weeks",
            effort_estimate="Medium",
            success_criteria=["Report completed", "Stakeholder approval"],
            board_id="test-board-123"
        )

        result = self.client.export_tactic(tactic)
        
        assert result["type"] == "tactic"
        assert result["title"] == "Market Research Phase"
        assert result["strategy_id"] == "product-launch-001"
        assert result["board_id"] == "test-board-123"

        # Verify checklists were created
        preview = self.client.get_dry_run_preview()
        checklist_items = [item for item in preview if item["type"] == "checklist"]
        assert len(checklist_items) == 2  # Deliverables + Success Criteria

    def test_full_export_integration(self):
        """Test full strategy with tactics export."""
        strategy = TrelloStrategy(
            title="Brand Repositioning",
            description="Reposition brand for premium market",
            objectives=["Increase brand perception", "Target premium segment"],
            assumptions=["Budget available for campaigns"],
            timeline="4 months"
        )

        tactics = [
            TrelloTactic(
                title="Brand Audit",
                description="Comprehensive brand analysis",
                strategy_id="brand-repo-001",
                deliverables=["Audit report", "Recommendations"],
                timeline="3 weeks", 
                effort_estimate="Large",
                success_criteria=["Audit complete", "Insights documented"],
                board_id=""  # Will be set by full export
            )
        ]

        result = self.client.export_full_strategy_with_tactics(strategy, tactics)
        
        assert result["strategy"]["title"] == "Brand Repositioning"
        assert len(result["tactics"]) == 1
        assert result["tactics"][0]["title"] == "Brand Audit"


class TestJiraIntegration:
    """Test suite for Jira integration."""

    def setup_method(self):
        """Setup for each test."""
        self.client = JiraClient(
            server_url="https://test.atlassian.net",
            username="test@example.com",
            api_token="test-token"
        )
        self.client.set_dry_run(True)

    def test_export_strategy_as_epic(self):
        """Test strategy export as Jira epic."""
        strategy = JiraStrategy(
            title="Platform Modernization",
            description="Modernize legacy platform architecture",
            objectives=["Improve scalability", "Reduce technical debt"],
            assumptions=["Team has required skills", "Timeline is realistic"],
            timeline="6 months",
            project_key="PLAT"
        )

        result = self.client.export_strategy(strategy)
        
        assert result["type"] == "strategy"
        assert result["title"] == "Platform Modernization"
        assert result["project_key"] == "PLAT"
        assert "epic_key" in result

        # Verify dry-run items
        preview = self.client.get_dry_run_preview()
        epic_items = [item for item in preview if item["type"] == "epic"]
        assert len(epic_items) == 1

    def test_export_tactic_as_story(self):
        """Test tactic export as Jira story."""
        tactic = JiraTactic(
            title="Migrate User Service",
            description="Migrate user management service to new architecture",
            strategy_epic_key="PLAT-123",
            deliverables=["Migrated service", "Integration tests", "Documentation"],
            timeline="2 sprints",
            effort_estimate="8 SP",
            success_criteria=["All tests pass", "Performance improved"],
            project_key="PLAT",
            issue_type="Story"
        )

        result = self.client.export_tactic(tactic)
        
        assert result["type"] == "tactic"
        assert result["title"] == "Migrate User Service"
        assert result["strategy_epic_key"] == "PLAT-123"
        assert result["story_points"] == 8
        assert result["issue_type"] == "Story"

    def test_effort_estimate_parsing(self):
        """Test effort estimate parsing for story points."""
        test_cases = [
            ("5 SP", 5),
            ("Small", 1), 
            ("Medium", 3),
            ("Large", 5),
            ("XL", 8),
            ("3 hours", None)  # Should not convert non-SP estimates
        ]

        for estimate, expected_points in test_cases:
            tactic = JiraTactic(
                title="Test Tactic",
                description="Test",
                strategy_epic_key="TEST-1",
                deliverables=["Test"],
                timeline="1 week",
                effort_estimate=estimate,
                success_criteria=["Done"],
                project_key="TEST"
            )

            result = self.client.export_tactic(tactic)
            assert result["story_points"] == expected_points

    def test_full_export_with_epic_linking(self):
        """Test full export with proper epic linking."""
        strategy = JiraStrategy(
            title="API Gateway Implementation",
            description="Implement centralized API gateway",
            objectives=["Centralize API management", "Improve security"],
            assumptions=["Gateway solution selected"],
            timeline="3 months",
            project_key="API"
        )

        tactics = [
            JiraTactic(
                title="Setup Gateway Infrastructure", 
                description="Set up basic gateway infrastructure",
                strategy_epic_key="",  # Will be set by full export
                deliverables=["Infrastructure", "Basic config"],
                timeline="1 sprint",
                effort_estimate="5 SP",
                success_criteria=["Gateway accessible"],
                project_key="API",
                issue_type="Story"
            )
        ]

        result = self.client.export_full_strategy_with_tactics(strategy, tactics)
        
        assert result["strategy"]["title"] == "API Gateway Implementation"
        assert len(result["tactics"]) == 1
        
        # Verify epic linking
        epic_key = result["strategy"]["epic_key"]
        assert result["tactics"][0]["strategy_epic_key"] == epic_key


class TestIntegrationRoundTrip:
    """Integration tests for round-trip validation."""

    def test_idempotency_keys_unique(self):
        """Test that idempotency keys are unique per item."""
        strategy1 = NotionStrategy(
            title="Strategy A",
            description="Different strategy",
            objectives=["Goal 1"],
            assumptions=["Assumption 1"],
            metrics=["Metric 1"],
            timeline="Q1"
        )

        strategy2 = NotionStrategy(
            title="Strategy B", 
            description="Another strategy",
            objectives=["Goal 2"],
            assumptions=["Assumption 2"],
            metrics=["Metric 2"],
            timeline="Q2"
        )

        client = NotionClient("test-token")
        client.set_dry_run(True)

        result1 = client.export_strategy(strategy1, "page1")
        result2 = client.export_strategy(strategy2, "page2")

        # Idempotency keys should be different
        assert result1["idempotency_key"] != result2["idempotency_key"]

        # Same strategy should produce same key
        result3 = client.export_strategy(strategy1, "page1")
        assert result1["idempotency_key"] == result3["idempotency_key"]

    def test_cross_platform_data_consistency(self):
        """Test data consistency across all platforms."""
        # Create same strategy for all platforms
        base_data = {
            "title": "Cross-Platform Test Strategy",
            "description": "Test strategy for all platforms",
            "objectives": ["Objective 1", "Objective 2"],
            "assumptions": ["Assumption 1"],
            "timeline": "6 months"
        }

        # Notion version
        notion_strategy = NotionStrategy(
            metrics=["Metric 1", "Metric 2"],
            **base_data
        )

        # Trello version
        trello_strategy = TrelloStrategy(**base_data)

        # Jira version
        jira_strategy = JiraStrategy(
            project_key="TEST",
            **base_data
        )

        # Export all in dry-run
        notion_client = NotionClient("test")
        notion_client.set_dry_run(True)
        notion_result = notion_client.export_strategy(notion_strategy, "page")

        trello_client = TrelloClient("key", "token") 
        trello_client.set_dry_run(True)
        trello_result = trello_client.export_strategy(trello_strategy)

        jira_client = JiraClient("https://test.com", "user", "token")
        jira_client.set_dry_run(True) 
        jira_result = jira_client.export_strategy(jira_strategy)

        # All should have same core data
        assert notion_result["title"] == trello_result["title"] == jira_result["title"]
        assert all("exported_at" in result for result in [notion_result, trello_result, jira_result])
        assert all("idempotency_key" in result for result in [notion_result, trello_result, jira_result])

    def test_error_handling_dry_run(self):
        """Test error handling in dry-run mode."""
        # All clients should handle dry-run gracefully
        clients = [
            NotionClient("test"),
            TrelloClient("key", "token"),
            JiraClient("https://test.com", "user", "token")
        ]

        for client in clients:
            client.set_dry_run(True)
            preview_before = client.get_dry_run_preview()
            assert len(preview_before) == 0

            # Should work without network requests
            if isinstance(client, NotionClient):
                strategy = NotionStrategy("Test", "Desc", [], [], [], "Q1")
                client.export_strategy(strategy, "page")
            elif isinstance(client, TrelloClient):
                strategy = TrelloStrategy("Test", "Desc", [], [], "Q1")
                client.export_strategy(strategy)
            elif isinstance(client, JiraClient):
                strategy = JiraStrategy("Test", "Desc", [], [], "Q1", "TEST")
                client.export_strategy(strategy)

            preview_after = client.get_dry_run_preview()
            assert len(preview_after) > 0