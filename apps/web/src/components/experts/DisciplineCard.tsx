'use client'

import { DisciplineMemo } from '@/types/experts'
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline'
import { useState } from 'react'

interface DisciplineCardProps {
  memo: DisciplineMemo
}

export function DisciplineCard({ memo }: DisciplineCardProps) {
  const [expanded, setExpanded] = useState(false)

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100'
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return '🚫'
      case 'warning':
        return '⚠️'
      case 'info':
        return 'ℹ️'
      default:
        return '•'
    }
  }

  return (
    <div className="discipline-card">
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center space-x-3">
          {expanded ? (
            <ChevronDownIcon className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronRightIcon className="h-4 w-4 text-gray-400" />
          )}
          <div>
            <h4 className="font-medium text-gray-900 capitalize">
              {memo.discipline.replace('_', ' ')}
            </h4>
            <p className="text-sm text-gray-500">{memo.expert_name}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getScoreColor(memo.overall_score)}`}>
            {Math.round(memo.overall_score * 100)}%
          </span>
          <span className="text-xs text-gray-400">
            {memo.findings.length} finding{memo.findings.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pl-7 space-y-4">
          {/* Summary */}
          <div>
            <h5 className="text-sm font-medium text-gray-700 mb-1">Summary</h5>
            <p className="text-sm text-gray-600">{memo.summary}</p>
          </div>

          {/* Findings */}
          {memo.findings.length > 0 && (
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-2">Findings</h5>
              <div className="space-y-2">
                {memo.findings.map((finding, index) => (
                  <div 
                    key={finding.id || index}
                    className={`p-3 rounded-lg border ${
                      finding.severity === 'error' ? 'severity-error' :
                      finding.severity === 'warning' ? 'severity-warning' :
                      'severity-info'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      <span className="text-sm">{getSeverityIcon(finding.severity)}</span>
                      <div>
                        <h6 className="text-sm font-medium">{finding.title}</h6>
                        <p className="text-xs text-gray-600 mt-1">{finding.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {memo.recommendations.length > 0 && (
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-2">Recommendations</h5>
              <ul className="space-y-1">
                {memo.recommendations.map((rec, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-start space-x-2">
                    <span className="text-stratmaster-primary mt-1">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Confidence */}
          <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t">
            <span>Confidence: {Math.round(memo.confidence * 100)}%</span>
            <span>{new Date(memo.timestamp).toLocaleTimeString()}</span>
          </div>
        </div>
      )}
    </div>
  )
}