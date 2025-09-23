export interface DisciplineMemo {
  discipline: string
  expert_name: string
  overall_score: number
  findings: Finding[]
  recommendations: string[]
  summary: string
  confidence: number
  timestamp: string
}

export interface Finding {
  id: string
  severity: 'error' | 'warning' | 'info'
  title: string
  description: string
  category?: string
  impact_score?: number
}

export interface CouncilVote {
  strategy_id: string
  weighted_score: number
  consensus_level: number
  dissenting_views: string[]
  final_recommendation: string
  confidence: number
  timestamp: string
}

export interface Strategy {
  id: string
  title: string
  content: string
  summary?: string
  context?: Record<string, any>
}

export interface EvaluationRequest {
  strategy: Strategy
  disciplines: string[]
}

export interface PersuasionRisk {
  level: 'low' | 'medium' | 'high'
  score: number
  factors: string[]
  recommendations: string[]
}

export interface MessageMapNode {
  id: string
  type: 'core' | 'supporting' | 'proof'
  content: string
  level: number
  parent_id?: string
  children: string[]
}