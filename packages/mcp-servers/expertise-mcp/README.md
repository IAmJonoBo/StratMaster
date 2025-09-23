# Expertise MCP Server

Model Context Protocol (MCP) server for expert discipline evaluation in StratMaster.

## Overview

This MCP server provides expert evaluation capabilities across multiple disciplines:
- Psychology (COM-B model, reactance detection)
- Design (NN/g heuristics, visual proof validation)
- Communication (message mapping)
- Accessibility (WCAG compliance)
- Brand Science (consistency checks)

## Tools

### `expert.evaluate`

Evaluates a strategy against specified expert disciplines.

**Input:**
- `strategy`: Object containing strategy data
- `disciplines`: Array of discipline names

**Output:**
- Array of DisciplineMemo objects with findings and scores

### `expert.vote`

Aggregates discipline memos into a weighted council vote.

**Input:**
- `strategy_id`: String identifier for the strategy
- `weights`: Object mapping discipline names to weights
- `memos`: Array of DisciplineMemo objects

**Output:**
- CouncilVote object with weighted score

## Usage

### Standalone

```bash
python main.py
```

### Docker

```bash
docker build -t expertise-mcp .
docker run expertise-mcp
```

## Configuration

Expert doctrines are loaded from `configs/experts/doctrines/` directory.
Each discipline should have its own YAML configuration file.

## Integration

This MCP server integrates with:
- FastAPI routes in `packages/api/routers/experts.py`
- LangGraph orchestration in `packages/orchestrator/`
- Expert models in `packages/api/models/experts/`