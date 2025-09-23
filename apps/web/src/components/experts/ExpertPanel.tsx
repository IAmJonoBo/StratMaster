'use client'

import { useState, useEffect } from 'react'
import { DisciplineMemo, EvaluationRequest, Strategy } from '@/types/experts'
import { DisciplineCard } from './DisciplineCard'
import { evaluateStrategy } from '@/lib/api'

const sampleStrategy: Strategy = {
  id: 'demo-strategy-1',
  title: 'New Product Launch Campaign',
  content: 'Launch our revolutionary new product with guaranteed results. This breakthrough technology will transform your life overnight with no effort required. Our secret formula is scientifically proven by doctors.',
  summary: 'High-impact product launch with bold claims'
}

const availableDisciplines = [
  { id: 'psychology', name: 'Psychology', description: 'Behavioral insights and persuasion principles' },
  { id: 'design', name: 'Design', description: 'Visual design and user experience' },
  { id: 'communication', name: 'Communication', description: 'Message clarity and structure' },
  { id: 'brand_science', name: 'Brand Science', description: 'Brand positioning and consistency' },
  { id: 'economics', name: 'Economics', description: 'Business viability and market dynamics' },
  { id: 'legal', name: 'Legal', description: 'Compliance and risk assessment' },
]

export function ExpertPanel() {
  const [memos, setMemos] = useState<DisciplineMemo[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedDisciplines, setSelectedDisciplines] = useState<string[]>([
    'psychology', 'legal', 'economics'
  ])
  const [strategy, setStrategy] = useState<Strategy>(sampleStrategy)

  const handleEvaluate = async () => {
    setLoading(true)
    try {
      const request: EvaluationRequest = {
        strategy,
        disciplines: selectedDisciplines
      }
      const result = await evaluateStrategy(request)
      setMemos(result)
    } catch (error) {
      console.error('Evaluation failed:', error)
      // For demo purposes, show mock data
      setMemos(generateMockMemos())
    } finally {
      setLoading(false)
    }
  }

  const generateMockMemos = (): DisciplineMemo[] => {
    return selectedDisciplines.map(discipline => ({
      discipline,
      expert_name: `${discipline.charAt(0).toUpperCase() + discipline.slice(1)} Expert`,
      overall_score: Math.random() * 0.4 + 0.4, // Score between 0.4 and 0.8
      findings: [
        {
          id: `${discipline}-1`,
          severity: discipline === 'legal' ? 'error' : discipline === 'economics' ? 'warning' : 'info',
          title: discipline === 'legal' ? 'Risky Claims Detected' : 
                 discipline === 'economics' ? 'Insufficient ROI Analysis' :
                 'Design Elements Missing',
          description: discipline === 'legal' ? 'Strategy contains absolute claims like "guaranteed results" that may lead to legal issues' :
                      discipline === 'economics' ? 'Strategy lacks key economic considerations like costs and market analysis' :
                      'Strategy should include visual design considerations'
        }
      ],
      recommendations: [
        discipline === 'legal' ? 'Remove or qualify absolute claims to avoid potential legal liability' :
        discipline === 'economics' ? 'Include economic feasibility analysis with costs, ROI, and market considerations' :
        'Provide mockups, wireframes, or visual examples to support the strategy'
      ],
      summary: `${discipline.charAt(0).toUpperCase() + discipline.slice(1)} evaluation complete with key findings and recommendations.`,
      confidence: Math.random() * 0.3 + 0.7, // Confidence between 0.7 and 1.0
      timestamp: new Date().toISOString()
    }))
  }

  const toggleDiscipline = (disciplineId: string) => {
    setSelectedDisciplines(prev => 
      prev.includes(disciplineId) 
        ? prev.filter(id => id !== disciplineId)
        : [...prev, disciplineId]
    )
  }

  useEffect(() => {
    // Auto-evaluate on component mount for demo
    handleEvaluate()
  }, [selectedDisciplines])

  return (
    <div className="expert-panel">
      {/* Strategy Input */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Strategy Content
        </label>
        <textarea
          value={strategy.content}
          onChange={(e) => setStrategy({ ...strategy, content: e.target.value })}
          className="w-full h-24 p-3 border border-gray-300 rounded-lg text-sm"
          placeholder="Enter your strategy content here..."
        />
      </div>

      {/* Discipline Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Expert Disciplines
        </label>
        <div className="grid grid-cols-2 gap-2">
          {availableDisciplines.map(discipline => (
            <label key={discipline.id} className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={selectedDisciplines.includes(discipline.id)}
                onChange={() => toggleDiscipline(discipline.id)}
                className="rounded border-gray-300 text-stratmaster-primary focus:ring-stratmaster-primary"
              />
              <span className="font-medium">{discipline.name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Evaluate Button */}
      <button
        onClick={handleEvaluate}
        disabled={loading || selectedDisciplines.length === 0}
        className="w-full py-2 px-4 bg-stratmaster-primary text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed mb-6"
      >
        {loading ? 'Evaluating...' : 'Evaluate Strategy'}
      </button>

      {/* Results */}
      {memos.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">
            Expert Evaluations ({memos.length})
          </h3>
          {memos.map((memo, index) => (
            <DisciplineCard key={`${memo.discipline}-${index}`} memo={memo} />
          ))}
        </div>
      )}
    </div>
  )
}