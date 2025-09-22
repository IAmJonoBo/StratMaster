from pathlib import Path

from stratmaster_dsp import TelemetryRecorder, compile_research_planner


def test_compile_research_planner_emits_artifact(tmp_path: Path) -> None:
    telemetry = TelemetryRecorder()
    artifact_path = compile_research_planner(
        query="international expansion",
        output_dir=tmp_path,
        telemetry=telemetry,
    )

    assert artifact_path.exists()
    saved = artifact_path.read_text(encoding="utf-8")
    assert "international expansion".title() in saved
    assert telemetry.events
    event = telemetry.events[0]
    assert event["event_type"] == "dspy.compile"
    assert event["program"] == "research_planner"
