'use client'

import { useState, useEffect } from 'react'
import { ConstitutionalPrompts, ConstitutionalPrinciple, ConstitutionalConfigState } from '@/types/debate'

interface ConstitutionalConfigProps {
  initialConfig?: ConstitutionalConfigState
  onConfigChange?: (config: ConstitutionalConfigState) => void
}

// Default constitutional prompts based on the YAML files
const DEFAULT_CONSTITUTIONAL_PROMPTS: Record<string, ConstitutionalPrompts> = {
  house: {
    title: "StratMaster House Rules",
    id: "constitutions/house", 
    version: "2024-10-01",
    principles: [
      {
        id: "sourcing",
        rule: "Always cite at least two sources with URLs or knowledge base identifiers for every key claim."
      },
      {
        id: "safety", 
        rule: "Decline or defer when a request violates legal, ethical, or security policy. Escalate to a human when unsure."
      },
      {
        id: "transparency",
        rule: "Expose reasoning steps, assumptions, and residual uncertainties using structured bullet points."
      }
    ],
    review: [
      {
        metric: "Provenance completeness",
        guidance: "Ensure each recommendation cites a minimum of two unique provenance IDs."
      },
      {
        metric: "Safety",
        guidance: "Reject or escalate any action that conflicts with policy."
      }
    ]
  },
  adversary: {
    title: "Strategic Adversary",
    id: "constitutions/adversary",
    version: "2024-10-01", 
    principles: [
      {
        id: "stress_test",
        rule: "Challenge every assumption with counterfactuals, adverse scenarios, and missing-data considerations."
      },
      {
        id: "red_team",
        rule: "Search for ethical, legal, or reputational failure modes and demand mitigations."
      }
    ],
    review: [
      {
        metric: "Counterfactual coverage",
        guidance: "Surface at least two failure scenarios and quantify their likelihood."
      }
    ]
  },
  critic: {
    title: "Constitutional Critic",
    id: "constitutions/critic",
    version: "2024-10-01",
    principles: [
      {
        id: "factual_accuracy",
        rule: "Reject any recommendation when supporting evidence lacks citations, conflicts with referenced sources, or relies on speculation."
      },
      {
        id: "proportionality", 
        rule: "Flag overconfident language. Require calibrated confidence bands tied to evidence strength."
      }
    ],
    review: [
      {
        metric: "Evidence alignment",
        guidance: "Each claim must map to explicit provenance with matching statements."
      },
      {
        metric: "Confidence calibration",
        guidance: "Confidence must correspond to the weakest supporting evidence grade."
      }
    ]
  }
}

export function ConstitutionalConfig({ initialConfig, onConfigChange }: ConstitutionalConfigProps) {
  const [config, setConfig] = useState<ConstitutionalConfigState>(() => ({
    house_rules_enabled: true,
    adversary_enabled: true, 
    critic_enabled: true,
    strictness_level: 'moderate',
    custom_principles: [],
    ...initialConfig
  }))

  const [activeTab, setActiveTab] = useState<'house' | 'adversary' | 'critic' | 'custom'>('house')
  const [editingPrinciple, setEditingPrinciple] = useState<ConstitutionalPrinciple | null>(null)

  useEffect(() => {
    onConfigChange?.(config)
  }, [config, onConfigChange])

  const toggleComponent = (component: keyof ConstitutionalConfigState) => {
    if (typeof config[component] === 'boolean') {
      setConfig(prev => ({
        ...prev,
        [component]: !prev[component]
      }))
    }
  }

  const updateStrictness = (level: 'strict' | 'moderate' | 'lenient') => {
    setConfig(prev => ({
      ...prev,
      strictness_level: level
    }))
  }

  const addCustomPrinciple = (principle: ConstitutionalPrinciple) => {
    setConfig(prev => ({
      ...prev,
      custom_principles: [...prev.custom_principles, principle]
    }))
  }

  const removeCustomPrinciple = (principleId: string) => {
    setConfig(prev => ({
      ...prev,
      custom_principles: prev.custom_principles.filter(p => p.id !== principleId)
    }))
  }

  const getStrictnessDescription = (level: string) => {
    switch (level) {
      case 'strict':
        return 'All constitutional violations result in rejection. Zero tolerance for non-compliance.'
      case 'moderate': 
        return 'Balance constitutional compliance with practical considerations. Allow minor violations with warnings.'
      case 'lenient':
        return 'Focus on major constitutional violations only. Provide guidance but allow flexibility.'
      default:
        return ''
    }
  }

  return (
    <div className="constitutional-config bg-white rounded-lg border">
      <div className="config-header p-4 border-b">
        <h3 className="text-lg font-medium text-gray-900">Constitutional Configuration</h3>
        <p className="text-sm text-gray-600 mt-1">
          Configure the constitutional rules and principles that guide the expert debate system
        </p>
      </div>

      {/* Component Toggles */}
      <div className="component-toggles p-4 border-b bg-gray-50">
        <h4 className="font-medium text-gray-900 mb-3">Active Components</h4>
        <div className="grid grid-cols-3 gap-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.house_rules_enabled}
              onChange={() => toggleComponent('house_rules_enabled')}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm font-medium">House Rules</span>
          </label>
          
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.adversary_enabled}
              onChange={() => toggleComponent('adversary_enabled')}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm font-medium">Adversary</span>
          </label>
          
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.critic_enabled}
              onChange={() => toggleComponent('critic_enabled')}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm font-medium">Constitutional Critic</span>
          </label>
        </div>
      </div>

      {/* Strictness Level */}
      <div className="strictness-config p-4 border-b">
        <h4 className="font-medium text-gray-900 mb-3">Enforcement Level</h4>
        <div className="space-y-2">
          {(['strict', 'moderate', 'lenient'] as const).map((level) => (
            <label key={level} className="flex items-start space-x-3">
              <input
                type="radio"
                name="strictness"
                value={level}
                checked={config.strictness_level === level}
                onChange={() => updateStrictness(level)}
                className="mt-0.5 border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <div>
                <div className="font-medium capitalize">{level}</div>
                <div className="text-sm text-gray-600">{getStrictnessDescription(level)}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Constitutional Principles Tabs */}
      <div className="principles-config">
        <div className="tab-nav flex border-b">
          {(['house', 'adversary', 'critic', 'custom'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab === 'house' ? 'House Rules' : 
               tab === 'adversary' ? 'Adversary' :
               tab === 'critic' ? 'Critic' : 'Custom'}
            </button>
          ))}
        </div>

        <div className="tab-content p-4">
          {activeTab !== 'custom' && (
            <div className="principles-list space-y-4">
              <div className="prompt-header mb-4">
                <h5 className="font-medium text-gray-900">{DEFAULT_CONSTITUTIONAL_PROMPTS[activeTab].title}</h5>
                <p className="text-sm text-gray-600">Version {DEFAULT_CONSTITUTIONAL_PROMPTS[activeTab].version}</p>
              </div>
              
              {DEFAULT_CONSTITUTIONAL_PROMPTS[activeTab].principles.map((principle) => (
                <div key={principle.id} className="principle-card p-3 border rounded bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <h6 className="font-medium text-sm capitalize">{principle.id.replace('_', ' ')}</h6>
                    <span className="text-xs text-gray-500 px-2 py-1 bg-white rounded">Built-in</span>
                  </div>
                  <p className="text-sm text-gray-700">{principle.rule}</p>
                </div>
              ))}

              {DEFAULT_CONSTITUTIONAL_PROMPTS[activeTab].review && (
                <div className="review-metrics mt-4 pt-4 border-t">
                  <h6 className="font-medium text-sm mb-2">Review Metrics</h6>
                  <div className="space-y-2">
                    {DEFAULT_CONSTITUTIONAL_PROMPTS[activeTab].review!.map((metric, idx) => (
                      <div key={idx} className="text-sm">
                        <span className="font-medium">{metric.metric}:</span>
                        <span className="text-gray-600 ml-1">{metric.guidance}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'custom' && (
            <div className="custom-principles">
              <div className="custom-header flex items-center justify-between mb-4">
                <h5 className="font-medium text-gray-900">Custom Principles</h5>
                <button
                  onClick={() => setEditingPrinciple({ id: '', rule: '' })}
                  className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Add Principle
                </button>
              </div>

              {config.custom_principles.length === 0 && (
                <div className="empty-state text-center py-8 text-gray-500">
                  <div className="text-2xl mb-2">📜</div>
                  <p>No custom principles defined</p>
                  <p className="text-sm">Add custom constitutional rules specific to your organization</p>
                </div>
              )}

              <div className="custom-principles-list space-y-3">
                {config.custom_principles.map((principle) => (
                  <div key={principle.id} className="principle-card p-3 border rounded">
                    <div className="flex items-center justify-between mb-2">
                      <h6 className="font-medium text-sm">{principle.id}</h6>
                      <div className="space-x-2">
                        <button
                          onClick={() => setEditingPrinciple(principle)}
                          className="text-xs text-blue-600 hover:text-blue-800"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => removeCustomPrinciple(principle.id)}
                          className="text-xs text-red-600 hover:text-red-800"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700">{principle.rule}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Edit Principle Modal */}
      {editingPrinciple && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full">
            <h4 className="font-medium mb-4">
              {editingPrinciple.id ? 'Edit Principle' : 'Add New Principle'}
            </h4>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Principle ID</label>
                <input
                  type="text"
                  value={editingPrinciple.id}
                  onChange={(e) => setEditingPrinciple({ ...editingPrinciple, id: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm"
                  placeholder="e.g., custom_safety_check"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Rule Description</label>
                <textarea
                  value={editingPrinciple.rule}
                  onChange={(e) => setEditingPrinciple({ ...editingPrinciple, rule: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm h-24 resize-none"
                  placeholder="Describe the constitutional rule or principle..."
                />
              </div>
            </div>
            
            <div className="flex space-x-2 mt-6">
              <button
                onClick={() => {
                  if (editingPrinciple.id && editingPrinciple.rule) {
                    if (config.custom_principles.find(p => p.id === editingPrinciple.id)) {
                      // Update existing
                      setConfig(prev => ({
                        ...prev,
                        custom_principles: prev.custom_principles.map(p =>
                          p.id === editingPrinciple.id ? editingPrinciple : p
                        )
                      }))
                    } else {
                      // Add new
                      addCustomPrinciple(editingPrinciple)
                    }
                  }
                  setEditingPrinciple(null)
                }}
                disabled={!editingPrinciple.id || !editingPrinciple.rule}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {editingPrinciple.id && config.custom_principles.find(p => p.id === editingPrinciple.id) ? 'Update' : 'Add'}
              </button>
              <button
                onClick={() => setEditingPrinciple(null)}
                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded text-sm hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}