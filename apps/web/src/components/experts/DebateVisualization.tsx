'use client'

import { useState, useEffect } from 'react'
import { DebateTrace, DebateTurn } from '@/types/debate'

interface DebateVisualizationProps {
  debate?: DebateTrace
  isLive?: boolean
  onTurnUpdate?: (turn: DebateTurn) => void
}

interface AgentConfig {
  name: string
  color: string
  bgColor: string
  icon: string
}

const AGENT_CONFIGS: Record<string, AgentConfig> = {
  Researcher: {
    name: 'Researcher',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 border-blue-200',
    icon: '🔍'
  },
  Synthesiser: {
    name: 'Synthesiser', 
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 border-purple-200',
    icon: '🧠'
  },
  Strategist: {
    name: 'Strategist',
    color: 'text-green-600', 
    bgColor: 'bg-green-50 border-green-200',
    icon: '🎯'
  },
  Adversary: {
    name: 'Adversary',
    color: 'text-red-600',
    bgColor: 'bg-red-50 border-red-200', 
    icon: '⚔️'
  },
  ConstitutionalCritic: {
    name: 'Constitutional Critic',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50 border-yellow-200',
    icon: '⚖️'
  },
  Recommender: {
    name: 'Recommender',
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50 border-indigo-200',
    icon: '📋'
  }
}

export function DebateVisualization({ debate, isLive = false, onTurnUpdate }: DebateVisualizationProps) {
  const [visibleTurns, setVisibleTurns] = useState<number>(0)
  const [isAnimating, setIsAnimating] = useState(false)

  // Animate turns appearing one by one
  useEffect(() => {
    if (!debate?.turns || debate.turns.length === 0) return

    if (visibleTurns < debate.turns.length) {
      const timer = setTimeout(() => {
        setIsAnimating(true)
        setTimeout(() => {
          setVisibleTurns(prev => prev + 1)
          setIsAnimating(false)
        }, 150)
      }, isLive ? 1000 : 300) // Slower animation for live updates
      
      return () => clearTimeout(timer)
    }
  }, [debate?.turns, visibleTurns, isLive])

  // Reset animation when debate changes
  useEffect(() => {
    setVisibleTurns(0)
  }, [debate?.turns?.length])

  if (!debate || !debate.turns || debate.turns.length === 0) {
    return (
      <div className="debate-visualization empty-state">
        <div className="text-center py-12">
          <div className="text-4xl mb-4">💬</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Debate Yet</h3>
          <p className="text-gray-600">
            Start a strategy evaluation to see the expert debate unfold in real-time
          </p>
        </div>
      </div>
    )
  }

  const currentTurns = debate.turns.slice(0, visibleTurns)

  return (
    <div className="debate-visualization">
      <div className="debate-header mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Expert Debate</h3>
            <p className="text-sm text-gray-600">
              {debate.turns.length} turns • {debate.verdict ? `Verdict: ${debate.verdict}` : 'In progress...'}
            </p>
          </div>
          {isLive && visibleTurns < debate.turns.length && (
            <div className="flex items-center space-x-2 text-sm text-blue-600">
              <div className="animate-pulse w-2 h-2 bg-blue-600 rounded-full"></div>
              <span>Live updates</span>
            </div>
          )}
        </div>
      </div>

      <div className="debate-timeline space-y-4">
        {currentTurns.map((turn, index) => {
          const config = AGENT_CONFIGS[turn.role] || {
            name: turn.role,
            color: 'text-gray-600',
            bgColor: 'bg-gray-50 border-gray-200',
            icon: '🤖'
          }

          const isNew = index === visibleTurns - 1 && isAnimating

          return (
            <div 
              key={`${turn.agent}-${index}`}
              className={`debate-turn ${config.bgColor} border rounded-lg p-4 transition-all duration-300 ${
                isNew ? 'transform scale-105 shadow-lg' : ''
              }`}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 rounded-full bg-white border-2 border-current flex items-center justify-center text-lg">
                    {config.icon}
                  </div>
                </div>
                
                <div className="flex-grow min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <div className={`font-medium ${config.color}`}>
                      {config.name}
                    </div>
                    <div className="flex items-center space-x-2 text-xs text-gray-500">
                      <span>Turn {index + 1}</span>
                      {isNew && (
                        <span className="animate-pulse bg-green-500 text-white px-2 py-1 rounded text-xs">
                          NEW
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-800 leading-relaxed">
                    {turn.content}
                  </div>

                  {/* Grounding information */}
                  {turn.grounding && turn.grounding.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <details className="text-xs text-gray-600">
                        <summary className="cursor-pointer hover:text-gray-800">
                          Evidence & Sources ({turn.grounding.length})
                        </summary>
                        <div className="mt-2 space-y-1">
                          {turn.grounding.map((ground, idx) => (
                            <div key={idx} className="flex items-center space-x-2">
                              <span className="text-blue-500">🔗</span>
                              <span>Source {ground.source_id} (chars {ground.start_char}-{ground.end_char})</span>
                            </div>
                          ))}
                        </div>
                      </details>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}

        {/* Loading indicator for next turn */}
        {isLive && visibleTurns < debate.turns.length && (
          <div className="debate-turn-loading bg-gray-50 border border-dashed border-gray-300 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <div className="animate-spin w-6 h-6 border-2 border-gray-300 border-t-blue-600 rounded-full"></div>
              <span className="text-gray-600">Processing next argument...</span>
            </div>
          </div>
        )}
      </div>

      {/* Verdict section */}
      {debate.verdict && visibleTurns >= debate.turns.length && (
        <div className="debate-verdict mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-blue-600 text-lg">⚖️</span>
            <h4 className="font-medium text-blue-900">Final Verdict</h4>
          </div>
          <p className="text-blue-800">{debate.verdict}</p>
        </div>
      )}

      {/* Debate progress indicator */}
      <div className="debate-progress mt-4">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Progress</span>
          <span>{visibleTurns} / {debate.turns.length}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
            style={{ width: `${(visibleTurns / debate.turns.length) * 100}%` }}
          ></div>
        </div>
      </div>
    </div>
  )
}