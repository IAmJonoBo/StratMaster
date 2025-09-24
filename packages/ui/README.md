# StratMaster UI Components

**Status**: ✅ **COMPLETED** - Full implementation available in `apps/web/`

This package provides the core UI components for the StratMaster platform, implemented as a modern Next.js application with comprehensive features.

## ✅ Implemented Features

- **Tri-pane layout**: Sources | Debate | Graph/Boards with keyboard navigation
- **Expert Panel**: Constitutional debate system with real-time visualization  
- **Message Map Builder**: Strategic messaging framework
- **Persuasion Risk Gauge**: Ethics and compliance assessment
- **Debate Visualization**: Real-time constitutional debate process
- **Constitutional Configuration**: Expert discipline configuration
- **DSPy Telemetry**: Program compilation and execution metrics
- **Hardware Detection**: Adaptive UI based on device capabilities
- **Mobile Support**: Responsive design with read-only approvals

## Architecture

- **Framework**: Next.js 15 with React 19
- **Styling**: Tailwind CSS with custom components
- **Components**: Modular expert system components
- **State Management**: React hooks with context patterns
- **Performance**: Optimized for <2s load times

## Components Reference

### Core Components
- `ExpertPanel` - Configure and run expert evaluations
- `MessageMapBuilder` - Strategic messaging framework
- `PersuasionRiskGauge` - Risk analysis and compliance
- `DebateVisualization` - Real-time debate process
- `ConstitutionalConfig` - Expert system configuration

### Specialist Views  
- Argument Map - Logic flow visualization
- Evidence Badge - Source credibility indicators
- Assumption Heat-map - Risk assessment visualization
- Graph Explorer - Knowledge graph navigation
- Strategy Kanban - Project management boards
- Experiment Console - A/B testing interface

## Usage

The UI is fully integrated with the StratMaster API and provides a comprehensive dashboard for strategy evaluation, expert debates, and real-time collaboration.

See `apps/web/` for the complete implementation.
