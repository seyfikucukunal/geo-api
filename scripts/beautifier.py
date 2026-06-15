#!/usr/bin/env python3
"""
GEO Report Premium Beautifier
AI-syah.nl

Usage:
    python beautifier.py <data.json> [--output report.pdf] [--client-logo logo.png]
"""

import json
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime


# ─── BRAND CONFIG ────────────────────────────────────────────────────────────
BRAND = {
    "name": "AI-syah.nl",
    "tagline": "Generative Engine Optimization",
    "website": "ai-syah.nl",
    "phone": "",
    "contact_name": "AI-syah.nl",
    "colors": {
        "primary":             "#22d3ee",
        "primary_bright":      "#67e8f9",
        "secondary":           "#22d3ee",
        "bg_deep":             "#000000",
        "bg_dark":             "#000000",
        "bg_card":             "#111111",
        "bg_card_alt":         "#18181b",
        "border":              "#27272a",
        "text_primary":        "#ffffff",
        "text_secondary":      "#a1a1aa",
        "text_accent":         "#22d3ee",
        "critical":            "#ef4444",
        "high":                "#f97316",
        "medium":              "#eab308",
        "low":                 "#3b82f6",
        "score_excellent":     "#22c55e",
        "score_good":          "#3b82f6",
        "score_moderate":      "#eab308",
        "score_below":         "#f97316",
        "score_critical":      "#ef4444",
    }
}


def apply_brand_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    for key, value in cfg.items():
        if key == "colors" and isinstance(value, dict):
            BRAND["colors"].update(value)
        else:
            BRAND[key] = value
    print(f"  Brand: {BRAND['name']} (white-labeled via {os.path.basename(config_path)})")


def score_color(score):
    c = BRAND["colors"]
    if score >= 85: return c["score_excellent"]
    if score >= 70: return c["score_good"]
    if score >= 55: return c["score_moderate"]
    if score >= 40: return c["score_below"]
    return c["score_critical"]


def score_label(score):
    if score >= 85: return "EXCELLENT"
    if score >= 70: return "GOOD"
    if score >= 55: return "MODERATE"
    if score >= 40: return "DEVELOPING"
    return "CRITICAL"


def severity_color(severity):
    c = BRAND["colors"]
    s = severity.upper()
    if s == "CRITICAL": return c["critical"]
    if s == "HIGH":     return c["high"]
    if s == "MEDIUM":   return c["medium"]
    return c["low"]


def gauge_svg(score, size=160):
    color = score_color(score)
    cx, cy, r = size // 2, size // 2, (size // 2) - 14
    circ = 2 * 3.14159 * r
    arc_len = circ * 0.75
    filled = arc_len * (score / 100)
    gap = circ - arc_len
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
      <circle cx="{cx}" cy="{cy}" r="{r}"
        fill="none" stroke="#27272a" stroke-width="10"
        stroke-dasharray="{arc_len:.1f} {gap:.1f}"
        stroke-dashoffset="{-gap/2 - circ*0.125:.1f}"
        stroke-linecap="round"/>
      <circle cx="{cx}" cy="{cy}" r="{r}"
        fill="none" stroke="{color}" stroke-width="10"
        stroke-dasharray="{filled:.1f} {circ - filled:.1f}"
        stroke-dashoffset="{-gap/2 - circ*0.125:.1f}"
        stroke-linecap="round"/>
      <text x="{cx}" y="{cy - 6}" text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="{size // 4}" fill="{color}" font-weight="bold">{score}</text>
      <text x="{cx}" y="{cy + 14}" text-anchor="middle"
        font-family="Arial, sans-serif" font-size="11"
        fill="#a1a1aa" letter-spacing="1">/ 100</text>
    </svg>"""


def mini_gauge_svg(score, size=72):
    color = score_color(score)
    cx, cy, r = size // 2, size // 2, (size // 2) - 8
    circ = 2 * 3.14159 * r
    arc_len = circ * 0.75
    filled = arc_len * (score / 100)
    gap = circ - arc_len
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
      <circle cx="{cx}" cy="{cy}" r="{r}"
        fill="none" stroke="#27272a" stroke-width="6"
        stroke-dasharray="{arc_len:.1f} {gap:.1f}"
        stroke-dashoffset="{-gap/2 - circ*0.125:.1f}"
        stroke-linecap="round"/>
      <circle cx="{cx}" cy="{cy}" r="{r}"
        fill="none" stroke="{color}" stroke-width="6"
        stroke-dasharray="{filled:.1f} {circ - filled:.1f}"
        stroke-dashoffset="{-gap/2 - circ*0.125:.1f}"
        stroke-linecap="round"/>
      <text x="{cx}" y="{cy + 5}" text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="13" fill="{color}" font-weight="bold">{score}</text>
    </svg>"""


def bar_chart_svg(dimensions, width=520, height=140):
    colors = BRAND["colors"]
    bars = ""
    label_w = 180
    bar_area = width - label_w - 60
    row_h = height // len(dimensions)

    for i, dim in enumerate(dimensions):
        y = i * row_h + 4
        score = dim.get("score", 0)
        bar_w = int(bar_area * score / 100)
        col = score_color(score)
        bars += f"""
        <text x="0" y="{y + row_h//2 + 4}" font-family="Arial, sans-serif"
          font-size="10" fill="#a1a1aa">{dim['name'][:26]}</text>
        <rect x="{label_w}" y="{y + 4}" width="{bar_w}" height="{row_h - 10}"
          fill="{col}" rx="3" opacity="0.85"/>
        <text x="{label_w + bar_w + 6}" y="{y + row_h//2 + 4}"
          font-family="Arial, sans-serif" font-size="10" fill="{col}"
          font-weight="bold">{score}</text>"""

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
      {bars}
    </svg>"""


def platform_badge(name, score):
    col = score_color(score)
    label = score_label(score)
    return f"""
    <div class="platform-badge" style="border-color:{col}30">
      <div class="platform-score" style="color:{col}">{score}</div>
      <div class="platform-name">{name}</div>
      <div class="platform-label" style="color:{col};background:{col}15;border:1px solid {col}30">{label}</div>
    </div>"""


def finding_card(finding):
    sev = finding.get("severity", "LOW").upper()
    col = severity_color(sev)
    title = finding.get("title", "")
    body = finding.get("description", "")
    return f"""
    <div class="finding-card" style="border-left-color:{col}">
      <div class="finding-header">
        <span class="severity-badge" style="background:{col}20;color:{col};border:1px solid {col}40">{sev}</span>
        <span class="finding-title">{title}</span>
      </div>
      <p class="finding-body">{body}</p>
    </div>"""


def action_item(num, item, timeframe_color):
    title = item.get("title", "") if isinstance(item, dict) else str(item)
    desc = item.get("description", "") if isinstance(item, dict) else ""
    time_est = item.get("time_estimate", "") if isinstance(item, dict) else ""
    time_html = f'<span class="action-time">{time_est}</span>' if time_est else ""
    return f"""
    <div class="action-item">
      <div class="action-num" style="background:{timeframe_color}20;color:{timeframe_color};border:1px solid {timeframe_color}40">{num}</div>
      <div class="action-content">
        <div class="action-title">{title}{time_html}</div>
        <div class="action-desc">{desc}</div>
      </div>
    </div>"""


def crawler_row(crawler):
    status = crawler.get("status", "Unknown")
    if "Allowed" in status:
        status_color = "#22c55e"
    elif "Delay" in status or "Blocked" in status or "Disallowed" in status:
        status_color = "#ef4444"
    else:
        status_color = "#eab308"  # amber for "Not Mentioned" — warning, not error
    dot = f'<span style="color:{status_color}">●</span>'
    return f"""
    <tr>
      <td>{crawler.get('name','')}</td>
      <td style="color:#a1a1aa">{crawler.get('platform','')}</td>
      <td>{dot} {status}</td>
      <td style="color:#a1a1aa;font-size:11px">{crawler.get('recommendation','')}</td>
    </tr>"""


def generate_html(data: dict, logo_path: str = None) -> str:
    c = BRAND["colors"]
    b = BRAND

    company     = data.get("company_name", "")
    url         = data.get("url", "")
    audit_date  = data.get("audit_date", datetime.now().strftime("%B %d, %Y"))
    overall     = data.get("overall_score", 0)
    tagline     = data.get("company_tagline", "")
    stats       = data.get("stats", [])
    summary     = data.get("executive_summary", "")
    dimensions  = data.get("dimensions", [])
    platforms   = data.get("platforms", [])
    crawlers    = data.get("crawlers", [])
    findings    = data.get("findings", [])
    quick_wins  = data.get("action_plan", {}).get("quick_wins", [])
    medium_term = data.get("action_plan", {}).get("medium_term", [])
    strategic   = data.get("action_plan", {}).get("strategic", [])
    methodology = data.get("methodology", "")

    overall_color = score_color(overall)
    overall_label = score_label(overall)

    if logo_path and os.path.exists(logo_path):
        import base64
        ext = Path(logo_path).suffix.lower().replace(".", "")
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/{ext};base64,{logo_b64}" class="client-logo" alt="{company} logo">'
    else:
        logo_html = f'<div class="logo-text">{company}</div>'

    stats_html = ""
    for s in stats:
        stats_html += f'<div class="stat-badge"><span class="stat-val">{s["value"]}</span><span class="stat-lbl">{s["label"]}</span></div>'

    dim_cards_html = ""
    for dim in dimensions:
        mg = mini_gauge_svg(dim.get("score", 0), 68)
        wt = dim.get("weight", "")
        ws = dim.get("weighted_score", "")
        ws_html = f'<div class="dim-weighted">{ws} pts</div>' if ws else ""
        dim_cards_html += f"""
        <div class="dim-card">
          <div class="dim-gauge">{mg}</div>
          <div class="dim-info">
            <div class="dim-name">{dim.get('name','')}</div>
            <div class="dim-sub">{dim.get('description','')}</div>
            <div class="dim-meta">{wt} weight {ws_html}</div>
          </div>
        </div>"""

    chart_html = bar_chart_svg(dimensions) if dimensions else ""
    platforms_html = "".join(platform_badge(p.get("name",""), p.get("score",0)) for p in platforms)
    crawler_rows_html = "".join(crawler_row(cr) for cr in crawlers)
    findings_html = "".join(finding_card(f) for f in findings)

    finding_counts = {
        "CRITICAL": sum(1 for f in findings if f.get("severity","").upper()=="CRITICAL"),
        "HIGH":     sum(1 for f in findings if f.get("severity","").upper()=="HIGH"),
        "MEDIUM":   sum(1 for f in findings if f.get("severity","").upper()=="MEDIUM"),
        "LOW":      sum(1 for f in findings if f.get("severity","").upper()=="LOW"),
    }
    finding_summary = " · ".join(
        f'<span style="color:{severity_color(k)}">{v} {k}</span>'
        for k, v in finding_counts.items() if v > 0
    )

    qw_html  = "".join(action_item(i+1, it, c["secondary"]) for i, it in enumerate(quick_wins))
    mt_html  = "".join(action_item(i+1, it, c["primary"]) for i, it in enumerate(medium_term))
    str_html = "".join(action_item(i+1, it, "#9B59B6") for i, it in enumerate(strategic))

    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<title>GEO Rapport — {company}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --cyan:    {c['primary']};
    --bg:      {c['bg_dark']};
    --card:    {c['bg_card']};
    --card2:   {c['bg_card_alt']};
    --border:  {c['border']};
    --text:    {c['text_primary']};
    --muted:   {c['text_secondary']};
  }}
  html {{ font-size: 13px; }}
  body {{
    font-family: Arial, Helvetica, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
  }}
  .page {{ width: 794px; margin: 0 auto; }}

  /* COVER */
  .cover {{
    min-height: 1123px;
    background: linear-gradient(160deg, #000000 0%, #0a0a0f 50%, #000000 100%);
    display: flex; flex-direction: column;
    padding: 0; position: relative; overflow: hidden;
    page-break-after: always;
  }}
  .cover-line {{
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, transparent, {c['primary']}, transparent);
  }}
  .cover-header {{
    padding: 36px 52px 0;
    display: flex; justify-content: space-between; align-items: center;
  }}
  .cover-brand-name {{
    font-size: 13px; letter-spacing: 3px; text-transform: uppercase;
    color: var(--cyan); font-weight: bold;
  }}
  .cover-brand-tag {{
    font-size: 10px; letter-spacing: 1px; color: var(--muted);
    text-transform: uppercase; margin-top: 2px;
  }}
  .cover-confidential {{
    font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
    color: var(--muted); border: 1px solid var(--border); padding: 4px 10px;
  }}
  .cover-divider {{
    margin: 32px 52px; height: 1px;
    background: linear-gradient(90deg, var(--cyan), transparent);
  }}
  .cover-body {{
    flex: 1; display: flex; flex-direction: column; padding: 0 52px;
  }}
  .cover-eyebrow {{
    font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
    color: var(--muted); margin-bottom: 14px;
  }}
  .cover-title {{
    font-size: 48px; line-height: 1.08; color: var(--text);
    margin-bottom: 6px; font-weight: bold;
  }}
  .cover-title em {{ color: var(--cyan); font-style: normal; }}
  .cover-url {{ font-size: 13px; color: var(--muted); margin-bottom: 40px; }}
  .cover-logo-block {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 24px 28px;
    display: inline-flex; align-items: center; gap: 20px;
    margin-bottom: 36px; align-self: flex-start;
  }}
  .client-logo {{ max-height: 52px; max-width: 200px; object-fit: contain; }}
  .logo-text {{ font-size: 22px; color: var(--text); font-weight: bold; }}
  .cover-logo-meta {{ display: flex; flex-direction: column; gap: 4px; }}
  .cover-logo-company {{ font-size: 16px; font-weight: 700; color: var(--text) !important; }}
  .cover-logo-url {{ font-size: 11px; color: var(--muted) !important; }}
  .cover-stats {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 36px; }}
  .stat-badge {{
    background: var(--card); border: 1px solid var(--border);
    border-bottom: 2px solid var(--cyan);
    border-radius: 8px; padding: 10px 16px;
    display: flex; flex-direction: column; align-items: center; gap: 2px; min-width: 90px;
  }}
  .stat-val {{ font-size: 18px; color: var(--cyan); font-weight: bold; }}
  .stat-lbl {{ font-size: 9px; color: var(--muted); letter-spacing: 1px; text-transform: uppercase; }}
  .cover-score-row {{
    display: flex; align-items: center; gap: 32px;
    margin-top: auto; padding-bottom: 40px;
  }}
  .cover-score-label {{
    font-size: 10px; letter-spacing: 3px; text-transform: uppercase;
    color: var(--muted); margin-bottom: 10px;
  }}
  .cover-score-badge {{
    display: inline-block; font-size: 13px; letter-spacing: 2px;
    text-transform: uppercase; font-weight: 700;
    padding: 5px 16px; border-radius: 4px; margin-bottom: 14px;
  }}
  .cover-score-verdict {{
    font-size: 12px; color: var(--muted); line-height: 1.5; max-width: 340px;
  }}
  .cover-footer {{
    padding: 20px 52px;
    border-top: 1px solid var(--border);
    display: flex; justify-content: space-between; align-items: center;
  }}
  .cover-footer-name {{ font-size: 11px; color: var(--text); font-weight: 500; }}
  .cover-footer-contact {{ font-size: 10px; color: var(--muted); }}
  .cover-footer-date {{ font-size: 10px; color: var(--muted); }}

  /* CONTENT PAGES */
  .content-page {{
    padding: 48px 52px; min-height: 1123px;
    page-break-after: always; position: relative;
    background: var(--bg);
  }}
  .content-page::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--cyan) 0%, transparent 60%);
  }}
  .page-label {{
    font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
    color: var(--muted); margin-bottom: 8px;
  }}
  /* Section titles: wrap second/key word in <em> for cyan accent */
  .section-title {{
    font-size: 28px; color: var(--text); margin-bottom: 6px; font-weight: bold;
  }}
  .section-title em {{ color: var(--cyan); font-style: normal; }}
  .section-sub {{ font-size: 12px; color: var(--muted); margin-bottom: 28px; }}
  .section-divider {{ height: 1px; background: var(--border); margin: 28px 0; }}

  /* EXEC SUMMARY */
  .exec-summary {{
    background: var(--card); border: 1px solid var(--border);
    border-left: 3px solid var(--cyan); border-radius: 8px;
    padding: 24px 28px; font-size: 13px; line-height: 1.75;
    color: var(--text); margin-bottom: 28px;
  }}

  /* OVERALL ROW */
  .overall-row {{
    background: var(--card2); border: 1px solid {overall_color}40;
    border-radius: 8px; padding: 16px 24px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 20px;
  }}
  .overall-row-label {{ font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); }}
  .overall-row-score {{ font-size: 28px; color: {overall_color}; font-weight: bold; }}
  .overall-row-verdict {{
    font-size: 11px; letter-spacing: 2px; text-transform: uppercase;
    color: {overall_color}; padding: 4px 12px;
    background: {overall_color}18; border: 1px solid {overall_color}40; border-radius: 4px;
  }}

  /* DIMENSIONS */
  .dim-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }}
  .dim-card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 8px; padding: 14px 16px;
    display: flex; align-items: center; gap: 14px;
  }}
  .dim-gauge {{ flex-shrink: 0; }}
  .dim-name {{ font-size: 12px; font-weight: 600; color: var(--text); margin-bottom: 2px; }}
  .dim-sub {{ font-size: 10px; color: var(--muted); margin-bottom: 4px; line-height: 1.4; }}
  .dim-meta {{ font-size: 10px; color: var(--muted); }}
  .dim-weighted {{ font-size: 10px; color: var(--cyan); }}

  .platform-grid {{
    display: grid; grid-template-columns: repeat(5, 1fr);
    gap: 12px; margin-bottom: 28px;
  }}
  .platform-badge {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px 16px;
    text-align: center;
  }}
  .platform-score {{ font-size: 28px; font-weight: bold; margin-bottom: 4px; }}
  .platform-name {{ font-size: 10px; color: var(--muted); margin-bottom: 6px; }}
  .platform-label {{
    display: inline-block; font-size: 9px; letter-spacing: 1px;
    text-transform: uppercase; font-weight: 600;
    padding: 2px 8px; border-radius: 3px;
  }}

  /* CRAWLER TABLE */
  .crawler-table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
  .crawler-table th {{
    background: var(--card2); color: var(--muted);
    font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
    padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--border);
  }}
  .crawler-table td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); color: var(--text); }}

  /* FINDINGS */
  .finding-summary {{ font-size: 11px; color: var(--muted); margin-bottom: 16px; }}
  .finding-card {{
    border-left: 3px solid; background: var(--card);
    border-top: 1px solid var(--border); border-right: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    border-radius: 0 6px 6px 0; padding: 14px 16px; margin-bottom: 10px;
  }}
  .finding-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }}
  .severity-badge {{
    font-size: 9px; letter-spacing: 1.5px; font-weight: 700;
    padding: 2px 8px; border-radius: 3px; text-transform: uppercase; flex-shrink: 0;
  }}
  .finding-title {{ font-size: 12px; font-weight: 600; color: var(--text); }}
  .finding-body {{ font-size: 11px; color: var(--muted); line-height: 1.6; }}

  /* ACTION PLAN */
  .action-tier {{ margin-bottom: 28px; }}
  .tier-header {{
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;
  }}
  .tier-label {{ font-size: 9px; letter-spacing: 3px; text-transform: uppercase; color: var(--muted); }}
  .tier-badge {{
    font-size: 9px; letter-spacing: 1px; text-transform: uppercase; font-weight: 600;
    padding: 3px 12px; border-radius: 3px;
  }}
  .action-item {{
    display: flex; gap: 14px; align-items: flex-start;
    padding: 12px 14px; background: var(--card); border: 1px solid var(--border);
    border-radius: 7px; margin-bottom: 8px;
  }}
  .action-num {{
    width: 26px; height: 26px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700; flex-shrink: 0;
  }}
  .action-content {{ flex: 1; }}
  .action-title {{
    font-size: 12px; font-weight: 600; color: var(--text);
    margin-bottom: 3px; display: flex; align-items: center; gap: 10px;
  }}
  .action-time {{
    font-size: 9px; color: var(--muted); background: var(--card2);
    border: 1px solid var(--border); padding: 1px 7px; border-radius: 3px; font-weight: 400;
  }}
  .action-desc {{ font-size: 11px; color: var(--muted); line-height: 1.5; }}

  /* FOOTER */
  .page-footer {{
    position: absolute; bottom: 24px; left: 52px; right: 52px;
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid var(--border); padding-top: 12px;
    font-size: 9px; color: var(--muted);
  }}
  .footer-brand {{ color: var(--cyan); font-weight: 600; }}

  /* GLOSSARY */
  .methodology-text {{
    font-size: 12px; color: var(--muted); line-height: 1.75;
    background: var(--card); border: 1px solid var(--border);
    border-radius: 8px; padding: 20px 24px; margin-bottom: 20px;
  }}
  .glossary-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
  .glossary-item {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 6px; padding: 10px 14px;
  }}
  .glossary-term {{ font-size: 11px; font-weight: 600; color: var(--cyan); margin-bottom: 2px; }}
  .glossary-def {{ font-size: 10px; color: var(--muted); line-height: 1.4; }}

  @media print {{
    .cover, .content-page {{ page-break-after: always; }}
  }}
</style>
</head>
<body>
<div class="page">

<!-- COVER -->
<div class="cover">
  <div class="cover-line"></div>
  <div class="cover-header">
    <div class="cover-brand">
      <div class="cover-brand-name">{b['name']}</div>
      <div class="cover-brand-tag">{b.get('cover_tag', 'GEO Audit')}</div>
    </div>
    <div class="cover-confidential">Vertrouwelijk</div>
  </div>
  <div class="cover-divider"></div>
  <div class="cover-body">
    <div class="cover-eyebrow">GEO Visibility Rapport</div>
    <div class="cover-title">{company}<br><em>{url}</em></div>
    <div class="cover-url">{audit_date}</div>
    <div class="cover-logo-block">
      {logo_html}
      <div class="cover-logo-meta">
        <span class="cover-logo-company">{company}</span>
        <span class="cover-logo-url">{url}</span>
      </div>
    </div>
    {'<div class="cover-stats">' + stats_html + '</div>' if stats else ''}
    <div class="cover-score-row">
      <div class="cover-score-gauge">{gauge_svg(overall, 180)}</div>
      <div class="cover-score-text">
        <div class="cover-score-label">Overall GEO Score</div>
        <div class="cover-score-badge" style="color:{overall_color};background:{overall_color}18;border:1px solid {overall_color}40">{overall_label}</div>
        <div class="cover-score-verdict">{tagline}</div>
      </div>
    </div>
  </div>
  <div class="cover-footer">
    <div class="cover-footer-left">
      <div class="cover-footer-name">{b['contact_name']}</div>
      <div class="cover-footer-contact">{b['website']}</div>
    </div>
    <div class="cover-footer-date">{audit_date}</div>
  </div>
</div>

<!-- PAGE 2: EXECUTIVE SUMMARY + SCORES -->
<div class="content-page">
  <div class="page-label">Executive Summary</div>
  <div class="section-title">Het <em>Probleem</em></div>
  <div class="section-sub">{url} — Audit uitgevoerd {audit_date}</div>
  <div class="exec-summary">{summary}</div>
  <div class="overall-row">
    <div class="overall-row-label">Overall GEO Score</div>
    <div class="overall-row-score">{overall} / 100</div>
    <div class="overall-row-verdict">{overall_label}</div>
  </div>
  <div class="section-divider"></div>
  <div class="page-label">Score Breakdown</div>
  <div class="section-title"><em>Zes</em> Dimensies</div>
  <div class="section-sub">Elke gewogen dimensie draagt bij aan je totale GEO score.</div>
  <div class="dim-grid">{dim_cards_html}</div>
  <div class="page-footer">
    <span class="footer-brand">{b['name']}</span>
    <span>{b['website']}</span>
    <span>Vertrouwelijk · {audit_date}</span>
  </div>
</div>

<!-- PAGE 3: AI READINESS -->
<div class="content-page">
  <div class="page-label">AI Gereedheid</div>
  <div class="section-title">Platform <em>Scores</em></div>
  <div class="section-sub">Hoe waarschijnlijk het is dat elk AI-platform jouw content citeert. Onder 50 betekent significante barrières.</div>
  <div class="platform-grid">{platforms_html}</div>
  <div class="section-divider"></div>
  <div class="page-label">Crawler Toegang</div>
  <div class="section-title">Crawler <em>Status</em></div>
  <div class="section-sub">Expliciete crawler-toestemmingen signaleren AI-vriendelijkheid.</div>
  <table class="crawler-table">
    <thead><tr><th>Crawler</th><th>Platform</th><th>Status</th><th>Aanbeveling</th></tr></thead>
    <tbody>{crawler_rows_html}</tbody>
  </table>
  <div class="page-footer">
    <span class="footer-brand">{b['name']}</span>
    <span>{b['website']}</span>
    <span>Vertrouwelijk · {audit_date}</span>
  </div>
</div>

<!-- PAGE 4: BEVINDINGEN -->
<div class="content-page">
  <div class="page-label">Bevindingen</div>
  <div class="section-title">Wat We <em>Vonden</em></div>
  <div class="finding-summary">{len(findings)} problemen gevonden. {finding_summary}</div>
  {findings_html}
  <div class="page-footer">
    <span class="footer-brand">{b['name']}</span>
    <span>{b['website']}</span>
    <span>Vertrouwelijk · {audit_date}</span>
  </div>
</div>

<!-- PAGE 5: ACTIEPLAN -->
<div class="content-page">
  <div class="page-label">Actieplan</div>
  <div class="section-title">Wat Nu <em>Te Doen</em></div>
  <div class="section-sub">Geprioriteerd op impact en inspanning.</div>
  {'<div class="action-tier"><div class="tier-header"><span class="tier-label">Deze Week · Quick Wins</span><span class="tier-badge" style="color:' + c['secondary'] + ';background:' + c['secondary'] + '18;border:1px solid ' + c['secondary'] + '40">Direct Uitvoerbaar</span></div>' + qw_html + '</div>' if quick_wins else ''}
  {'<div class="action-tier"><div class="tier-header"><span class="tier-label">Deze Maand</span><span class="tier-badge" style="color:' + c['primary'] + ';background:' + c['primary'] + '18;border:1px solid ' + c['primary'] + '40">Content + Autoriteit</span></div>' + mt_html + '</div>' if medium_term else ''}
  {'<div class="action-tier"><div class="tier-header"><span class="tier-label">Dit Kwartaal · Strategisch</span><span class="tier-badge" style="color:#9B59B6;background:#9B59B618;border:1px solid #9B59B640">Lange Termijn</span></div>' + str_html + '</div>' if strategic else ''}
  <div class="page-footer">
    <span class="footer-brand">{b['name']}</span>
    <span>{b['website']}</span>
    <span>Vertrouwelijk · {audit_date}</span>
  </div>
</div>

<!-- PAGE 6: APPENDIX -->
<div class="content-page">
  <div class="page-label">Appendix</div>
  <div class="section-title"><em>Methodologie</em></div>
  <div class="methodology-text">{methodology or "Deze GEO audit analyseerde de website op zes gewogen dimensies: AI Citability & Visibility (25%), Brand Authority Signals (20%), Content Quality & E-E-A-T (20%), Technical Foundations (15%), Schema & Structured Data (10%), en Platform Optimization (10%)."}</div>
  <div class="section-divider"></div>
  <div class="glossary-grid">
    <div class="glossary-item"><div class="glossary-term">GEO</div><div class="glossary-def">Generative Engine Optimization — optimaliseren voor AI-citatie</div></div>
    <div class="glossary-item"><div class="glossary-term">E-E-A-T</div><div class="glossary-def">Experience, Expertise, Authoritativeness, Trustworthiness</div></div>
    <div class="glossary-item"><div class="glossary-term">llms.txt</div><div class="glossary-def">Machine-leesbaar bestand voor AI-begrip van de site</div></div>
    <div class="glossary-item"><div class="glossary-term">JSON-LD</div><div class="glossary-def">Gestructureerde data voor zoekmachines en AI</div></div>
    <div class="glossary-item"><div class="glossary-term">Schema.org</div><div class="glossary-def">Vocabulaire voor gestructureerde data</div></div>
    <div class="glossary-item"><div class="glossary-term">IndexNow</div><div class="glossary-def">Protocol voor directe zoekmachine-notificatie</div></div>
  </div>
  <div style="text-align:center;padding:20px 0;font-size:10px;color:var(--muted);">
    © {datetime.now().year} {b['name']} · {b['website']} · Vertrouwelijk
  </div>
  <div class="page-footer">
    <span class="footer-brand">{b['name']}</span>
    <span>{b['website']}</span>
    <span>Vertrouwelijk · {audit_date}</span>
  </div>
</div>

</div>
</body>
</html>"""
    return html


def generate_pdf(html: str, output_path: str):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}
            )
            browser.close()
        print(f"  PDF opgeslagen: {output_path}")
    except Exception as e:
        print(f"  Fout: {e}")
        html_path = output_path.replace(".pdf", ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  HTML opgeslagen: {html_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data_file")
    parser.add_argument("--output", "-o", default="geo-rapport.pdf")
    parser.add_argument("--client-logo", "-l")
    parser.add_argument("--brand-config", "-b")
    parser.add_argument("--html-only", action="store_true")
    args = parser.parse_args()

    if args.brand_config:
        apply_brand_config(args.brand_config)

    with open(args.data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\n  GEO Report — {BRAND['name']}")
    print(f"  Client: {data.get('company_name', 'Unknown')}")
    print(f"  Score:  {data.get('overall_score', 0)}/100\n")

    html = generate_html(data, logo_path=args.client_logo)

    if args.html_only:
        html_path = args.output.replace(".pdf", ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  HTML opgeslagen: {html_path}")
    else:
        generate_pdf(html, args.output)

    print("  Klaar.")


if __name__ == "__main__":
    main()