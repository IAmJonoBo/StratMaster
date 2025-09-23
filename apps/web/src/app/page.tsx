import { ExpertPanel } from '@/components/experts/ExpertPanel'
import { MessageMapBuilder } from '@/components/experts/MessageMapBuilder'
import { PersuasionRiskGauge } from '@/components/experts/PersuasionRiskGauge'

export default function DashboardPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Strategy Dashboard</h1>
        <p className="mt-2 text-gray-600">
          AI-powered brand strategy evaluation with expert discipline analysis
        </p>
      </div>

      <div className="tri-pane-layout">
        {/* Left Pane: Expert Panel */}
        <div className="pane">
          <div className="pane-header">
            <h2 className="text-lg font-medium">Expert Panel</h2>
          </div>
          <div className="pane-content">
            <ExpertPanel />
          </div>
        </div>

        {/* Middle Pane: Persuasion Risk & Analysis */}
        <div className="pane">
          <div className="pane-header">
            <h2 className="text-lg font-medium">Risk Analysis</h2>
          </div>
          <div className="pane-content">
            <div className="space-y-6">
              <PersuasionRiskGauge />
              <div className="border-t pt-6">
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
        </div>

        {/* Right Pane: Message Map Builder */}
        <div className="pane">
          <div className="pane-header">
            <h2 className="text-lg font-medium">Message Map</h2>
          </div>
          <div className="pane-content">
            <MessageMapBuilder />
          </div>
        </div>
      </div>
    </div>
  )
}