'use client'

import { useEffect, useState } from 'react'
import { PersuasionRisk } from '@/types/experts'

interface PersuasionRiskGaugeProps {
  risk?: PersuasionRisk
}

export function PersuasionRiskGauge({ risk }: PersuasionRiskGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0)

  // Mock risk data for demonstration
  const defaultRisk: PersuasionRisk = {
    level: 'medium',
    score: 0.65,
    factors: [
      'Absolute claims detected',
      'Limited economic justification',
      'Strong psychological triggers'
    ],
    recommendations: [
      'Qualify absolute statements',
      'Add economic evidence',
      'Balance persuasion with ethics'
    ]
  }

  const currentRisk = risk || defaultRisk

  useEffect(() => {
    // Animate the gauge on mount
    const timer = setTimeout(() => {
      setAnimatedScore(currentRisk.score)
    }, 100)
    return () => clearTimeout(timer)
  }, [currentRisk.score])

  const getArcPath = (score: number) => {
    const radius = 50
    const circumference = Math.PI * radius
    const offset = circumference - (score * circumference)
    return { circumference, offset }
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low':
        return '#059669'
      case 'medium':
        return '#d97706'
      case 'high':
        return '#dc2626'
      default:
        return '#6b7280'
    }
  }

  const getRiskBgColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'bg-green-50 border-green-200'
      case 'medium':
        return 'bg-yellow-50 border-yellow-200'
      case 'high':
        return 'bg-red-50 border-red-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const { circumference, offset } = getArcPath(animatedScore)

  return (
    <div className="space-y-4">
      {/* Gauge */}
      <div className={`risk-gauge risk-${currentRisk.level} p-6 border rounded-lg ${getRiskBgColor(currentRisk.level)}`}>
        <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 120 120">
          {/* Background arc */}
          <circle
            cx="60"
            cy="60"
            r="50"
            className="gauge-arc gauge-background"
          />
          {/* Foreground arc */}
          <circle
            cx="60"
            cy="60"
            r="50"
            className="gauge-arc gauge-foreground"
            style={{
              stroke: getRiskColor(currentRisk.level),
              strokeDasharray: circumference,
              strokeDashoffset: offset,
              transition: 'stroke-dashoffset 1.5s ease-in-out'
            }}
          />
        </svg>
        
        {/* Center label */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl font-bold" style={{ color: getRiskColor(currentRisk.level) }}>
              {Math.round(currentRisk.score * 100)}%
            </div>
            <div className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              {currentRisk.level} Risk
            </div>
          </div>
        </div>
      </div>

      {/* Risk Details */}
      <div className="space-y-3">
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-2">Risk Factors</h4>
          <ul className="space-y-1">
            {currentRisk.factors.map((factor, index) => (
              <li key={index} className="text-sm text-gray-600 flex items-start space-x-2">
                <span className="text-red-400 mt-1 text-xs">⚠</span>
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-2">Recommendations</h4>
          <ul className="space-y-1">
            {currentRisk.recommendations.map((rec, index) => (
              <li key={index} className="text-sm text-gray-600 flex items-start space-x-2">
                <span className="text-green-500 mt-1 text-xs">✓</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Risk Level Indicator */}
      <div className="flex justify-between items-center pt-3 border-t">
        <div className="flex space-x-2">
          <div className={`w-3 h-3 rounded-full ${currentRisk.level === 'low' ? 'bg-green-500' : 'bg-gray-300'}`} />
          <div className={`w-3 h-3 rounded-full ${currentRisk.level === 'medium' ? 'bg-yellow-500' : 'bg-gray-300'}`} />
          <div className={`w-3 h-3 rounded-full ${currentRisk.level === 'high' ? 'bg-red-500' : 'bg-gray-300'}`} />
        </div>
        <span className="text-xs text-gray-500">
          Persuasion Ethics Score
        </span>
      </div>
    </div>
  )
}