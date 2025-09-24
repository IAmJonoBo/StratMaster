"""Privacy controls and PII redaction for StratMaster."""

from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Any

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PrivacyMode(str, Enum):
    """Privacy mode settings for workspace."""
    STRICT = "strict"          # Maximum privacy, all PII redacted
    MODERATE = "moderate"      # Standard business privacy
    RELAXED = "relaxed"        # Minimal privacy controls
    CUSTOM = "custom"          # Custom privacy configuration


class DataSource(str, Enum):
    """Data source types for privacy controls."""
    WEB_RESEARCH = "web_research"
    UPLOADED_DOCUMENTS = "uploaded_documents"
    USER_INPUT = "user_input"
    API_RESPONSES = "api_responses"
    ANALYSIS_RESULTS = "analysis_results"


class PIIType(str, Enum):
    """Types of personally identifiable information."""
    PERSON = "PERSON"
    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    PHONE_NUMBER = "PHONE_NUMBER"
    CREDIT_CARD = "CREDIT_CARD"
    IP_ADDRESS = "IP_ADDRESS"
    LOCATION = "LOCATION"
    DATE_TIME = "DATE_TIME"
    US_SSN = "US_SSN"
    IBAN_CODE = "IBAN_CODE"
    URL = "URL"
    CRYPTO = "CRYPTO"
    MEDICAL_LICENSE = "MEDICAL_LICENSE"
    US_PASSPORT = "US_PASSPORT"
    US_DRIVER_LICENSE = "US_DRIVER_LICENSE"


class PrivacySettings(BaseModel):
    """Privacy settings for a workspace."""

    workspace_id: str
    privacy_mode: PrivacyMode = PrivacyMode.MODERATE

    # Data source controls
    disable_web_research: bool = False
    restrict_model_vendors: list[str] = Field(default_factory=list)
    enforce_on_prem_retrieval: bool = False

    # PII redaction settings
    pii_redaction_enabled: bool = True
    redacted_pii_types: set[PIIType] = Field(
        default_factory=lambda: {
            PIIType.PERSON, PIIType.EMAIL_ADDRESS, PIIType.PHONE_NUMBER,
            PIIType.CREDIT_CARD, PIIType.US_SSN, PIIType.IBAN_CODE
        }
    )

    # Data retention
    data_retention_days: int = 365
    auto_delete_research_data: bool = False

    # Compliance settings
    require_provenance: bool = True
    audit_all_queries: bool = True

    # Custom rules
    custom_redaction_patterns: dict[str, str] = Field(default_factory=dict)
    allowed_domains: list[str] = Field(default_factory=list)
    blocked_domains: list[str] = Field(default_factory=list)


class PIIRedactor:
    """PII detection and redaction using Microsoft Presidio."""

    def __init__(self):
        """Initialize Presidio analyzer and anonymizer engines."""
        try:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            logger.info("Initialized Presidio PII redaction engines")
        except Exception as e:
            logger.error(f"Failed to initialize Presidio engines: {e}")
            self.analyzer = None
            self.anonymizer = None

    def analyze_text(self, text: str, language: str = "en") -> list[dict[str, Any]]:
        """Analyze text for PII entities."""
        if not self.analyzer:
            logger.warning("Presidio analyzer not available")
            return []

        try:
            results = self.analyzer.analyze(text=text, language=language)

            pii_entities = []
            for result in results:
                pii_entities.append({
                    "entity_type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "text": text[result.start:result.end]
                })

            return pii_entities

        except Exception as e:
            logger.error(f"PII analysis failed: {e}")
            return []

    def redact_text(
        self,
        text: str,
        pii_types: set[PIIType],
        redaction_method: str = "replace",
        replacement_text: str = "[REDACTED]",
        language: str = "en"
    ) -> dict[str, Any]:
        """Redact PII from text."""
        if not self.analyzer or not self.anonymizer:
            logger.warning("Presidio engines not available, returning original text")
            return {"text": text, "entities_found": [], "redacted": False}

        try:
            # Analyze text for PII
            analyzer_results = self.analyzer.analyze(
                text=text,
                language=language,
                entities=[pii_type.value for pii_type in pii_types]
            )

            if not analyzer_results:
                return {"text": text, "entities_found": [], "redacted": False}

            # Anonymize/redact detected PII
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results,
                operators={
                    "DEFAULT": {
                        "type": redaction_method,
                        "new_value": replacement_text
                    }
                }
            )

            # Extract entity information
            entities_found = []
            for result in analyzer_results:
                entities_found.append({
                    "entity_type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "original_text": text[result.start:result.end]
                })

            return {
                "text": anonymized_result.text,
                "entities_found": entities_found,
                "redacted": True
            }

        except Exception as e:
            logger.error(f"PII redaction failed: {e}")
            return {"text": text, "entities_found": [], "redacted": False}

    def apply_custom_redaction(
        self,
        text: str,
        custom_patterns: dict[str, str]
    ) -> str:
        """Apply custom redaction patterns."""
        redacted_text = text

        for pattern_name, pattern in custom_patterns.items():
            try:
                # Replace pattern with redaction placeholder
                redacted_text = re.sub(
                    pattern,
                    f"[{pattern_name.upper()}]",
                    redacted_text,
                    flags=re.IGNORECASE
                )
            except re.error as e:
                logger.error(f"Invalid regex pattern '{pattern_name}': {e}")

        return redacted_text


class WorkspacePrivacyManager:
    """Manages privacy controls for workspaces."""

    def __init__(self):
        self.redactor = PIIRedactor()
        self.workspace_settings: dict[str, PrivacySettings] = {}

    def get_privacy_settings(self, workspace_id: str) -> PrivacySettings:
        """Get privacy settings for workspace."""
        if workspace_id not in self.workspace_settings:
            # Create default settings
            self.workspace_settings[workspace_id] = PrivacySettings(
                workspace_id=workspace_id
            )

        return self.workspace_settings[workspace_id]

    def update_privacy_settings(
        self,
        workspace_id: str,
        settings: PrivacySettings
    ) -> None:
        """Update privacy settings for workspace."""
        settings.workspace_id = workspace_id
        self.workspace_settings[workspace_id] = settings

        logger.info(f"Updated privacy settings for workspace {workspace_id}")

    def is_data_source_allowed(
        self,
        workspace_id: str,
        data_source: DataSource
    ) -> bool:
        """Check if data source is allowed for workspace."""
        settings = self.get_privacy_settings(workspace_id)

        if data_source == DataSource.WEB_RESEARCH:
            return not settings.disable_web_research

        # Add more data source checks as needed
        return True

    def is_model_vendor_allowed(
        self,
        workspace_id: str,
        vendor: str
    ) -> bool:
        """Check if model vendor is allowed for workspace."""
        settings = self.get_privacy_settings(workspace_id)

        if not settings.restrict_model_vendors:
            return True

        return vendor in settings.restrict_model_vendors

    def is_domain_allowed(self, workspace_id: str, domain: str) -> bool:
        """Check if domain is allowed for web research."""
        settings = self.get_privacy_settings(workspace_id)

        # Check blocked domains first
        if domain in settings.blocked_domains:
            return False

        # If allowed domains list is empty, allow all (except blocked)
        if not settings.allowed_domains:
            return True

        # Check if domain is in allowed list
        return domain in settings.allowed_domains

    def process_text_for_privacy(
        self,
        workspace_id: str,
        text: str,
        data_source: DataSource,
        language: str = "en"
    ) -> dict[str, Any]:
        """Process text according to workspace privacy settings."""
        settings = self.get_privacy_settings(workspace_id)

        result = {
            "original_text": text,
            "processed_text": text,
            "redacted": False,
            "entities_found": [],
            "privacy_applied": []
        }

        # Check if PII redaction is enabled
        if settings.pii_redaction_enabled:
            redaction_result = self.redactor.redact_text(
                text=text,
                pii_types=settings.redacted_pii_types,
                language=language
            )

            result["processed_text"] = redaction_result["text"]
            result["redacted"] = redaction_result["redacted"]
            result["entities_found"] = redaction_result["entities_found"]

            if redaction_result["redacted"]:
                result["privacy_applied"].append("pii_redaction")

        # Apply custom redaction patterns
        if settings.custom_redaction_patterns:
            custom_redacted = self.redactor.apply_custom_redaction(
                result["processed_text"],
                settings.custom_redaction_patterns
            )

            if custom_redacted != result["processed_text"]:
                result["processed_text"] = custom_redacted
                result["privacy_applied"].append("custom_redaction")

        return result

    def validate_privacy_compliance(
        self,
        workspace_id: str,
        operation: str,
        data_sources: list[DataSource],
        model_vendor: str | None = None,
        domains: list[str] | None = None
    ) -> dict[str, Any]:
        """Validate if operation complies with privacy settings."""
        settings = self.get_privacy_settings(workspace_id)

        compliance_result = {
            "compliant": True,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }

        # Check data sources
        for data_source in data_sources:
            if not self.is_data_source_allowed(workspace_id, data_source):
                compliance_result["compliant"] = False
                compliance_result["violations"].append(
                    f"Data source {data_source.value} is not allowed"
                )

        # Check model vendor
        if model_vendor and not self.is_model_vendor_allowed(workspace_id, model_vendor):
            compliance_result["compliant"] = False
            compliance_result["violations"].append(
                f"Model vendor {model_vendor} is not allowed"
            )

        # Check domains
        if domains:
            for domain in domains:
                if not self.is_domain_allowed(workspace_id, domain):
                    compliance_result["violations"].append(
                        f"Domain {domain} is blocked or not in allowed list"
                    )
                    compliance_result["compliant"] = False

        # Add recommendations based on privacy mode
        if settings.privacy_mode == PrivacyMode.STRICT:
            compliance_result["recommendations"].append(
                "Strict privacy mode: Consider using only on-premise models and data sources"
            )

        return compliance_result

    def generate_privacy_report(self, workspace_id: str) -> dict[str, Any]:
        """Generate privacy compliance report for workspace."""
        settings = self.get_privacy_settings(workspace_id)

        report = {
            "workspace_id": workspace_id,
            "privacy_mode": settings.privacy_mode.value,
            "pii_protection": {
                "enabled": settings.pii_redaction_enabled,
                "types_redacted": [pii_type.value for pii_type in settings.redacted_pii_types],
                "custom_patterns": len(settings.custom_redaction_patterns)
            },
            "data_source_controls": {
                "web_research_disabled": settings.disable_web_research,
                "restricted_vendors": settings.restrict_model_vendors,
                "on_prem_only": settings.enforce_on_prem_retrieval
            },
            "compliance_settings": {
                "provenance_required": settings.require_provenance,
                "audit_all_queries": settings.audit_all_queries,
                "data_retention_days": settings.data_retention_days
            },
            "domain_controls": {
                "allowed_domains": len(settings.allowed_domains),
                "blocked_domains": len(settings.blocked_domains)
            }
        }

        # Add compliance assessment
        if settings.privacy_mode == PrivacyMode.STRICT:
            report["compliance_level"] = "High"
        elif settings.privacy_mode == PrivacyMode.MODERATE:
            report["compliance_level"] = "Standard"
        else:
            report["compliance_level"] = "Basic"

        return report


# Privacy policy templates
PRIVACY_POLICY_TEMPLATES = {
    PrivacyMode.STRICT: PrivacySettings(
        workspace_id="",
        privacy_mode=PrivacyMode.STRICT,
        disable_web_research=True,
        enforce_on_prem_retrieval=True,
        pii_redaction_enabled=True,
        redacted_pii_types={
            PIIType.PERSON, PIIType.EMAIL_ADDRESS, PIIType.PHONE_NUMBER,
            PIIType.CREDIT_CARD, PIIType.US_SSN, PIIType.IBAN_CODE,
            PIIType.IP_ADDRESS, PIIType.LOCATION, PIIType.DATE_TIME,
            PIIType.MEDICAL_LICENSE, PIIType.US_PASSPORT, PIIType.US_DRIVER_LICENSE
        },
        data_retention_days=90,
        auto_delete_research_data=True,
        require_provenance=True,
        audit_all_queries=True
    ),

    PrivacyMode.MODERATE: PrivacySettings(
        workspace_id="",
        privacy_mode=PrivacyMode.MODERATE,
        disable_web_research=False,
        enforce_on_prem_retrieval=False,
        pii_redaction_enabled=True,
        redacted_pii_types={
            PIIType.PERSON, PIIType.EMAIL_ADDRESS, PIIType.PHONE_NUMBER,
            PIIType.CREDIT_CARD, PIIType.US_SSN, PIIType.IBAN_CODE
        },
        data_retention_days=365,
        require_provenance=True,
        audit_all_queries=True
    ),

    PrivacyMode.RELAXED: PrivacySettings(
        workspace_id="",
        privacy_mode=PrivacyMode.RELAXED,
        disable_web_research=False,
        enforce_on_prem_retrieval=False,
        pii_redaction_enabled=True,
        redacted_pii_types={PIIType.CREDIT_CARD, PIIType.US_SSN, PIIType.IBAN_CODE},
        data_retention_days=730,
        require_provenance=False,
        audit_all_queries=False
    )
}


def create_privacy_settings_from_template(
    workspace_id: str,
    template: PrivacyMode
) -> PrivacySettings:
    """Create privacy settings from template."""
    if template not in PRIVACY_POLICY_TEMPLATES:
        raise ValueError(f"Unknown privacy template: {template}")

    settings = PRIVACY_POLICY_TEMPLATES[template].copy()
    settings.workspace_id = workspace_id

    return settings
