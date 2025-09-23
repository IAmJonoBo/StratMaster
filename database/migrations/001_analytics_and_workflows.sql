-- StratMaster Database Schema Extensions
-- Analytics, ML Training, and Approval Workflows

-- Analytics metrics table for custom business intelligence
CREATE TABLE IF NOT EXISTS analytics_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    value FLOAT NOT NULL,
    labels JSONB,
    tenant_id VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for analytics_metrics
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_name_tenant ON analytics_metrics (metric_name, tenant_id);
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_timestamp ON analytics_metrics (timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_labels ON analytics_metrics USING GIN (labels);

-- Approval workflows management
CREATE TABLE IF NOT EXISTS approval_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_name VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    tenant_id VARCHAR(255) NOT NULL,
    requester_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT approval_workflows_status_check 
        CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')),
    CONSTRAINT approval_workflows_priority_check 
        CHECK (priority IN ('low', 'medium', 'high', 'urgent'))
);

-- Create indexes for approval_workflows
CREATE INDEX IF NOT EXISTS idx_approval_workflows_status_tenant ON approval_workflows (status, tenant_id);
CREATE INDEX IF NOT EXISTS idx_approval_workflows_requester ON approval_workflows (requester_id);
CREATE INDEX IF NOT EXISTS idx_approval_workflows_created ON approval_workflows (created_at);
CREATE INDEX IF NOT EXISTS idx_approval_workflows_due ON approval_workflows (due_date);

-- Approval workflow stages (multi-stage approvals)
CREATE TABLE IF NOT EXISTS approval_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES approval_workflows(id) ON DELETE CASCADE,
    stage_order INTEGER NOT NULL,
    stage_name VARCHAR(255) NOT NULL,
    required_approvals INTEGER DEFAULT 1,
    current_approvals INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT approval_stages_status_check 
        CHECK (status IN ('pending', 'approved', 'rejected', 'skipped')),
    CONSTRAINT approval_stages_order_positive CHECK (stage_order > 0),
    CONSTRAINT approval_stages_required_positive CHECK (required_approvals > 0),
    CONSTRAINT approval_stages_current_non_negative CHECK (current_approvals >= 0),
    
    -- Unique constraint to prevent duplicate stage orders per workflow
    UNIQUE (workflow_id, stage_order)
);

-- Create indexes for approval_stages
CREATE INDEX IF NOT EXISTS idx_approval_stages_workflow ON approval_stages (workflow_id);
CREATE INDEX IF NOT EXISTS idx_approval_stages_status ON approval_stages (status);

-- Individual approval actions
CREATE TABLE IF NOT EXISTS approval_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES approval_workflows(id) ON DELETE CASCADE,
    stage_id UUID NOT NULL REFERENCES approval_stages(id) ON DELETE CASCADE,
    approver_id VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,
    comments TEXT,
    signature_data JSONB, -- For mobile signature capture
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT approval_actions_action_check 
        CHECK (action IN ('approved', 'rejected', 'abstained')),
    
    -- Prevent duplicate approvals by same user for same stage
    UNIQUE (stage_id, approver_id)
);

-- Create indexes for approval_actions
CREATE INDEX IF NOT EXISTS idx_approval_actions_workflow ON approval_actions (workflow_id);
CREATE INDEX IF NOT EXISTS idx_approval_actions_stage ON approval_actions (stage_id);
CREATE INDEX IF NOT EXISTS idx_approval_actions_approver ON approval_actions (approver_id);
CREATE INDEX IF NOT EXISTS idx_approval_actions_action ON approval_actions (action);

-- ML training experiments and model metadata
CREATE TABLE IF NOT EXISTS ml_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    parameters JSONB,
    training_config JSONB,
    metrics JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    tenant_id VARCHAR(255),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    model_path VARCHAR(500),
    mlflow_run_id VARCHAR(255),
    
    -- Constraints
    CONSTRAINT ml_experiments_status_check 
        CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

-- Create indexes for ml_experiments
CREATE INDEX IF NOT EXISTS idx_ml_experiments_name_tenant ON ml_experiments (experiment_name, tenant_id);
CREATE INDEX IF NOT EXISTS idx_ml_experiments_status ON ml_experiments (status);
CREATE INDEX IF NOT EXISTS idx_ml_experiments_type ON ml_experiments (model_type);
CREATE INDEX IF NOT EXISTS idx_ml_experiments_started ON ml_experiments (started_at);

-- Constitutional compliance tracking for ML models
CREATE TABLE IF NOT EXISTS constitutional_compliance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES ml_experiments(id) ON DELETE CASCADE,
    content_id VARCHAR(255), -- Reference to content being evaluated
    category VARCHAR(100) NOT NULL, -- safety, accuracy, bias, etc.
    score FLOAT NOT NULL,
    threshold FLOAT NOT NULL,
    passed BOOLEAN NOT NULL,
    details JSONB,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT constitutional_compliance_score_range CHECK (score >= 0 AND score <= 1),
    CONSTRAINT constitutional_compliance_threshold_range CHECK (threshold >= 0 AND threshold <= 1),
    CONSTRAINT constitutional_compliance_category_check 
        CHECK (category IN ('safety', 'accuracy', 'bias', 'fairness', 'transparency', 'privacy', 'robustness'))
);

-- Create indexes for constitutional_compliance
CREATE INDEX IF NOT EXISTS idx_constitutional_compliance_experiment ON constitutional_compliance (experiment_id);
CREATE INDEX IF NOT EXISTS idx_constitutional_compliance_category ON constitutional_compliance (category);
CREATE INDEX IF NOT EXISTS idx_constitutional_compliance_passed ON constitutional_compliance (passed);
CREATE INDEX IF NOT EXISTS idx_constitutional_compliance_evaluated ON constitutional_compliance (evaluated_at);

-- System configuration management
CREATE TABLE IF NOT EXISTS system_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(255) NOT NULL,
    config_value JSONB NOT NULL,
    environment VARCHAR(50) NOT NULL,
    tenant_id VARCHAR(255),
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    is_secret BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    
    -- Constraints
    CONSTRAINT system_configurations_env_check 
        CHECK (environment IN ('development', 'staging', 'production')),
    CONSTRAINT system_configurations_version_positive CHECK (version > 0)
);

-- Create indexes for system_configurations
CREATE INDEX IF NOT EXISTS idx_system_configurations_key_env ON system_configurations (config_key, environment);
CREATE INDEX IF NOT EXISTS idx_system_configurations_tenant ON system_configurations (tenant_id);
CREATE INDEX IF NOT EXISTS idx_system_configurations_active ON system_configurations (is_active);
CREATE INDEX IF NOT EXISTS idx_system_configurations_updated ON system_configurations (updated_at);

-- Audit log for compliance and tracking
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(100) NOT NULL, -- 'workflow', 'experiment', 'configuration'
    entity_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL, -- 'created', 'updated', 'approved', 'rejected'
    actor_id VARCHAR(255) NOT NULL, -- User who performed the action
    tenant_id VARCHAR(255),
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Create indexes for audit_logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs (actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs (tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs (action);

-- Mobile notification tracking
CREATE TABLE IF NOT EXISTS mobile_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES approval_workflows(id) ON DELETE CASCADE,
    recipient_id VARCHAR(255) NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    payload JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    sent_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT mobile_notifications_status_check 
        CHECK (status IN ('pending', 'sent', 'failed', 'read')),
    CONSTRAINT mobile_notifications_type_check 
        CHECK (notification_type IN ('approval_request', 'approval_reminder', 'workflow_completed', 'workflow_cancelled'))
);

-- Create indexes for mobile_notifications
CREATE INDEX IF NOT EXISTS idx_mobile_notifications_workflow ON mobile_notifications (workflow_id);
CREATE INDEX IF NOT EXISTS idx_mobile_notifications_recipient ON mobile_notifications (recipient_id);
CREATE INDEX IF NOT EXISTS idx_mobile_notifications_status ON mobile_notifications (status);
CREATE INDEX IF NOT EXISTS idx_mobile_notifications_sent ON mobile_notifications (sent_at);

-- Create function for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to relevant tables
DROP TRIGGER IF EXISTS update_approval_workflows_updated_at ON approval_workflows;
CREATE TRIGGER update_approval_workflows_updated_at 
    BEFORE UPDATE ON approval_workflows 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_system_configurations_updated_at ON system_configurations;
CREATE TRIGGER update_system_configurations_updated_at 
    BEFORE UPDATE ON system_configurations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create composite indexes for performance
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_composite 
    ON analytics_metrics (tenant_id, metric_name, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_approval_workflows_composite 
    ON approval_workflows (tenant_id, status, created_at DESC);

-- Comments for documentation
COMMENT ON TABLE analytics_metrics IS 'Stores custom business intelligence metrics';
COMMENT ON TABLE approval_workflows IS 'Main approval workflow tracking';
COMMENT ON TABLE approval_stages IS 'Multi-stage approval configuration';
COMMENT ON TABLE approval_actions IS 'Individual approval/rejection actions';
COMMENT ON TABLE ml_experiments IS 'ML training experiment tracking';
COMMENT ON TABLE constitutional_compliance IS 'AI constitutional compliance scores';
COMMENT ON TABLE system_configurations IS 'Environment-specific configuration management';
COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail for compliance';
COMMENT ON TABLE mobile_notifications IS 'Mobile push notification tracking';