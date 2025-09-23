import { ExpertPanel } from '@/components/experts/ExpertPanel'
import { MessageMapBuilder } from '@/components/experts/MessageMapBuilder'
import { PersuasionRiskGauge } from '@/components/experts/PersuasionRiskGauge'
import { DebateVisualization } from '@/components/experts/DebateVisualization'
import { ConstitutionalConfig } from '@/components/experts/ConstitutionalConfig'

export default function DashboardPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Strategy Dashboard</h1>
        <p className="mt-2 text-gray-600">
          AI-powered brand strategy evaluation with expert discipline analysis, constitutional debate system, and real-time DSPy telemetry
        </p>
      </div>

      {/* Enhanced layout with new components */}
      <div className="space-y-8">
        
        {/* Configuration Panel */}
        <div className="config-section">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Constitutional Configuration</h2>
          <ConstitutionalConfig />
        </div>

        {/* Main Analysis Layout */}
        <div className="analysis-layout grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Panel: Expert Panel */}
          <div className="col-span-1">
            <div className="panel-card bg-white rounded-lg border p-6">
              <div className="panel-header mb-4">
                <h2 className="text-lg font-medium text-gray-900">Expert Panel</h2>
                <p className="text-sm text-gray-600">Configure and run expert evaluations</p>
              </div>
              <div className="panel-content">
                <ExpertPanel />
              </div>
            </div>
          </div>

          {/* Center Panel: Risk Analysis & Debate */}
          <div className="col-span-1">
            <div className="space-y-6">
              
              {/* Risk Analysis */}
              <div className="panel-card bg-white rounded-lg border p-6">
                <div className="panel-header mb-4">
                  <h2 className="text-lg font-medium text-gray-900">Risk Analysis</h2>
                  <p className="text-sm text-gray-600">Persuasion ethics and compliance assessment</p>
                </div>
                <div className="panel-content">
                  <PersuasionRiskGauge />
                  <div className="mt-6 pt-6 border-t">
                    <h3 className="text-md font-medium text-gray-900 mb-4">Key Findings</h3>
                    <div className="space-y-3">
                      <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                        <div className="text-sm font-medium text-green-800">Strong Brand Positioning</div>
                        <div className="text-sm text-green-600">Clear value proposition identified</div>
                      </div>
                      <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <div className="text-sm font-medium text-yellow-800">Legal Compliance Review</div>
                        <div className="text-sm text-yellow-600">Consider privacy policy updates</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Real-time Debate Visualization */}
              <div className="panel-card bg-white rounded-lg border p-6">
                <div className="panel-header mb-4">
                  <h2 className="text-lg font-medium text-gray-900">Expert Debate</h2>
                  <p className="text-sm text-gray-600">Real-time constitutional debate process</p>
                </div>
                <div className="panel-content">
                  <DebateVisualization />
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel: Message Map & Telemetry */}
          <div className="col-span-1">
            <div className="space-y-6">
              
              {/* Message Map Builder */}
              <div className="panel-card bg-white rounded-lg border p-6">
                <div className="panel-header mb-4">
                  <h2 className="text-lg font-medium text-gray-900">Message Map</h2>
                  <p className="text-sm text-gray-600">Strategic messaging framework</p>
                </div>
                <div className="panel-content">
                  <MessageMapBuilder />
                </div>
              </div>

              {/* DSPy Telemetry Preview */}
              <div className="panel-card bg-white rounded-lg border p-6">
                <div className="panel-header mb-4">
                  <h2 className="text-lg font-medium text-gray-900">DSPy Telemetry</h2>
                  <p className="text-sm text-gray-600">Program compilation and execution metrics</p>
                </div>
                <div className="panel-content">
                  <div className="telemetry-preview">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="metric-card p-3 bg-blue-50 rounded-lg">
                        <div className="text-lg font-semibold text-blue-900">3</div>
                        <div className="text-xs text-blue-700">Active Programs</div>
                      </div>
                      <div className="metric-card p-3 bg-green-50 rounded-lg">
                        <div className="text-lg font-semibold text-green-900">92%</div>
                        <div className="text-xs text-green-700">Success Rate</div>
                      </div>
                      <div className="metric-card p-3 bg-purple-50 rounded-lg">
                        <div className="text-lg font-semibold text-purple-900">847</div>
                        <div className="text-xs text-purple-700">Total Events</div>
                      </div>
                      <div className="metric-card p-3 bg-yellow-50 rounded-lg">
                        <div className="text-lg font-semibold text-yellow-900">2.3s</div>
                        <div className="text-xs text-yellow-700">Avg Compile Time</div>
                      </div>
                    </div>
                    
                    <div className="mt-4 text-center">
                      <button className="text-sm text-blue-600 hover:text-blue-800 underline">
                        View Full Telemetry Dashboard
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* System Status Footer */}
        <div className="system-status bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-700">Constitutional System: Active</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-700">DSPy Telemetry: Enabled</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-700">Chain-of-Verification: Ready</span>
              </div>
            </div>
            <div className="text-xs text-gray-500">
              Last updated: {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}