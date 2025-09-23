// Types for the debate system and DSPy telemetry integration

export interface GroundingSpan {
  source_id: string
  chunk_hash: string
  start_char: number
  end_char: number
}

export interface DebateTurn {
  agent: string
  role: 'Researcher' | 'Synthesiser' | 'Strategist' | 'Adversary' | 'ConstitutionalCritic' | 'Recommender'
  content: string
  grounding: GroundingSpan[]
}

export interface DebateTrace {
  turns: DebateTurn[]
  verdict?: string
}

export interface ConstitutionalPrinciple {
  id: string
  rule: string
}

export interface ConstitutionalPrompts {
  title: string
  id: string
  version: string
  principles: ConstitutionalPrinciple[]
  review?: Array<{
    metric: string
    guidance: string
  }>
}

export interface VerificationQuestion {
  id: string
  question: string
  claim_id: string
  verification_type: 'factual' | 'logical' | 'source'
}

export interface VerificationAnswer {
  question_id: string
  answer: string
  confidence: number
  supporting_evidence: string[]
  conflicts_detected: boolean
}

export interface VerificationResult {
  questions: VerificationQuestion[]
  answers: VerificationAnswer[]
  verified_claims: string[]
  flagged_claims: string[]
  amendments: string[]
  overall_confidence: number
}

export interface DSPyArtifact {
  program_name: string
  version: string
  created_at: string
  prompt: string
  steps: string[]
  compilation_metrics: Record<string, any>
  langfuse_trace_id?: string
}

export interface TelemetryEvent {
  event_type: string
  timestamp: string
  trace_id?: string
  [key: string]: any
}

export interface DSPyTelemetryState {
  current_trace?: string
  events: TelemetryEvent[]
  artifacts: DSPyArtifact[]
}

export interface EnhancedRecommendationRequest {
  tenant_id: string
  cep_id: string
  jtbd_ids: string[]
  risk_tolerance: 'low' | 'medium' | 'high'
  enable_cove?: boolean
  enable_dspy_telemetry?: boolean
  constitutional_strictness?: 'strict' | 'moderate' | 'lenient'
}

export interface ConstitutionalViolation {
  principle_id: string
  rule: string
  violation_description: string
  severity: 'error' | 'warning' | 'info'
}

export interface EnhancedDebateMetrics {
  constitutional_compliance: number
  verification_confidence: number
  total_critique_score: number
  debate_turns: number
  verified_claims_ratio: number
  constitutional_violations: ConstitutionalViolation[]
}

export interface DebateSystemState {
  debate?: DebateTrace
  verification_result?: VerificationResult
  constitutional_violations: ConstitutionalViolation[]
  metrics: EnhancedDebateMetrics
  dspy_telemetry?: DSPyTelemetryState
}

// UI State interfaces
export interface DebateVisualizationState {
  isLive: boolean
  currentTurn: number
  maxTurns: number
  animationSpeed: number
  showGrounding: boolean
  showTelemetry: boolean
}

export interface ConstitutionalConfigState {
  house_rules_enabled: boolean
  adversary_enabled: boolean
  critic_enabled: boolean
  strictness_level: 'strict' | 'moderate' | 'lenient'
  custom_principles: ConstitutionalPrinciple[]
}

export interface TelemetryDashboardState {
  traces: Array<{
    id: string
    name: string
    start_time: string
    end_time?: string
    success: boolean
    events: TelemetryEvent[]
  }>
  selected_trace?: string
  filter_program?: string
  show_raw_events: boolean
}

// API Response interfaces
export interface EnhancedRecommendationResponse {
  recommendation_id: string
  debate: DebateTrace
  verification_result: VerificationResult
  constitutional_violations: ConstitutionalViolation[]
  metrics: EnhancedDebateMetrics
  dspy_artifacts: DSPyArtifact[]
  telemetry_summary: {
    total_events: number
    trace_id: string
    programs_compiled: string[]
  }
}