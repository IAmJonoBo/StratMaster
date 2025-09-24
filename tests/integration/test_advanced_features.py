"""
Integration tests for StratMaster advanced features.
Tests analytics, approval workflows, ML experiments, and system configuration.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta

import pytest
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from stratmaster_api.app import create_app


@pytest.fixture
def test_database_url():
    """Test database URL - override in CI/testing environment."""
    return "postgresql://stratmaster:stratmaster@localhost:5432/stratmaster_test"


@pytest.fixture
async def test_client():
    """Create test client for API testing."""
    app = create_app()
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def db_session(test_database_url):
    """Database session for direct database testing."""
    engine = create_engine(test_database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestAnalyticsIntegration:
    """Test analytics metrics collection and querying."""
    
    async def test_analytics_metrics_crud(self, test_client):
        """Test creating and retrieving analytics metrics."""
        # Create a metric
        metric_data = {
            "metric_name": "strategy_success_rate",
            "value": 0.87,
            "labels": {"category": "technology", "region": "north_america"},
            "tenant_id": "test-tenant"
        }
        
        response = await test_client.post("/analytics/metrics", json=metric_data)
        assert response.status_code == 201
        
        metric_id = response.json()["id"]
        
        # Retrieve the metric
        response = await test_client.get(f"/analytics/metrics/{metric_id}")
        assert response.status_code == 200
        
        metric = response.json()
        assert metric["metric_name"] == "strategy_success_rate"
        assert metric["value"] == 0.87
        assert metric["labels"]["category"] == "technology"
    
    async def test_analytics_aggregation(self, test_client):
        """Test analytics data aggregation queries."""
        # Create multiple metrics for aggregation
        metrics = [
            {"metric_name": "conversion_rate", "value": 0.15, "tenant_id": "test-tenant"},
            {"metric_name": "conversion_rate", "value": 0.18, "tenant_id": "test-tenant"},
            {"metric_name": "conversion_rate", "value": 0.22, "tenant_id": "test-tenant"},
        ]
        
        for metric in metrics:
            await test_client.post("/analytics/metrics", json=metric)
        
        # Query aggregated data
        response = await test_client.get(
            "/analytics/aggregated", 
            params={"metric_name": "conversion_rate", "tenant_id": "test-tenant"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] >= 3
        assert data["average"] > 0.15


class TestApprovalWorkflowIntegration:
    """Test approval workflow system end-to-end."""
    
    async def test_workflow_creation(self, test_client):
        """Test creating an approval workflow."""
        workflow_data = {
            "workflow_name": "strategy_approval",
            "title": "Q4 2024 Brand Strategy Approval",
            "description": "Approval for new brand strategy targeting Gen Z consumers",
            "priority": "high",
            "tenant_id": "test-tenant",
            "requester_id": "user123",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        response = await test_client.post("/workflows", json=workflow_data)
        assert response.status_code == 201
        
        workflow = response.json()
        assert workflow["status"] == "pending"
        assert workflow["priority"] == "high"
        
        return workflow["id"]
    
    async def test_multi_stage_approval(self, test_client):
        """Test multi-stage approval process."""
        # Create workflow
        workflow_id = await self.test_workflow_creation(test_client)
        
        # Create approval stages
        stages = [
            {"stage_order": 1, "stage_name": "Legal Review", "required_approvals": 1},
            {"stage_order": 2, "stage_name": "Marketing Director", "required_approvals": 1},
            {"stage_order": 3, "stage_name": "Executive Approval", "required_approvals": 2}
        ]
        
        for stage in stages:
            stage["workflow_id"] = workflow_id
            response = await test_client.post("/workflows/stages", json=stage)
            assert response.status_code == 201
        
        # Get workflow with stages
        response = await test_client.get(f"/workflows/{workflow_id}")
        assert response.status_code == 200
        
        workflow = response.json()
        assert len(workflow["stages"]) == 3
        assert workflow["stages"][0]["stage_name"] == "Legal Review"
    
    async def test_approval_action(self, test_client):
        """Test submitting approval actions."""
        workflow_id = await self.test_workflow_creation(test_client)
        
        # Create a stage
        stage_data = {
            "workflow_id": workflow_id,
            "stage_order": 1,
            "stage_name": "Review",
            "required_approvals": 1
        }
        
        response = await test_client.post("/workflows/stages", json=stage_data)
        stage_id = response.json()["id"]
        
        # Submit approval
        approval_data = {
            "workflow_id": workflow_id,
            "stage_id": stage_id,
            "approver_id": "approver123",
            "action": "approved",
            "comments": "Looks good to proceed"
        }
        
        response = await test_client.post("/workflows/actions", json=approval_data)
        assert response.status_code == 201
        
        # Check stage status updated
        response = await test_client.get(f"/workflows/stages/{stage_id}")
        stage = response.json()
        assert stage["current_approvals"] == 1
        assert stage["status"] == "approved"


class TestMLExperimentIntegration:
    """Test ML experiment tracking and constitutional compliance."""
    
    async def test_experiment_creation(self, test_client):
        """Test creating ML experiment."""
        experiment_data = {
            "experiment_name": "constitutional_classifier_v1",
            "model_type": "bert-base-uncased",
            "parameters": {
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 10
            },
            "training_config": {
                "dataset": "constitutional_compliance_v1",
                "validation_split": 0.2
            },
            "tenant_id": "test-tenant"
        }
        
        response = await test_client.post("/ml/experiments", json=experiment_data)
        assert response.status_code == 201
        
        experiment = response.json()
        assert experiment["status"] == "running"
        assert experiment["model_type"] == "bert-base-uncased"
        
        return experiment["id"]
    
    async def test_constitutional_compliance_tracking(self, test_client):
        """Test tracking constitutional compliance scores."""
        experiment_id = await self.test_experiment_creation(test_client)
        
        # Record compliance scores
        compliance_data = [
            {
                "experiment_id": experiment_id,
                "content_id": "content_001",
                "category": "safety",
                "score": 0.92,
                "threshold": 0.85,
                "passed": True,
                "details": {"confidence": 0.95, "model_version": "v1.0"}
            },
            {
                "experiment_id": experiment_id,
                "content_id": "content_002",
                "category": "bias",
                "score": 0.78,
                "threshold": 0.80,
                "passed": False,
                "details": {"confidence": 0.88, "bias_type": "gender"}
            }
        ]
        
        for compliance in compliance_data:
            response = await test_client.post("/ml/compliance", json=compliance)
            assert response.status_code == 201
        
        # Query compliance results
        response = await test_client.get(f"/ml/experiments/{experiment_id}/compliance")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) == 2
        assert results[0]["category"] in ["safety", "bias"]
    
    async def test_experiment_completion(self, test_client):
        """Test completing ML experiment with metrics."""
        experiment_id = await self.test_experiment_creation(test_client)
        
        # Update experiment with completion metrics
        completion_data = {
            "status": "completed",
            "metrics": {
                "accuracy": 0.94,
                "precision": 0.92,
                "recall": 0.89,
                "f1_score": 0.905
            },
            "model_path": "s3://ml-models/constitutional_classifier_v1"
        }
        
        response = await test_client.put(f"/ml/experiments/{experiment_id}", json=completion_data)
        assert response.status_code == 200
        
        # Verify update
        response = await test_client.get(f"/ml/experiments/{experiment_id}")
        experiment = response.json()
        assert experiment["status"] == "completed"
        assert experiment["metrics"]["accuracy"] == 0.94


class TestSystemConfigurationIntegration:
    """Test system configuration management."""
    
    async def test_configuration_management(self, test_client):
        """Test creating and managing system configurations."""
        config_data = {
            "config_key": "ml_model_threshold",
            "config_value": {"safety": 0.85, "bias": 0.80, "accuracy": 0.90},
            "environment": "production",
            "tenant_id": "test-tenant",
            "created_by": "admin_user"
        }
        
        response = await test_client.post("/config", json=config_data)
        assert response.status_code == 201
        
        config = response.json()
        assert config["is_active"] is True
        assert config["version"] == 1
        
        # Update configuration (creates new version)
        update_data = {
            "config_value": {"safety": 0.90, "bias": 0.85, "accuracy": 0.92}
        }
        
        response = await test_client.put(f"/config/{config['id']}", json=update_data)
        assert response.status_code == 200
        
        # Check version increment
        response = await test_client.get(f"/config/{config['id']}")
        updated_config = response.json()
        assert updated_config["version"] == 2
    
    async def test_environment_specific_config(self, test_client):
        """Test environment-specific configuration retrieval."""
        environments = ["development", "staging", "production"]
        config_key = "api_rate_limit"
        
        # Create configs for different environments
        for env in environments:
            config_data = {
                "config_key": config_key,
                "config_value": {"requests_per_minute": 100 * (environments.index(env) + 1)},
                "environment": env,
                "tenant_id": "test-tenant"
            }
            await test_client.post("/config", json=config_data)
        
        # Retrieve production config
        response = await test_client.get(
            "/config", 
            params={"key": config_key, "environment": "production", "tenant_id": "test-tenant"}
        )
        assert response.status_code == 200
        
        config = response.json()
        assert config["environment"] == "production"
        assert config["config_value"]["requests_per_minute"] == 300


class TestMobileNotificationIntegration:
    """Test mobile notification system."""
    
    async def test_notification_creation(self, test_client):
        """Test creating mobile notifications."""
        # First create a workflow
        workflow_test = TestApprovalWorkflowIntegration()
        workflow_id = await workflow_test.test_workflow_creation(test_client)
        
        notification_data = {
            "workflow_id": workflow_id,
            "recipient_id": "mobile_user123",
            "notification_type": "approval_request",
            "title": "New Approval Request",
            "message": "You have a new approval request for Q4 2024 Brand Strategy",
            "payload": {
                "workflow_title": "Q4 2024 Brand Strategy Approval",
                "priority": "high",
                "due_date": "2024-12-31"
            }
        }
        
        response = await test_client.post("/mobile/notifications", json=notification_data)
        assert response.status_code == 201
        
        notification = response.json()
        assert notification["status"] == "pending"
        assert notification["notification_type"] == "approval_request"
    
    async def test_notification_status_update(self, test_client):
        """Test updating notification status (sent, read)."""
        workflow_test = TestApprovalWorkflowIntegration()
        workflow_id = await workflow_test.test_workflow_creation(test_client)
        
        # Create notification
        notification_data = {
            "workflow_id": workflow_id,
            "recipient_id": "mobile_user123",
            "notification_type": "approval_request",
            "title": "Test Notification",
            "message": "Test message"
        }
        
        response = await test_client.post("/mobile/notifications", json=notification_data)
        notification_id = response.json()["id"]
        
        # Mark as sent
        response = await test_client.patch(
            f"/mobile/notifications/{notification_id}",
            json={"status": "sent"}
        )
        assert response.status_code == 200
        
        # Mark as read
        response = await test_client.patch(
            f"/mobile/notifications/{notification_id}",
            json={"status": "read"}
        )
        assert response.status_code == 200
        
        # Verify final status
        response = await test_client.get(f"/mobile/notifications/{notification_id}")
        notification = response.json()
        assert notification["status"] == "read"
        assert notification["read_at"] is not None


class TestAuditLogIntegration:
    """Test audit logging functionality."""
    
    def test_audit_log_creation(self, db_session):
        """Test audit log creation through database triggers."""
        # This would typically be triggered by database operations
        # Testing direct audit log creation for verification
        
        audit_data = {
            "entity_type": "workflow",
            "entity_id": str(uuid.uuid4()),
            "action": "created",
            "actor_id": "test_user",
            "tenant_id": "test-tenant",
            "details": {"workflow_name": "test_workflow", "priority": "medium"}
        }
        
        # Insert audit log
        sql = text("""
            INSERT INTO audit_logs (entity_type, entity_id, action, actor_id, tenant_id, details)
            VALUES (:entity_type, :entity_id, :action, :actor_id, :tenant_id, :details)
            RETURNING id
        """)
        
        result = db_session.execute(sql, {
            **audit_data,
            "details": json.dumps(audit_data["details"])
        })
        audit_id = result.fetchone()[0]
        
        # Verify audit log exists
        sql = text("SELECT * FROM audit_logs WHERE id = :audit_id")
        result = db_session.execute(sql, {"audit_id": audit_id})
        audit_log = result.fetchone()
        
        assert audit_log is not None
        assert audit_log.entity_type == "workflow"
        assert audit_log.action == "created"


@pytest.mark.asyncio
async def test_end_to_end_approval_workflow():
    """End-to-end test of complete approval workflow."""
    async with httpx.AsyncClient(app=create_app(), base_url="http://testserver") as client:
        # 1. Create workflow
        workflow_data = {
            "workflow_name": "comprehensive_test",
            "title": "End-to-End Test Workflow",
            "description": "Testing complete approval flow",
            "priority": "medium",
            "tenant_id": "e2e-tenant",
            "requester_id": "requester123"
        }
        
        response = await client.post("/workflows", json=workflow_data)
        workflow_id = response.json()["id"]
        
        # 2. Add stages
        stages = [
            {"stage_order": 1, "stage_name": "Initial Review", "required_approvals": 1},
            {"stage_order": 2, "stage_name": "Final Approval", "required_approvals": 2}
        ]
        
        stage_ids = []
        for stage in stages:
            stage["workflow_id"] = workflow_id
            response = await client.post("/workflows/stages", json=stage)
            stage_ids.append(response.json()["id"])
        
        # 3. Create mobile notifications
        notification_data = {
            "workflow_id": workflow_id,
            "recipient_id": "approver1",
            "notification_type": "approval_request",
            "title": "New Approval Required",
            "message": "Please review the End-to-End Test Workflow"
        }
        await client.post("/mobile/notifications", json=notification_data)
        
        # 4. Submit approvals
        # First stage approval
        approval1 = {
            "workflow_id": workflow_id,
            "stage_id": stage_ids[0],
            "approver_id": "approver1",
            "action": "approved",
            "comments": "Initial review passed"
        }
        await client.post("/workflows/actions", json=approval1)
        
        # Second stage approvals (needs 2)
        for i, approver in enumerate(["approver2", "approver3"]):
            approval = {
                "workflow_id": workflow_id,
                "stage_id": stage_ids[1],
                "approver_id": approver,
                "action": "approved",
                "comments": f"Final approval {i+1}"
            }
            await client.post("/workflows/actions", json=approval)
        
        # 5. Verify workflow completion
        response = await client.get(f"/workflows/{workflow_id}")
        workflow = response.json()
        
        # Check all stages are approved
        for stage in workflow["stages"]:
            assert stage["status"] == "approved"
        
        assert workflow["status"] == "approved"
        
        print("✅ End-to-end approval workflow test completed successfully!")


if __name__ == "__main__":
    # Run the end-to-end test
    asyncio.run(test_end_to_end_approval_workflow())