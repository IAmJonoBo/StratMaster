import { DisciplineMemo, EvaluationRequest, CouncilVote } from '@/types/experts'

const API_BASE_URL = process.env.STRATMASTER_API_URL || 'http://localhost:8080'

class APIError extends Error {
  constructor(message: string, public status: number) {
    super(message)
    this.name = 'APIError'
  }
}

async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.text()
    throw new APIError(`API request failed: ${error}`, response.status)
  }

  return response.json()
}

export async function evaluateStrategy(request: EvaluationRequest): Promise<DisciplineMemo[]> {
  return apiRequest<DisciplineMemo[]>('/experts/evaluate', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export async function aggregateVote(request: {
  strategy_id: string
  weights: Record<string, number>
  memos: DisciplineMemo[]
}): Promise<CouncilVote> {
  return apiRequest<CouncilVote>('/experts/vote', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export async function healthCheck(): Promise<{ status: string; service: string }> {
  return apiRequest<{ status: string; service: string }>('/experts/health')
}

// Utility function to calculate overall risk score from memos
export function calculateRiskScore(memos: DisciplineMemo[]): number {
  if (memos.length === 0) return 0

  const totalScore = memos.reduce((sum, memo) => sum + memo.overall_score, 0)
  const averageScore = totalScore / memos.length

  // Convert score to risk (inverse relationship)
  return 1 - averageScore
}

// Utility function to get risk level from score
export function getRiskLevel(score: number): 'low' | 'medium' | 'high' {
  if (score < 0.3) return 'low'
  if (score < 0.7) return 'medium'
  return 'high'
}