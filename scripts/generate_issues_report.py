#!/usr/bin/env python3
"""
Generate an HTML report summarizing the declarative roadmap issues.

Typical workflow:
 1. python scripts/export_issues_json.py --output issues.json
 2. python scripts/generate_issues_report.py --input issues.json --output issues_report.html

Sections included:
 - High‑level summary (total issues, open vs closed)
 - Milestone distribution (count + percentage)
 - Label frequency (top N, configurable)
 - Detailed issue listing grouped by milestone (sorted by issue number if present else title)

The export JSON is expected to contain a list of objects each with (at minimum):
  id (optional), title, body, labels (list[str]), milestone (nullable), hash_short, normalized_title

No external dependencies (pure stdlib) to keep CI lightweight.
"""
from __future__ import annotations

import argparse
import collections
from datetime import datetime, timezone
import html
import json
import pathlib
from typing import Any, Dict, List, Optional


def load_issues(path: pathlib.Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):  # Defensive
        raise ValueError("Export JSON must be a list of issue objects")
    return data


UNASSIGNED_MILESTONE = "(none)"


def compute_stats(issues: List[Dict[str, Any]]):
    total = len(issues)
    status_counter = collections.Counter()
    milestone_counter = collections.Counter()
    label_counter = collections.Counter()

    for issue in issues:
        labels = issue.get("labels") or []
        if any(l.lower() == "status:closed" for l in labels):
            status_counter["closed"] += 1
        else:
            status_counter["open"] += 1
        milestone = issue.get("milestone") or UNASSIGNED_MILESTONE
        milestone_counter[milestone] += 1
        for lbl in labels:
            label_counter[lbl] += 1

    # Derive percentages
    def pct(count: int) -> float:
        return (count / total * 100.0) if total else 0.0

    milestone_stats = [
        {
            "milestone": m,
            "count": c,
            "percent": pct(c),
        }
        for m, c in sorted(milestone_counter.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    ]

    return {
        "total": total,
        "open": status_counter.get("open", 0),
        "closed": status_counter.get("closed", 0),
        "milestones": milestone_stats,
        "labels": label_counter,
    }


def group_by_milestone(issues: List[Dict[str, Any]]):
    grouped: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
    for issue in issues:
        m = issue.get("milestone") or UNASSIGNED_MILESTONE
        grouped[m].append(issue)
    # Sort issues inside each milestone by numeric id if present else title
    for m, bucket in grouped.items():
        def sort_key(it: Dict[str, Any]):
            issue_id = it.get("id")
            try:
                numeric = int(issue_id) if issue_id is not None else 10**12
            except Exception:
                numeric = 10**12
            return (numeric, it.get("title", ""))
        bucket.sort(key=sort_key)
    return dict(sorted(grouped.items(), key=lambda kv: (kv[0] == UNASSIGNED_MILESTONE, kv[0].lower())))

def _inline_css() -> str:
    return (
        "body { font-family: system-ui,-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,Oxygen,Ubuntu,\"Fira Sans\",\"Droid Sans\",\"Helvetica Neue\",Arial,sans-serif; margin: 1.5rem; }"\
        " h1,h2,h3 { line-height: 1.2; }"\
        " table { border-collapse: collapse; width: 100%; margin-bottom: 1.5rem; }"\
        " th, td { border: 1px solid #ddd; padding: 6px 8px; font-size: 0.9rem; }"\
        " th { background: #f5f5f5; text-align: left; }"\
        " tbody tr:nth-child(even) { background: #fafafa; }"\
        " code { background: #f0f0f0; padding: 2px 4px; border-radius: 3px; }"\
        " .tag { display: inline-block; background:#eef; color:#224; padding:2px 6px; margin:2px 2px 2px 0; border-radius:4px; font-size:0.7rem; font-weight:500; }"\
        " .closed { background:#fee; color:#600; }"\
        " .open { background:#efe; color:#060; }"\
        " .milestone-header { margin-top: 2.5rem; }"\
        " .issue-block { border:1px solid #ddd; border-radius:6px; padding:0.6rem 0.75rem; margin:0.75rem 0; background:#fff; }"\
        " .meta { font-size:0.7rem; color:#666; margin-bottom:0.35rem; }"\
        " .status-pill { display:inline-block; padding:2px 6px; border-radius:12px; font-size:0.65rem; font-weight:600; background:#ccc; color:#222; }"\
        " .status-pill.open { background:#28a745; color:#fff; }"\
        " .status-pill.closed { background:#d73a49; color:#fff; }"\
        " .footer { margin-top:3rem; font-size:0.7rem; color:#777; }"
    )


def _esc(val: Any) -> str:  # small helper for brevity
    return html.escape(str(val))


def _section_header(text: str, level: int = 2) -> str:
    return f"<h{level}>{_esc(text)}</h{level}>"


def _render_milestone_distribution(stats: Dict[str, Any]) -> str:
    rows = [
        "<table><thead><tr><th>Milestone</th><th>Count</th><th>Percent</th></tr></thead><tbody>",
    ]
    for row in stats["milestones"]:
        rows.append(
            f"<tr><td>{_esc(row['milestone'])}</td><td>{row['count']}</td><td>{row['percent']:.1f}%</td></tr>"
        )
    rows.append("</tbody></table>")
    return _section_header("Milestone Distribution") + "".join(rows)


def _render_label_table(stats: Dict[str, Any], top_labels: int) -> str:
    label_items = stats["labels"].most_common(top_labels)
    header = _section_header(f"Top Labels (Top {len(label_items)})")
    if not label_items:
        return header + "<p><em>No labels present.</em></p>"
    parts = [
        "<table><thead><tr><th>Label</th><th>Count</th></tr></thead><tbody>",
    ]
    parts.extend(
        f"<tr><td>{_esc(label)}</td><td>{count}</td></tr>" for label, count in label_items
    )
    parts.append("</tbody></table>")
    return header + "".join(parts)


def _issue_snippet(body: str) -> str:
    body = body.strip()
    if not body:
        return ""
    snippet_text = body[:300] + ("…" if len(body) > 300 else "")
    return f"<div style='margin-top:4px; font-size:0.75rem; color:#333;'>{_esc(snippet_text)}</div>"


def _labels_html(labels: List[str]) -> str:
    if not labels:
        return ""
    return "<div>" + " ".join(
        f"<span class='tag {'closed' if l.lower()=='status:closed' else ''}'>{_esc(l)}</span>" for l in labels
    ) + "</div>"


def _render_single_issue(issue: Dict[str, Any]) -> str:
    labels = issue.get("labels") or []
    is_closed = any(l.lower() == "status:closed" for l in labels)
    status_class = "closed" if is_closed else "open"
    issue_id = issue.get("id")
    id_part = f"#{issue_id} " if issue_id is not None else ""
    snippet = _issue_snippet(issue.get("body") or "")
    return (
        "<div class='issue-block'>"
        f"<div class='meta'><span class='status-pill {status_class}'>{status_class}</span> "
        f"{id_part}<code>{_esc(issue.get('hash_short',''))}</code></div>"
        f"<strong>{_esc(issue.get('title','(no title)'))}</strong><br/>"
        f"{_labels_html(labels)}{snippet}"
        "</div>"
    )


def _render_issues_by_milestone(grouped: Dict[str, List[Dict[str, Any]]]) -> str:
    sections: List[str] = [_section_header("Issues by Milestone")]
    for milestone, bucket in grouped.items():
        sections.append(f"<h3 class='milestone-header'>{_esc(milestone)}</h3>")
        if not bucket:
            sections.append("<p><em>No issues.</em></p>")
            continue
        sections.extend(_render_single_issue(issue) for issue in bucket)
    return "".join(sections)


def render_html(issues: List[Dict[str, Any]], stats: Dict[str, Any], *, title: str, top_labels: int) -> str:
    generated_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    grouped = group_by_milestone(issues)

    # Header + summary
    summary = (
        f"<p><strong>Total:</strong> {stats['total']} | "
        f"<span class='status-pill open'>Open: {stats['open']}</span> "
        f"<span class='status-pill closed'>Closed: {stats['closed']}</span></p>"
    )

    body_sections = [
        _render_milestone_distribution(stats),
        _render_label_table(stats, top_labels),
        _render_issues_by_milestone(grouped),
        f"<div class='footer'>Generated {_esc(generated_ts)} | Declarative issue automation suite | Hash short codes help detect drift.</div>",
    ]

    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>{_esc(title)}</title><style>{_inline_css()}</style></head><body>"
        f"<h1>{_esc(title)}</h1>"
        f"{summary}"
        + "".join(body_sections)
        + "</body></html>"
    )


def parse_args(argv: Optional[List[str]] = None):
    p = argparse.ArgumentParser(description="Generate HTML report from exported issues JSON")
    p.add_argument("--input", "-i", type=pathlib.Path, default=pathlib.Path("issues.json"), help="Path to issues JSON export")
    p.add_argument("--output", "-o", type=pathlib.Path, default=pathlib.Path("issues_report.html"), help="Output HTML file path")
    p.add_argument("--title", type=str, default="Issue Roadmap Report", help="Report title")
    p.add_argument("--top-labels", type=int, default=30, help="Number of top labels to include in label frequency table")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    issues = load_issues(args.input)
    stats = compute_stats(issues)
    html_doc = render_html(issues, stats, title=args.title, top_labels=args.top_labels)
    args.output.write_text(html_doc, encoding="utf-8")
    print(f"Report written to {args.output} (issues: {stats['total']}, open: {stats['open']}, closed: {stats['closed']})")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
