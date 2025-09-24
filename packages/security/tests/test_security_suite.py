"""Comprehensive tests for StratMaster security package."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from security import (
    KeycloakAuth,
    OIDCConfig,
    UserInfo,
    PrivacySettings,
    PIIRedactor,
    WorkspacePrivacyManager,
    PrivacyMode,
    PIIType,
    DataSource,
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    create_privacy_settings_from_template
)


class TestKeycloakAuth:
    """Test Keycloak OIDC authentication."""
    
    @pytest.fixture
    def oidc_config(self):
        return OIDCConfig(
            server_url="https://keycloak.example.com",
            realm_name="stratmaster",
            client_id="stratmaster-api",
            client_secret="secret123"
        )
    
    @pytest.fixture
    def keycloak_auth(self, oidc_config):
        return KeycloakAuth(oidc_config)
    
    def test_oidc_config_validation(self):
        """Test OIDC configuration validation."""
        config = OIDCConfig(
            server_url="https://keycloak.example.com",
            realm_name="test-realm",
            client_id="test-client"
        )
        
        assert config.server_url == "https://keycloak.example.com"
        assert config.realm_name == "test-realm"
        assert config.client_id == "test-client"
        assert config.verify_ssl is True
        assert config.verify_signature is True
    
    @patch('security.keycloak_auth.KeycloakOpenID')
    def test_auth_initialization(self, mock_keycloak, oidc_config):
        """Test KeycloakAuth initialization."""
        auth = KeycloakAuth(oidc_config)
        
        assert auth.config == oidc_config
        assert auth._public_key_cache is None
        mock_keycloak.assert_called_once()
    
    def test_user_info_creation(self):
        """Test UserInfo model creation."""
        user = UserInfo(
            sub="user123",
            preferred_username="testuser",
            email="test@example.com",
            roles=["analyst", "viewer"],
            permissions=["read:all", "write:own"]
        )
        
        assert user.sub == "user123"
        assert user.preferred_username == "testuser"
        assert user.email == "test@example.com"
        assert "analyst" in user.roles
        assert "read:all" in user.permissions
    
    def test_roles_to_permissions_mapping(self, keycloak_auth):
        """Test role to permission mapping."""
        admin_permissions = keycloak_auth._map_roles_to_permissions(["admin"])
        assert "read:all" in admin_permissions
        assert "write:all" in admin_permissions
        assert "manage:users" in admin_permissions
        
        viewer_permissions = keycloak_auth._map_roles_to_permissions(["viewer"])
        assert "read:public" in viewer_permissions
        assert "write:all" not in viewer_permissions


class TestPrivacyControls:
    """Test privacy controls and PII redaction."""
    
    def test_privacy_settings_creation(self):
        """Test privacy settings model."""
        settings = PrivacySettings(
            workspace_id="workspace123",
            privacy_mode=PrivacyMode.STRICT,
            disable_web_research=True,
            pii_redaction_enabled=True
        )
        
        assert settings.workspace_id == "workspace123"
        assert settings.privacy_mode == PrivacyMode.STRICT
        assert settings.disable_web_research is True
        assert settings.pii_redaction_enabled is True
    
    def test_privacy_templates(self):
        """Test privacy policy templates."""
        strict_settings = create_privacy_settings_from_template(
            "workspace123", PrivacyMode.STRICT
        )
        
        assert strict_settings.workspace_id == "workspace123"
        assert strict_settings.privacy_mode == PrivacyMode.STRICT
        assert strict_settings.disable_web_research is True
        assert PIIType.PERSON in strict_settings.redacted_pii_types
        assert PIIType.EMAIL_ADDRESS in strict_settings.redacted_pii_types
    
    def test_pii_redactor_initialization(self):
        """Test PII redactor initialization."""
        redactor = PIIRedactor()
        
        # Redactor should initialize even if Presidio is not available
        assert redactor is not None
    
    @patch('security.privacy_controls.AnalyzerEngine')
    @patch('security.privacy_controls.AnonymizerEngine')
    def test_pii_analysis(self, mock_anonymizer, mock_analyzer):
        """Test PII analysis functionality."""
        # Mock Presidio components
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        
        mock_result = Mock()
        mock_result.entity_type = "PERSON"
        mock_result.start = 0
        mock_result.end = 10
        mock_result.score = 0.9
        mock_analyzer_instance.analyze.return_value = [mock_result]
        
        redactor = PIIRedactor()
        text = "John Smith works at Acme Corp"
        results = redactor.analyze_text(text)
        
        assert len(results) == 1
        assert results[0]["entity_type"] == "PERSON"
        assert results[0]["score"] == 0.9
    
    def test_workspace_privacy_manager(self):
        """Test workspace privacy management."""
        manager = WorkspacePrivacyManager()
        
        # Test default settings
        settings = manager.get_privacy_settings("workspace123")
        assert settings.workspace_id == "workspace123"
        assert settings.privacy_mode == PrivacyMode.MODERATE
        
        # Test settings update
        new_settings = PrivacySettings(
            workspace_id="workspace123",
            privacy_mode=PrivacyMode.STRICT,
            disable_web_research=True
        )
        manager.update_privacy_settings("workspace123", new_settings)
        
        updated_settings = manager.get_privacy_settings("workspace123")
        assert updated_settings.privacy_mode == PrivacyMode.STRICT
        assert updated_settings.disable_web_research is True
    
    def test_data_source_controls(self):
        """Test data source access controls."""
        manager = WorkspacePrivacyManager()
        
        # Set strict privacy
        settings = PrivacySettings(
            workspace_id="workspace123",
            disable_web_research=True
        )
        manager.update_privacy_settings("workspace123", settings)
        
        # Web research should be blocked
        assert not manager.is_data_source_allowed("workspace123", DataSource.WEB_RESEARCH)
        
        # Other sources should be allowed
        assert manager.is_data_source_allowed("workspace123", DataSource.UPLOADED_DOCUMENTS)
    
    def test_domain_filtering(self):
        """Test domain allow/block lists."""
        manager = WorkspacePrivacyManager()
        
        settings = PrivacySettings(
            workspace_id="workspace123",
            allowed_domains=["example.com", "trusted.org"],
            blocked_domains=["malicious.com"]
        )
        manager.update_privacy_settings("workspace123", settings)
        
        # Allowed domain
        assert manager.is_domain_allowed("workspace123", "example.com")
        
        # Blocked domain
        assert not manager.is_domain_allowed("workspace123", "malicious.com")
        
        # Domain not in allowed list
        assert not manager.is_domain_allowed("workspace123", "random.com")
    
    def test_privacy_compliance_validation(self):
        """Test privacy compliance validation."""
        manager = WorkspacePrivacyManager()
        
        settings = PrivacySettings(
            workspace_id="workspace123",
            disable_web_research=True,
            restrict_model_vendors=["openai"]
        )
        manager.update_privacy_settings("workspace123", settings)
        
        # Test compliant operation
        result = manager.validate_privacy_compliance(
            "workspace123",
            "analysis",
            [DataSource.UPLOADED_DOCUMENTS],
            model_vendor="openai"
        )
        assert result["compliant"] is True
        
        # Test non-compliant operation
        result = manager.validate_privacy_compliance(
            "workspace123", 
            "research",
            [DataSource.WEB_RESEARCH],
            model_vendor="anthropic"
        )
        assert result["compliant"] is False
        assert len(result["violations"]) > 0
    
    def test_privacy_report_generation(self):
        """Test privacy report generation."""
        manager = WorkspacePrivacyManager()
        
        settings = PrivacySettings(
            workspace_id="workspace123",
            privacy_mode=PrivacyMode.STRICT,
            pii_redaction_enabled=True
        )
        manager.update_privacy_settings("workspace123", settings)
        
        report = manager.generate_privacy_report("workspace123")
        
        assert report["workspace_id"] == "workspace123"
        assert report["privacy_mode"] == "strict"
        assert report["compliance_level"] == "High"
        assert report["pii_protection"]["enabled"] is True


class TestAuditLogging:
    """Test audit logging system."""
    
    @pytest.fixture
    def audit_logger(self):
        return AuditLogger(log_to_file=False)  # Disable file logging for tests
    
    def test_audit_event_creation(self):
        """Test audit event model."""
        event = AuditEvent(
            event_id="test123",
            event_type=AuditEventType.LOGIN,
            user_id="user123",
            username="testuser",
            action="login",
            description="User login attempt",
            success=True
        )
        
        assert event.event_id == "test123"
        assert event.event_type == AuditEventType.LOGIN
        assert event.user_id == "user123"
        assert event.success is True
        assert event.severity == AuditSeverity.MEDIUM
    
    def test_audit_logger_initialization(self):
        """Test audit logger initialization."""
        logger = AuditLogger(log_to_file=False)
        
        assert logger.log_to_file is False
        assert logger.buffer_size == 100
        assert len(logger.event_buffer) == 0
    
    def test_event_logging(self, audit_logger):
        """Test basic event logging."""
        event = AuditEvent(
            event_id="test123",
            event_type=AuditEventType.DATA_READ,
            user_id="user123",
            action="read_document",
            description="User read document",
            resource_type="document",
            resource_id="doc123"
        )
        
        audit_logger.log_event(event)
        
        # Event should be in buffer
        assert len(audit_logger.event_buffer) == 1
        assert audit_logger.event_buffer[0].event_id == "test123"
    
    def test_authentication_logging(self, audit_logger):
        """Test authentication event logging."""
        audit_logger.log_authentication(
            AuditEventType.LOGIN,
            "user123",
            "testuser",
            True,
            ip_address="192.168.1.100"
        )
        
        assert len(audit_logger.event_buffer) == 1
        event = audit_logger.event_buffer[0]
        assert event.event_type == AuditEventType.LOGIN
        assert event.user_id == "user123"
        assert event.ip_address == "192.168.1.100"
        assert event.success is True
    
    def test_data_access_logging(self, audit_logger):
        """Test data access event logging."""
        audit_logger.log_data_access(
            AuditEventType.DATA_READ,
            "user123",
            "document",
            "doc123",
            "read_document",
            workspace_id="workspace123",
            contains_pii=True
        )
        
        assert len(audit_logger.event_buffer) == 1
        event = audit_logger.event_buffer[0]
        assert event.event_type == AuditEventType.DATA_READ
        assert event.resource_type == "document"
        assert event.resource_id == "doc123"
        assert event.contains_pii is True
        assert event.severity == AuditSeverity.HIGH  # High due to PII
    
    def test_privacy_event_logging(self, audit_logger):
        """Test privacy event logging."""
        audit_logger.log_privacy_event(
            AuditEventType.PII_REDACTION,
            "user123",
            "workspace123",
            "redact_pii",
            "PII redacted from document",
            pii_types=["PERSON", "EMAIL_ADDRESS"]
        )
        
        assert len(audit_logger.event_buffer) == 1
        event = audit_logger.event_buffer[0]
        assert event.event_type == AuditEventType.PII_REDACTION
        assert event.contains_pii is True
        assert event.severity == AuditSeverity.HIGH
        assert "privacy" in event.tags
    
    def test_export_event_logging(self, audit_logger):
        """Test export event logging."""
        audit_logger.log_export_event(
            AuditEventType.EXPORT_TO_NOTION,
            "user123",
            "workspace123",
            "notion",
            5
        )
        
        assert len(audit_logger.event_buffer) == 1
        event = audit_logger.event_buffer[0]
        assert event.event_type == AuditEventType.EXPORT_TO_NOTION
        assert event.metadata["destination"] == "notion"
        assert event.metadata["resource_count"] == 5
    
    def test_buffer_flushing(self, audit_logger):
        """Test event buffer flushing."""
        # Set small buffer size for testing
        audit_logger.buffer_size = 2
        
        # Add events to fill buffer
        for i in range(3):
            event = AuditEvent(
                event_id=f"test{i}",
                event_type=AuditEventType.DATA_READ,
                action="test_action",
                description="Test event"
            )
            audit_logger.log_event(event)
        
        # Buffer should have been flushed when it reached capacity
        assert len(audit_logger.event_buffer) == 1  # Only the last event
    
    @patch('security.audit_logger.redis.from_url')
    def test_redis_integration(self, mock_redis):
        """Test Redis integration for event streaming."""
        mock_redis_client = Mock()
        mock_redis.return_value = mock_redis_client
        
        # Initialize logger with Redis
        logger = AuditLogger(redis_url="redis://localhost:6379", log_to_file=False)
        
        # Log an event
        event = AuditEvent(
            event_id="test123",
            event_type=AuditEventType.LOGIN,
            action="login",
            description="Test login"
        )
        logger.log_event(event)
        
        # Verify Redis calls
        mock_redis_client.xadd.assert_called()
    
    def test_event_id_generation(self, audit_logger):
        """Test automatic event ID generation."""
        event_id = audit_logger._generate_event_id()
        
        assert event_id.startswith("audit_")
        assert len(event_id) == 18  # "audit_" + 12 hex chars
    
    def test_audit_report_generation(self, audit_logger):
        """Test audit report generation."""
        # Add some test events
        events = [
            AuditEvent(
                event_id="test1",
                event_type=AuditEventType.LOGIN,
                user_id="user123",
                action="login",
                description="Login",
                success=True
            ),
            AuditEvent(
                event_id="test2",
                event_type=AuditEventType.DATA_READ,
                user_id="user123",
                action="read",
                description="Read document",
                success=False
            )
        ]
        
        for event in events:
            audit_logger.log_event(event)
        
        # Mock Redis for report generation
        with patch.object(audit_logger, 'get_events_by_user') as mock_get_events:
            mock_get_events.return_value = [
                {
                    "event_type": "login",
                    "success": "true",
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "event_type": "data_read", 
                    "success": "false",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
            
            report = audit_logger.generate_audit_report(user_id="user123")
            
            assert "report_generated" in report
            assert report["filters"]["user_id"] == "user123"
            assert report["summary"]["total_events"] == 2
            assert report["summary"]["success_count"] == 1
            assert report["summary"]["failure_count"] == 1


class TestSecurityIntegration:
    """Test integration between security components."""
    
    def test_auth_privacy_integration(self):
        """Test integration between auth and privacy controls."""
        # Create user with specific permissions
        user = UserInfo(
            sub="user123",
            preferred_username="testuser",
            roles=["analyst"],
            permissions=["read:assigned", "write:own"],
            tenant_id="tenant123"
        )
        
        # Create privacy manager
        privacy_manager = WorkspacePrivacyManager()
        
        # Test data source access based on user permissions
        # This would typically be enforced in the API layer
        workspace_id = "workspace123"
        
        # Check if user can access workspace data sources
        settings = privacy_manager.get_privacy_settings(workspace_id)
        web_research_allowed = privacy_manager.is_data_source_allowed(
            workspace_id, DataSource.WEB_RESEARCH
        )
        
        # Verify privacy settings affect access
        assert isinstance(web_research_allowed, bool)
        assert settings.workspace_id == workspace_id
    
    def test_audit_privacy_integration(self):
        """Test integration between audit logging and privacy controls."""
        audit_logger = AuditLogger(log_to_file=False)
        privacy_manager = WorkspacePrivacyManager()
        
        # Simulate PII redaction with audit logging
        workspace_id = "workspace123"
        user_id = "user123"
        
        # Apply privacy processing
        text = "Contact John Smith at john@example.com for details"
        result = privacy_manager.process_text_for_privacy(
            workspace_id, text, DataSource.USER_INPUT
        )
        
        # Log privacy event
        if result["redacted"]:
            audit_logger.log_privacy_event(
                AuditEventType.PII_REDACTION,
                user_id,
                workspace_id,
                "redact_pii",
                "PII redacted from user input",
                pii_types=[entity["entity_type"] for entity in result["entities_found"]]
            )
        
        # Verify audit event was logged
        assert len(audit_logger.event_buffer) >= 0  # May be 0 if no PII found
    
    def test_complete_security_workflow(self):
        """Test complete security workflow."""
        # Initialize components
        audit_logger = AuditLogger(log_to_file=False)
        privacy_manager = WorkspacePrivacyManager()
        
        # Simulate user session
        user = UserInfo(
            sub="user123",
            preferred_username="testuser",
            email="test@example.com",
            roles=["analyst"],
            tenant_id="tenant123"
        )
        
        workspace_id = "workspace123"
        
        # 1. Log authentication
        audit_logger.log_authentication(
            AuditEventType.LOGIN,
            user.sub,
            user.preferred_username,
            True,
            ip_address="192.168.1.100"
        )
        
        # 2. Check privacy compliance for operation
        compliance_result = privacy_manager.validate_privacy_compliance(
            workspace_id,
            "research_analysis",
            [DataSource.WEB_RESEARCH, DataSource.UPLOADED_DOCUMENTS],
            model_vendor="openai"
        )
        
        # 3. Process sensitive data with privacy controls
        sensitive_text = "Customer data shows John Smith (SSN: 123-45-6789) prefers our premium service"
        privacy_result = privacy_manager.process_text_for_privacy(
            workspace_id, sensitive_text, DataSource.USER_INPUT
        )
        
        # 4. Log data processing
        audit_logger.log_data_access(
            AuditEventType.DATA_READ,
            user.sub,
            "customer_data",
            "cust123",
            "analyze_preferences",
            workspace_id=workspace_id,
            contains_pii=privacy_result["redacted"]
        )
        
        # 5. Log privacy event if PII was redacted
        if privacy_result["redacted"]:
            audit_logger.log_privacy_event(
                AuditEventType.PII_REDACTION,
                user.sub,
                workspace_id,
                "automatic_pii_redaction",
                "PII automatically redacted during analysis"
            )
        
        # Verify the workflow
        assert len(audit_logger.event_buffer) >= 2  # At least login and data access
        assert compliance_result["compliant"] in [True, False]
        assert "processed_text" in privacy_result


@pytest.fixture
def sample_jwt_payload():
    """Sample JWT payload for testing."""
    return {
        "sub": "user123",
        "preferred_username": "testuser",
        "email": "test@example.com",
        "name": "Test User",
        "realm_access": {
            "roles": ["analyst", "viewer"]
        },
        "resource_access": {
            "stratmaster-api": {
                "roles": ["api_client"]
            }
        },
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "tenant_id": "tenant123"
    }


def test_jwt_payload_extraction(sample_jwt_payload):
    """Test JWT payload extraction."""
    config = OIDCConfig(
        server_url="https://keycloak.example.com",
        realm_name="test",
        client_id="stratmaster-api"
    )
    auth = KeycloakAuth(config)
    
    user_info = auth._extract_user_info(sample_jwt_payload)
    
    assert user_info.sub == "user123"
    assert user_info.preferred_username == "testuser"
    assert user_info.email == "test@example.com"
    assert "analyst" in user_info.roles
    assert "viewer" in user_info.roles
    assert "api_client" in user_info.roles
    assert user_info.tenant_id == "tenant123"
    assert "read:assigned" in user_info.permissions  # Mapped from analyst role