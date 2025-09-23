"""Deterministic DSPy program stubs with simple telemetry hooks."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict


class DSPyArtifact(BaseModel):
    """Serializable artifact persisted after compilation."""

    model_config = ConfigDict(extra="forbid")

    program_name: str
    version: str
    created_at: datetime
    prompt: str
    steps: list[str]
    compilation_metrics: dict[str, Any] = field(default_factory=dict)
    langfuse_trace_id: str | None = None


class LangfuseTelemetryClient(Protocol):
    """Protocol for Langfuse telemetry integration."""
    
    def trace(self, name: str, **kwargs: Any) -> Any: ...
    def generation(self, **kwargs: Any) -> Any: ...
    def score(self, **kwargs: Any) -> None: ...


@dataclass
class TelemetryRecorder:
    """Enhanced telemetry recorder with optional Langfuse integration."""

    events: list[dict[str, Any]] = field(default_factory=list)
    langfuse_client: LangfuseTelemetryClient | None = None
    current_trace: Any = None

    def __post_init__(self) -> None:
        """Try to initialize Langfuse client if available."""
        if self.langfuse_client is None:
            try:
                from langfuse import Langfuse
                # Initialize with environment variables or default config
                self.langfuse_client = Langfuse()
                logging.info("Langfuse telemetry client initialized successfully")
            except ImportError:
                logging.info("Langfuse not available, using local telemetry only")
            except Exception as e:
                logging.warning(f"Failed to initialize Langfuse client: {e}")

    def start_trace(self, name: str, **metadata: Any) -> str | None:
        """Start a new telemetry trace."""
        trace_id = None
        if self.langfuse_client:
            try:
                self.current_trace = self.langfuse_client.trace(name=name, **metadata)
                trace_id = getattr(self.current_trace, 'id', None)
                logging.debug(f"Started Langfuse trace: {trace_id}")
            except Exception as e:
                logging.warning(f"Failed to start Langfuse trace: {e}")
        
        # Always record locally as fallback
        self.record("trace.start", {"name": name, "trace_id": trace_id, **metadata})
        return trace_id

    def end_trace(self, **metadata: Any) -> None:
        """End the current telemetry trace."""
        if self.current_trace and self.langfuse_client:
            try:
                # Update trace with final metadata
                self.current_trace.update(**metadata)
                logging.debug("Ended Langfuse trace")
            except Exception as e:
                logging.warning(f"Failed to end Langfuse trace: {e}")
            finally:
                self.current_trace = None
        
        self.record("trace.end", metadata)

    def record_generation(self, name: str, input_data: Any, output_data: Any, **metadata: Any) -> None:
        """Record a generation event with input/output."""
        if self.current_trace and self.langfuse_client:
            try:
                generation = self.current_trace.generation(
                    name=name,
                    input=input_data,
                    output=output_data,
                    **metadata
                )
                logging.debug(f"Recorded Langfuse generation: {name}")
            except Exception as e:
                logging.warning(f"Failed to record Langfuse generation: {e}")
        
        # Always record locally
        self.record("generation", {
            "name": name,
            "input": input_data,
            "output": output_data,
            **metadata
        })

    def record_score(self, name: str, value: float, **metadata: Any) -> None:
        """Record a score metric."""
        if self.current_trace and self.langfuse_client:
            try:
                self.current_trace.score(name=name, value=value, **metadata)
                logging.debug(f"Recorded Langfuse score: {name}={value}")
            except Exception as e:
                logging.warning(f"Failed to record Langfuse score: {e}")
        
        # Always record locally
        self.record("score", {"name": name, "value": value, **metadata})

    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        """Record a generic telemetry event."""
        enriched = payload | {
            "event_type": event_type,
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "trace_id": getattr(self.current_trace, 'id', None) if self.current_trace else None,
        }
        self.events.append(enriched)


@dataclass
class ResearchPlanner:
    """DSPy-style planner that emits deterministic task lists."""

    program_name: str = "research_planner"
    version: str = "2024.10.01"
    prompt: str = (
        "Generate comprehensive research tasks covering market analysis, competitive intelligence, and risk assessment."
    )

    def plan(self, query: str, telemetry: TelemetryRecorder | None = None) -> list[str]:
        """Generate research plan with telemetry tracking."""
        if telemetry:
            trace_id = telemetry.start_trace(f"research_planning", query=query, program=self.program_name)
            telemetry.record_generation(
                name="plan_generation",
                input_data={"query": query, "prompt": self.prompt},
                output_data=None,  # Will be filled below
                model="research_planner_v1"
            )
        
        base = query.strip().title() or "Strategy"
        steps = [
            f"Quantify demand signals for {base}",
            f"Map competitive landscape impacting {base}",
            f"Identify regulatory or ethical risks for {base}",
            f"Analyze market timing factors for {base}",
            f"Assess technical feasibility of {base}",
        ]
        
        if telemetry:
            telemetry.record_generation(
                name="plan_generation",
                input_data={"query": query, "prompt": self.prompt},
                output_data={"steps": steps, "step_count": len(steps)},
                model="research_planner_v1"
            )
            telemetry.record_score("plan_completeness", float(len(steps)) / 5.0)
            telemetry.end_trace(success=True, step_count=len(steps))
        
        return steps

    def compile(self, query: str, telemetry: TelemetryRecorder | None = None) -> DSPyArtifact:
        steps = self.plan(query, telemetry)
        metrics = {
            "query_length": len(query),
            "step_count": len(steps),
            "compilation_time": datetime.now(tz=UTC).isoformat(),
        }
        
        return DSPyArtifact(
            program_name=self.program_name,
            version=self.version,
            created_at=datetime.now(tz=UTC),
            prompt=self.prompt,
            steps=steps,
            compilation_metrics=metrics,
            langfuse_trace_id=getattr(telemetry.current_trace, 'id', None) if telemetry and telemetry.current_trace else None
        )

    def save(self, artifact: DSPyArtifact, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = artifact.model_dump(mode="json")
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def load(self, path: Path) -> DSPyArtifact:
        data = json.loads(path.read_text(encoding="utf-8"))
        return DSPyArtifact.model_validate(data)


@dataclass
class SynthesisPlanner:
    """DSPy-style synthesiser that creates coherent insights from research."""

    program_name: str = "synthesis_planner"
    version: str = "2024.10.01"
    prompt: str = (
        "Synthesize research findings into coherent strategic insights with clear evidence chains."
    )

    def synthesize(self, research_findings: list[str], telemetry: TelemetryRecorder | None = None) -> list[str]:
        """Synthesize research findings into strategic insights."""
        if telemetry:
            trace_id = telemetry.start_trace(f"synthesis_planning", 
                                           findings_count=len(research_findings), 
                                           program=self.program_name)
            telemetry.record_generation(
                name="synthesis_generation",
                input_data={"findings": research_findings, "prompt": self.prompt},
                output_data=None,
                model="synthesis_planner_v1"
            )
        
        # Generate synthetic insights based on findings
        insights = []
        for i, finding in enumerate(research_findings, 1):
            insight = f"Strategic insight {i}: {finding} suggests market opportunity"
            insights.append(insight)
        
        # Add cross-cutting insights
        if len(research_findings) > 1:
            insights.append("Cross-analysis reveals convergent market trends")
            insights.append("Risk-opportunity matrix indicates balanced approach needed")
        
        if telemetry:
            telemetry.record_generation(
                name="synthesis_generation",
                input_data={"findings": research_findings, "prompt": self.prompt},
                output_data={"insights": insights, "insight_count": len(insights)},
                model="synthesis_planner_v1"
            )
            telemetry.record_score("synthesis_coherence", 0.85)
            telemetry.record_score("evidence_coverage", float(len(insights)) / max(len(research_findings), 1))
            telemetry.end_trace(success=True, insight_count=len(insights))
        
        return insights

    def compile(self, research_findings: list[str], telemetry: TelemetryRecorder | None = None) -> DSPyArtifact:
        insights = self.synthesize(research_findings, telemetry)
        metrics = {
            "input_finding_count": len(research_findings),
            "output_insight_count": len(insights),
            "synthesis_ratio": len(insights) / max(len(research_findings), 1),
            "compilation_time": datetime.now(tz=UTC).isoformat(),
        }
        
        return DSPyArtifact(
            program_name=self.program_name,
            version=self.version,
            created_at=datetime.now(tz=UTC),
            prompt=self.prompt,
            steps=insights,
            compilation_metrics=metrics,
            langfuse_trace_id=getattr(telemetry.current_trace, 'id', None) if telemetry and telemetry.current_trace else None
        )


@dataclass
class StrategyPlanner:
    """DSPy-style strategist that creates actionable recommendations."""

    program_name: str = "strategy_planner"
    version: str = "2024.10.01"
    prompt: str = (
        "Transform insights into actionable strategic recommendations with clear success metrics."
    )

    def strategize(self, insights: list[str], telemetry: TelemetryRecorder | None = None) -> list[str]:
        """Generate strategic recommendations from insights."""
        if telemetry:
            trace_id = telemetry.start_trace(f"strategy_planning", 
                                           insights_count=len(insights), 
                                           program=self.program_name)
            telemetry.record_generation(
                name="strategy_generation",
                input_data={"insights": insights, "prompt": self.prompt},
                output_data=None,
                model="strategy_planner_v1"
            )
        
        recommendations = []
        for i, insight in enumerate(insights, 1):
            rec = f"Strategic recommendation {i}: Implement initiative based on {insight[:50]}..."
            recommendations.append(rec)
        
        # Add meta-strategic recommendations
        recommendations.extend([
            "Establish success metrics and KPI tracking",
            "Create risk mitigation protocols",
            "Design iterative feedback loops for strategy refinement"
        ])
        
        if telemetry:
            telemetry.record_generation(
                name="strategy_generation",
                input_data={"insights": insights, "prompt": self.prompt},
                output_data={"recommendations": recommendations, "rec_count": len(recommendations)},
                model="strategy_planner_v1"
            )
            telemetry.record_score("strategy_actionability", 0.90)
            telemetry.record_score("risk_coverage", 0.75)
            telemetry.end_trace(success=True, recommendation_count=len(recommendations))
        
        return recommendations

    def compile(self, insights: list[str], telemetry: TelemetryRecorder | None = None) -> DSPyArtifact:
        recommendations = self.strategize(insights, telemetry)
        metrics = {
            "input_insight_count": len(insights),
            "output_recommendation_count": len(recommendations),
            "strategy_depth": len(recommendations) / max(len(insights), 1),
            "compilation_time": datetime.now(tz=UTC).isoformat(),
        }
        
        return DSPyArtifact(
            program_name=self.program_name,
            version=self.version,
            created_at=datetime.now(tz=UTC),
            prompt=self.prompt,
            steps=recommendations,
            compilation_metrics=metrics,
            langfuse_trace_id=getattr(telemetry.current_trace, 'id', None) if telemetry and telemetry.current_trace else None
        )


def compile_research_planner(
    query: str,
    output_dir: Path | None = None,
    telemetry: TelemetryRecorder | None = None,
) -> Path:
    """Compile the research planner and persist its artifact."""
    if telemetry is None:
        telemetry = TelemetryRecorder()
    
    planner = ResearchPlanner()
    artifact = planner.compile(query, telemetry)
    target_dir = output_dir or Path("packages/dsp/dspy_programs")
    artifact_path = target_dir / f"{planner.program_name}-{planner.version}.json"
    planner.save(artifact, artifact_path)
    
    if telemetry is not None:
        telemetry.record(
            "dspy.compile",
            {
                "program": planner.program_name,
                "version": planner.version,
                "artifact_path": str(artifact_path),
                "query": query,
                "metrics": artifact.compilation_metrics,
            },
        )
    return artifact_path


def compile_synthesis_planner(
    research_findings: list[str],
    output_dir: Path | None = None,
    telemetry: TelemetryRecorder | None = None,
) -> Path:
    """Compile the synthesis planner and persist its artifact."""
    if telemetry is None:
        telemetry = TelemetryRecorder()
    
    planner = SynthesisPlanner()
    artifact = planner.compile(research_findings, telemetry)
    target_dir = output_dir or Path("packages/dsp/dspy_programs")
    artifact_path = target_dir / f"{planner.program_name}-{planner.version}.json"
    planner.save(artifact, artifact_path)
    
    if telemetry is not None:
        telemetry.record(
            "dspy.compile",
            {
                "program": planner.program_name,
                "version": planner.version,
                "artifact_path": str(artifact_path),
                "findings_count": len(research_findings),
                "metrics": artifact.compilation_metrics,
            },
        )
    return artifact_path


def compile_strategy_planner(
    insights: list[str],
    output_dir: Path | None = None,
    telemetry: TelemetryRecorder | None = None,
) -> Path:
    """Compile the strategy planner and persist its artifact."""
    if telemetry is None:
        telemetry = TelemetryRecorder()
    
    planner = StrategyPlanner()
    artifact = planner.compile(insights, telemetry)
    target_dir = output_dir or Path("packages/dsp/dspy_programs")
    artifact_path = target_dir / f"{planner.program_name}-{planner.version}.json"
    planner.save(artifact, artifact_path)
    
    if telemetry is not None:
        telemetry.record(
            "dspy.compile",
            {
                "program": planner.program_name,
                "version": planner.version,
                "artifact_path": str(artifact_path),
                "insights_count": len(insights),
                "metrics": artifact.compilation_metrics,
            },
        )
    return artifact_path


def compile_full_pipeline(
    query: str,
    output_dir: Path | None = None,
    telemetry: TelemetryRecorder | None = None,
) -> dict[str, Path]:
    """Compile the full DSPy pipeline: Research -> Synthesis -> Strategy."""
    if telemetry is None:
        telemetry = TelemetryRecorder()
    
    # Start pipeline trace
    pipeline_trace_id = telemetry.start_trace("dspy_pipeline_compilation", query=query)
    
    try:
        # Step 1: Research Planning
        research_planner = ResearchPlanner()
        research_findings = research_planner.plan(query, telemetry)
        research_path = compile_research_planner(query, output_dir, telemetry)
        
        # Step 2: Synthesis Planning
        synthesis_planner = SynthesisPlanner()
        insights = synthesis_planner.synthesize(research_findings, telemetry)
        synthesis_path = compile_synthesis_planner(research_findings, output_dir, telemetry)
        
        # Step 3: Strategy Planning
        strategy_planner = StrategyPlanner()
        recommendations = strategy_planner.strategize(insights, telemetry)
        strategy_path = compile_strategy_planner(insights, output_dir, telemetry)
        
        result = {
            "research": research_path,
            "synthesis": synthesis_path,
            "strategy": strategy_path,
        }
        
        # Record pipeline success
        telemetry.record_score("pipeline_completeness", 1.0)
        telemetry.end_trace(success=True, components=3, query=query)
        
        return result
        
    except Exception as e:
        telemetry.record("pipeline_error", {"error": str(e), "query": query})
        telemetry.end_trace(success=False, error=str(e))
        raise
