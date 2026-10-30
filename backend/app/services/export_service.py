import csv
import io
import html
from typing import List
import sys
from pathlib import Path

# Add ai-engine to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "ai-engine"))
from schemas import ComparisonResult, ChangeRecord

def generate_csv_report(result: ComparisonResult) -> str:
    """Generate CSV report of changes."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Change ID",
        "Change Type",
        "Priority",
        "Category",
        "Old Source",
        "New Source",
        "Similarity",
        "Rule Flags",
        "Priority Reasons",
        "Explanation",
        "Implication",
        "Old Text",
        "New Text"
    ])

    for chg in result.changes:
        rule_flags_str = "; ".join([f"{f.rule_id}: {f.description}" for f in chg.rule_flags])
        priority_reasons_str = "; ".join(chg.priority_reasons)
        writer.writerow([
            chg.change_id,
            chg.change_type,
            chg.priority,
            chg.category,
            chg.old_source or "",
            chg.new_source or "",
            chg.similarity if chg.similarity is not None else "",
            rule_flags_str,
            priority_reasons_str,
            chg.explanation,
            chg.implication,
            chg.old_text,
            chg.new_text
        ])

    return output.getvalue()

def generate_html_report(result: ComparisonResult) -> str:
    """Generate a clean, standalone, responsive HTML report."""
    summary = result.summary
    changes_html = []

    for c in result.changes:
        if c.change_type == "unchanged":
            continue

        priority_class = {
            "critical": "badge-critical",
            "high": "badge-high",
            "medium": "badge-medium",
            "low": "badge-low"
        }.get(c.priority, "badge-low")

        type_class = {
            "added": "badge-added",
            "removed": "badge-removed",
            "modified": "badge-modified"
        }.get(c.change_type, "badge-modified")

        flags_html = "".join([
            f"<li class='flag-item'><strong>{html.escape(f.category)}:</strong> {html.escape(f.description)}</li>"
            for f in c.rule_flags
        ]) or "<li class='flag-empty'>No deterministic rule flags triggered.</li>"

        reasons_html = "".join([
            f"<li>{html.escape(r)}</li>" for r in c.priority_reasons
        ]) or "<li>Standard review criteria.</li>"

        changes_html.append(f"""
        <div class="change-card">
            <div class="change-header">
                <div class="change-meta">
                    <span class="change-id">{html.escape(c.change_id)}</span>
                    <span class="badge {type_class}">{html.escape(c.change_type.upper())}</span>
                    <span class="badge {priority_class}">PRIORITY: {html.escape(c.priority.upper())}</span>
                    <span class="category-tag">{html.escape(c.category)}</span>
                </div>
                <div class="sources">
                    <span><strong>Old:</strong> {html.escape(c.old_source or 'None')}</span> | 
                    <span><strong>New:</strong> {html.escape(c.new_source or 'None')}</span>
                </div>
            </div>

            <div class="diff-grid">
                <div class="diff-col old-col">
                    <div class="diff-label">Previous Version</div>
                    <div class="diff-body">{html.escape(c.old_text) or '<em class="text-muted">(none)</em>'}</div>
                </div>
                <div class="diff-col new-col">
                    <div class="diff-label">New Version</div>
                    <div class="diff-body">{html.escape(c.new_text) or '<em class="text-muted">(none)</em>'}</div>
                </div>
            </div>

            <div class="analysis-section">
                <div class="analysis-box">
                    <h4>Explanation</h4>
                    <p>{html.escape(c.explanation)}</p>
                </div>
                <div class="analysis-box">
                    <h4>Operational Implication</h4>
                    <p>{html.escape(c.implication)}</p>
                </div>
            </div>

            <div class="rules-section">
                <div class="reasons-box">
                    <strong>Priority Rationale:</strong>
                    <ul>{reasons_html}</ul>
                </div>
                <div class="flags-box">
                    <strong>Rule Signals:</strong>
                    <ul>{flags_html}</ul>
                </div>
            </div>
        </div>
        """)

    body_content = "\n".join(changes_html)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocuDiff AI Analysis Report - {html.escape(summary.comparison_id)}</title>
    <style>
        :root {{
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --border: #e2e8f0;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --primary: #2563eb;
            --danger: #ef4444;
            --success: #10b981;
            --warning: #f59e0b;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 30px 20px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1080px;
            margin: 0 auto;
        }}
        .header {{
            background: var(--card-bg);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid var(--border);
            margin-bottom: 24px;
        }}
        .title {{
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 8px 0;
            color: var(--primary);
        }}
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 16px;
            margin-top: 20px;
        }}
        .stat-card {{
            background: var(--bg);
            padding: 16px;
            border-radius: 8px;
            border: 1px solid var(--border);
            text-align: center;
        }}
        .stat-value {{
            font-size: 26px;
            font-weight: 700;
        }}
        .stat-label {{
            font-size: 13px;
            color: var(--text-muted);
            text-transform: uppercase;
        }}
        .change-card {{
            background: var(--card-bg);
            border-radius: 12px;
            border: 1px solid var(--border);
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .change-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 16px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 12px;
        }}
        .change-id {{
            font-weight: 700;
            color: var(--text-muted);
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-modified {{ background: #eff6ff; color: #1d4ed8; }}
        .badge-added {{ background: #ecfdf5; color: #047857; }}
        .badge-removed {{ background: #fef2f2; color: #b91c1c; }}
        .badge-critical {{ background: #7f1d1d; color: #fff; }}
        .badge-high {{ background: #fee2e2; color: #dc2626; }}
        .badge-medium {{ background: #fef3c7; color: #b45309; }}
        .badge-low {{ background: #f1f5f9; color: #475569; }}
        .category-tag {{
            background: #f1f5f9;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            color: #334155;
        }}
        .sources {{ font-size: 13px; color: var(--text-muted); }}
        .diff-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
        }}
        .diff-col {{
            background: #f8fafc;
            border-radius: 8px;
            border: 1px solid var(--border);
            padding: 12px;
        }}
        .diff-label {{
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        .diff-body {{
            font-size: 14px;
            white-space: pre-wrap;
        }}
        .old-col {{ border-left: 4px solid #ef4444; }}
        .new-col {{ border-left: 4px solid #10b981; }}
        .analysis-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            background: #f1f5f9;
            padding: 14px;
            border-radius: 8px;
            margin-bottom: 12px;
        }}
        .analysis-box h4 {{
            margin: 0 0 4px 0;
            font-size: 13px;
            color: var(--text-muted);
            text-transform: uppercase;
        }}
        .analysis-box p {{
            margin: 0;
            font-size: 14px;
        }}
        .rules-section {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            font-size: 13px;
            color: var(--text-muted);
        }}
        .rules-section ul {{
            margin: 4px 0 0 0;
            padding-left: 18px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">DocuDiff AI — Document Intelligence Report</h1>
            <div>
                <strong>Comparison ID:</strong> {html.escape(summary.comparison_id)} | 
                <strong>Original:</strong> {html.escape(summary.old_filename)} | 
                <strong>Modified:</strong> {html.escape(summary.new_filename)} | 
                <strong>Generated:</strong> {html.escape(summary.created_at)}
            </div>
            <div>
                <strong>Model / Analyzer:</strong> {html.escape(summary.model)} | 
                <strong>Duration:</strong> {summary.processing_duration_seconds}s |
                <strong>LangGraph:</strong> {'Enabled' if summary.langgraph_used else 'Sequential'}
            </div>
            <div class="summary-stats">
                <div class="stat-card">
                    <div class="stat-value">{summary.total_changes}</div>
                    <div class="stat-label">Total Changes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #10b981;">{summary.added}</div>
                    <div class="stat-label">Added</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #2563eb;">{summary.modified}</div>
                    <div class="stat-label">Modified</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #ef4444;">{summary.removed}</div>
                    <div class="stat-label">Removed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #dc2626;">{summary.priority_breakdown.get('high', 0) + summary.priority_breakdown.get('critical', 0)}</div>
                    <div class="stat-label">High / Critical</div>
                </div>
            </div>
        </div>

        <div class="changes-list">
            {body_content}
        </div>
    </div>
</body>
</html>
"""
    return html_template

