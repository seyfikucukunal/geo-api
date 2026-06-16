#!/usr/bin/env python3
"""
GEO Report Premium Beautifier
AI-syah.nl
"""

import json
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

BRAND = {
    "name": "AI-syah.nl",
    "tagline": "Generative Engine Optimization",
    "website": "ai-syah.nl",
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
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#27272a" stroke-width="10"
        stroke-dasharray="{arc_len:.1f} {gap:.1f}" stroke-dashoffset="{-gap/2 - circ*0.125:.1f}" stroke-linecap="round"/>
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="10"
        stroke-dasharray="{filled:.1f} {circ - filled:.1f}" stroke-dashoffset="{-gap/2 - circ*0.125:.1f}" stroke-linecap="round"/>
      <text x="{cx}" y="{cy - 6}" text-anchor="middle" font-family="Arial" font-size="{size // 4}" fill="{color}" font-weight="bold">{score}</text>
      <text x="{cx}" y="{cy + 14}" text-anchor="middle" font-family="Arial" font-size="11" fill="#a1a1aa" letter-spacing="1">/ 100</text>
    </svg>"""

def mini_gauge_svg(score, size=72):
    color = score_color(score)
    cx, cy, r = size // 2, size // 2, (size // 2) - 8
    circ = 2 * 3.14159 * r
    arc_len = circ * 0.75
    filled = arc_len * (score / 100)
    gap = circ - arc_len
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#27272a" stroke-width="6"
        stroke-dasharray="{arc_len:.1f} {gap:.1f}" stroke-dashoffset="{-gap/2 - circ*0.125:.1f}" stroke-linecap="round"/>
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="6"
        stroke-dasharray="{filled:.1f} {circ - filled:.1f}" stroke-dashoffset="{-gap/2 - circ*0.125:.1f}" stroke-linecap="round"/>
      <text x="{cx}" y="{cy + 5}" text-anchor="middle" font-family="Arial" font-size="13" fill="{color}" font-weight="bold">{score}</text>
    </svg>"""

def bar_chart_svg(dimensions, width=610, height=220):
    bars = ""
    label_w = 190; score_w = 40
    bar_area = width - label_w - score_w - 20
    row_h = height // len(dimensions); pad = 6
    for i, dim in enumerate(dimensions):
        y = i * row_h; score = dim.get("score", 0)
        bar_w = int(bar_area * score / 100); col = score_color(score)
        bg_y = y + pad; bg_h = row_h - pad * 2
        row_bg = "#1a1a1a" if i % 2 == 0 else "#111111"
        bars += f"""<rect x="0" y="{bg_y-2}" width="{width}" height="{bg_h+4}" fill="{row_bg}" rx="0"/>
        <text x="{label_w-10}" y="{y+row_h//2+4}" font-family="Arial" font-size="10" fill="#a1a1aa" text-anchor="end">{dim['name'][:28]}</text>
        <rect x="{label_w}" y="{bg_y}" width="{bar_area}" height="{bg_h}" fill="#27272a" rx="4"/>
        <rect x="{label_w}" y="{bg_y}" width="{bar_w}" height="{bg_h}" fill="{col}" rx="4" opacity="0.9"/>
        <text x="{label_w+bar_w+8}" y="{y+row_h//2+4}" font-family="Arial" font-size="11" fill="{col}" font-weight="bold">{score}</text>"""
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">{bars}</svg>"""

def platform_badge(name, score):
    col = score_color(score); label = score_label(score)
    return f"""<div class="platform-badge" style="border-color:{col}35">
      <div class="platform-score" style="color:{col}">{score}</div>
      <div class="platform-name">{name}</div>
      <div class="platform-label" style="color:{col};background:{col}18;border:1px solid {col}35">{label}</div>
    </div>"""

def platform_bar_chart_svg(platforms, width=610, height=180):
    bars = ""
    label_w = 160; score_w = 50
    bar_area = width - label_w - score_w - 20
    n = len(platforms); row_h = height // n; pad = 6
    for i, p in enumerate(platforms):
        y = i * row_h; score = p.get("score", 0); name = p.get("name", "")
        bar_w = int(bar_area * score / 100); col = score_color(score)
        bg_y = y + pad; bg_h = row_h - pad * 2
        row_bg = "#1a1a1a" if i % 2 == 0 else "#111111"
        bars += f"""<rect x="0" y="{bg_y-2}" width="{width}" height="{bg_h+4}" fill="{row_bg}"/>
        <text x="{label_w-10}" y="{y+row_h//2+4}" font-family="Arial" font-size="11" fill="#a1a1aa" text-anchor="end">{name}</text>
        <rect x="{label_w}" y="{bg_y}" width="{bar_area}" height="{bg_h}" fill="#27272a" rx="4"/>
        <rect x="{label_w}" y="{bg_y}" width="{bar_w}" height="{bg_h}" fill="{col}" rx="4" opacity="0.9"/>
        <text x="{label_w+bar_w+8}" y="{y+row_h//2+4}" font-family="Arial" font-size="11" fill="{col}" font-weight="bold">{score}/100</text>"""
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">{bars}</svg>"""

def finding_card(finding):
    sev = finding.get("severity", "LOW").upper(); col = severity_color(sev)
    title = finding.get("title", ""); body = finding.get("description", "")
    return f"""<div class="finding-card" style="border-left-color:{col};background:linear-gradient(90deg,{col}08 0%,transparent 60%)">
      <div class="finding-header">
        <span class="severity-badge" style="background:{col}20;color:{col};border:1px solid {col}40">{sev}</span>
        <span class="finding-title">{title}</span>
      </div>
      <p class="finding-body">{body}</p>
    </div>"""

def findings_grouped_html(findings, severity_color_fn):
    result = ""
    c = BRAND["colors"]
    sev_map = {"CRITICAL":("Kritiek",c["critical"]),"HIGH":("Hoog",c["high"]),"MEDIUM":("Medium",c["medium"]),"LOW":("Laag",c["low"])}
    for sev, (label, col) in sev_map.items():
        group = [f for f in findings if f.get("severity","").upper() == sev]
        if not group: continue
        result += f"""<div class="finding-group">
      <div class="finding-group-header" style="border-left:3px solid {col};background:{col}10">
        <span class="finding-group-badge" style="color:{col};background:{col}20;border:1px solid {col}40">{sev}</span>
        <span class="finding-group-label">{label} prioriteit — {len(group)} {"issue" if len(group)==1 else "issues"}</span>
      </div>
      {"".join(finding_card(f) for f in group)}
    </div>"""
    return result

def action_item(num, item, timeframe_color):
    title = item.get("title","") if isinstance(item,dict) else str(item)
    desc = item.get("description","") if isinstance(item,dict) else ""
    time_est = item.get("time_estimate","") if isinstance(item,dict) else ""
    time_html = f'<span class="action-time">{time_est}</span>' if time_est else ""
    return f"""<div class="action-item">
      <div class="action-num" style="background:{timeframe_color}20;color:{timeframe_color};border:1px solid {timeframe_color}40">{num}</div>
      <div class="action-content">
        <div class="action-title">{title}{time_html}</div>
        <div class="action-desc">{desc}</div>
      </div>
    </div>"""

def crawler_row(crawler):
    status = crawler.get("status","Unknown")
    if "Allowed" in status: sc = "#22c55e"
    elif "Blocked" in status or "Disallowed" in status: sc = "#ef4444"
    else: sc = "#eab308"
    return f"""<tr>
      <td>{crawler.get('name','')}</td>
      <td style="color:#a1a1aa">{crawler.get('platform','')}</td>
      <td><span style="color:{sc}">●</span> {status}</td>
      <td style="color:#a1a1aa;font-size:11px">{crawler.get('recommendation','')}</td>
    </tr>"""

def generate_html(data: dict, logo_path: str = None) -> str:
    c = BRAND["colors"]; b = BRAND
    company    = data.get("company_name","")
    url        = data.get("url","")
    audit_date = data.get("audit_date", datetime.now().strftime("%B %d, %Y"))
    overall    = data.get("overall_score", 0)
    tagline    = data.get("company_tagline","")
    stats      = data.get("stats",[])
    summary    = data.get("executive_summary","")
    profile    = data.get("company_profile",{})
    dimensions = data.get("dimensions",[])
    platforms  = data.get("platforms",[])
    crawlers   = data.get("crawlers",[])
    findings   = data.get("findings",[])
    quick_wins  = data.get("action_plan",{}).get("quick_wins",[])
    medium_term = data.get("action_plan",{}).get("medium_term",[])
    strategic   = data.get("action_plan",{}).get("strategic",[])
    methodology = data.get("methodology","")

    overall_color = score_color(overall)
    overall_label = score_label(overall)

    stats_html = "".join(f'<div class="stat-badge"><span class="stat-val">{s["value"]}</span><span class="stat-lbl">{s["label"]}</span></div>' for s in stats)

    dim_cards_html = ""
    for dim in dimensions:
        mg = mini_gauge_svg(dim.get("score",0), 68)
        wt = dim.get("weight",""); ws = dim.get("weighted_score","")
        ws_html = f'<div class="dim-weighted">{ws} pts</div>' if ws else ""
        dim_cards_html += f"""<div class="dim-card">
          <div class="dim-gauge">{mg}</div>
          <div class="dim-info">
            <div class="dim-name">{dim.get('name','')}</div>
            <div class="dim-sub">{dim.get('description','')}</div>
            <div class="dim-meta">{wt} weight {ws_html}</div>
          </div>
        </div>"""

    chart_html = bar_chart_svg(dimensions) if dimensions else ""
    platforms_html = "".join(platform_badge(p.get("name",""), p.get("score",0)) for p in platforms)
    platform_bar_html = platform_bar_chart_svg(platforms) if platforms else ""
    platform_table_html = "".join(f"""<div class="platform-table-row">
      <span class="pt-name">{p.get("name","")}</span>
      <span class="pt-score" style="color:{score_color(p.get("score",0))}">{p.get("score",0)}/100</span>
      <span class="pt-label" style="color:{score_color(p.get("score",0))};background:{score_color(p.get("score",0))}18;border:1px solid {score_color(p.get("score",0))}35">{score_label(p.get("score",0))}</span>
    </div>""" for p in platforms)

    avg_platform = round(sum(p.get("score",0) for p in platforms)/len(platforms)) if platforms else 0
    platform_summary = f"De gemiddelde AI-zichtbaarheidsscore van {company} is <strong>{avg_platform}/100</strong> — AI-zoekmachines kunnen het bedrijf moeilijk vinden en citeren. Directe actie is vereist."
    crawler_rows_html = "".join(crawler_row(cr) for cr in crawlers)
    findings_grouped = findings_grouped_html(findings, severity_color)

    finding_counts = {
        "CRITICAL": sum(1 for f in findings if f.get("severity","").upper()=="CRITICAL"),
        "HIGH":     sum(1 for f in findings if f.get("severity","").upper()=="HIGH"),
        "MEDIUM":   sum(1 for f in findings if f.get("severity","").upper()=="MEDIUM"),
        "LOW":      sum(1 for f in findings if f.get("severity","").upper()=="LOW"),
    }
    finding_summary = " · ".join(f'<span style="color:{severity_color(k)}">{v} {k}</span>' for k, v in finding_counts.items() if v > 0)

    qw_html  = "".join(action_item(i+1, it, c["secondary"]) for i, it in enumerate(quick_wins))
    mt_html  = "".join(action_item(i+1, it, c["primary"])   for i, it in enumerate(medium_term))
    str_html = "".join(action_item(i+1, it, "#9B59B6")      for i, it in enumerate(strategic))

    strengths_html = ""; gaps_html = ""
    if profile:
        strengths = profile.get("strengths",[])
        gaps = profile.get("critical_gaps",[])
        if strengths:
            tags = "".join(f'<div class="profile-tag strength"><span>✓</span> {s}</div>' for s in strengths)
            strengths_html = f'<div class="profile-section"><div class="profile-section-label">Sterktes</div>{tags}</div>'
        if gaps:
            tags = "".join(f'<div class="profile-tag gap"><span>✗</span> {g}</div>' for g in gaps)
            gaps_html = f'<div class="profile-section" style="margin-top:12px"><div class="profile-section-label">Kritieke Gaps</div>{tags}</div>'

    # ── Cover dynamic variables ──
    n_critical = finding_counts["CRITICAL"]
    n_high     = finding_counts["HIGH"]
    n_quick    = len(quick_wins)
    miss_pct   = max(20, min(95, 100 - overall))
    vis_pct    = max(5, min(80, overall // 5))
    risk_label = "HOOG" if overall < 40 else ("GEMIDDELD" if overall < 70 else "LAAG")

    _pc_map = {"chatgpt":"#10a37f","openai":"#10a37f","claude":"#d97a21","anthropic":"#d97a21",
               "gemini":"#4285f4","google":"#4285f4","bing":"#0078d4","copilot":"#0078d4",
               "microsoft":"#0078d4","perplexity":"#22d3ee"}
    def _pc(name):
        nl = name.lower()
        for k,v in _pc_map.items():
            if k in nl: return v
        return "#a1a1aa"
    def _ps(score):
        if score >= 70: return "Hoog","#22c55e"
        if score >= 40: return "Gemiddeld","#eab308"
        return "Laag","#ef4444"

    cover_platforms_html = ""
    for _p in platforms:
        _pn = _p.get("name",""); _psc = _p.get("score",0)
        _col = _pc(_pn); _slbl, _scol = _ps(_psc)
        cover_platforms_html += (f'<div class="plat-item">'
            f'<div class="plat-icon" style="background:{_col}">{_pn[0].upper() if _pn else "?"}</div>'
            f'<div class="plat-name">{_pn}</div>'
            f'<div class="plat-status" style="color:{_scol}">{_slbl}</div></div>')

    cover_impact_html = (
        f'<div class="impact-row"><div class="impact-icon" style="background:#10a37f20">🔍</div>'
        f'<div><div class="impact-val" style="color:#22d3ee">{miss_pct}%</div>'
        f'<div class="impact-lbl">van AI-vragen mist {company}</div></div></div>'
        f'<div class="impact-row"><div class="impact-icon" style="background:#f9731620">⚠</div>'
        f'<div><div class="impact-val" style="color:#f97316">{n_critical + n_high}</div>'
        f'<div class="impact-lbl">kritieke GEO-lekken gevonden</div></div></div>'
        f'<div class="impact-row"><div class="impact-icon" style="background:#22c55e20">⚡</div>'
        f'<div><div class="impact-val" style="color:#22c55e">{n_quick}</div>'
        f'<div class="impact-lbl">snelle verbeteringen mogelijk</div></div></div>'
    )
    # ────────────────────────────────────────────────────────────────────────

    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<title>GEO Rapport — {company}</title>
<style>
  @page{{size:A4;margin:0 0 48px 0;@bottom-left{{content:element(run-footer-brand);width:33%}}@bottom-center{{content:element(run-footer-page);width:33%}}@bottom-right{{content:element(run-footer-right);width:34%}}}}
  @page cover-page{{size:A4;margin:0}}
  .cover{{page:cover-page}}
  .run-footer-brand{{position:running(run-footer-brand);font-family:Arial,Helvetica,sans-serif;font-size:9px;color:#22d3ee;font-weight:600;padding:8px 0 0 52px;border-top:1px solid #27272a}}
  .run-footer-page{{position:running(run-footer-page);font-family:Arial,Helvetica,sans-serif;font-size:9px;color:#a1a1aa;padding:8px 0 0;border-top:1px solid #27272a;text-align:center}}
  .run-footer-right{{position:running(run-footer-right);font-family:Arial,Helvetica,sans-serif;font-size:9px;color:#a1a1aa;padding:8px 52px 0 0;border-top:1px solid #27272a;text-align:right}}
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  :root{{--cyan:{c['primary']};--bg:{c['bg_dark']};--card:{c['bg_card']};--card2:{c['bg_card_alt']};--border:{c['border']};--text:{c['text_primary']};--muted:{c['text_secondary']}}}
  html{{font-size:13px}}
  body{{font-family:Arial,Helvetica,sans-serif;background:var(--bg);color:var(--text);line-height:1.6}}
  .page{{width:210mm;margin:0 auto}}

  /* ══ COVER ══ */
  .cover{{background:linear-gradient(160deg,#000 0%,#0a0a0f 50%,#000 100%);display:flex;flex-direction:column;position:relative;overflow:hidden;page-break-after:always;height:297mm}}
  .cover-line{{position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,transparent,{c['primary']},transparent)}}

  /* header */
  .cover-header{{padding:24px 40px 0;display:flex;justify-content:space-between;align-items:flex-start}}
  .cover-brand-logo{{display:flex;align-items:center;gap:12px}}
  .cover-brand-text{{display:flex;flex-direction:column;gap:1px}}
  .cover-brand-name{{font-size:15px;letter-spacing:2px;font-weight:800;color:var(--cyan);text-transform:uppercase}}
  .cover-brand-tag{{font-size:9px;letter-spacing:2px;color:var(--muted);text-transform:uppercase}}
  .cover-brand-sub{{font-size:9px;color:#52525b;margin-top:2px}}
  .cover-confidential{{display:flex;align-items:center;gap:5px;font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);border:1px solid var(--border);padding:5px 12px;border-radius:4px}}
  .cover-divider{{margin:14px 40px 0;height:1px;background:linear-gradient(90deg,var(--cyan),transparent)}}

  /* two-col body */
  .cover-body{{display:grid;grid-template-columns:1fr 272px;gap:16px;padding:12px 40px 0;flex:1;align-items:start}}
  .cover-left{{display:flex;flex-direction:column}}
  .cover-right{{display:flex;flex-direction:column;gap:12px;align-self:start}}
  .cover-eyebrow{{font-size:8px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-bottom:6px}}
  .cover-title{{font-size:54px;line-height:1.0;color:var(--text);margin-bottom:6px;font-weight:900}}
  .cover-url{{font-size:12px;color:var(--muted);margin-bottom:18px}}

  /* stats */
  .cover-stats{{display:flex;gap:8px;flex-wrap:nowrap;margin-bottom:16px}}
  .stat-badge{{background:var(--card);border:1px solid var(--border);border-bottom:2px solid var(--cyan);border-radius:8px;padding:10px 8px;display:flex;flex-direction:column;align-items:center;gap:4px;flex:1;min-width:0}}
  .stat-val{{font-size:18px;color:var(--cyan);font-weight:bold}}
  .stat-lbl{{font-size:8px;color:var(--muted);text-transform:uppercase;letter-spacing:1px}}

  /* impact */
  .cover-impact{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px 18px;margin-bottom:12px}}
  .cover-impact-title{{font-size:8px;letter-spacing:2px;text-transform:uppercase;color:var(--cyan);margin-bottom:8px;font-weight:700}}
  .impact-row{{display:flex;align-items:center;gap:12px;margin-bottom:10px}}
  .impact-icon{{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0}}
  .impact-val{{font-size:22px;font-weight:800}}
  .impact-lbl{{font-size:11px;color:var(--muted);line-height:1.3}}
  .cover-impact-footer{{display:flex;gap:14px;padding-top:8px;border-top:1px solid var(--border);margin-top:2px}}
  .impact-pill{{display:flex;flex-direction:column;gap:2px}}
  .impact-pill-label{{font-size:7px;text-transform:uppercase;letter-spacing:1px;color:var(--muted)}}
  .impact-pill-val{{font-size:13px;font-weight:800}}

  /* right col */
  .cover-score-card{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:18px 16px}}
  .cover-score-card-label{{font-size:8px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:4px}}
  .cover-score-big{{font-size:50px;font-weight:900;line-height:1;color:{overall_color};margin-bottom:2px}}
  .cover-score-denom{{font-size:18px;color:var(--muted);font-weight:400}}
  .cover-score-badge{{display:inline-flex;align-items:center;gap:5px;font-size:9px;letter-spacing:2px;font-weight:700;text-transform:uppercase;padding:4px 10px;border-radius:4px;margin:6px 0;color:{overall_color};background:{overall_color}18;border:1px solid {overall_color}40}}
  .cover-score-verdict{{font-size:10px;color:var(--muted);line-height:1.6}}
  .cover-score-gauge{{margin:8px 0;display:flex;justify-content:center}}

  /* benchmark */
  .cover-benchmark{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px 14px}}
  .cover-benchmark-title{{font-size:8px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:8px}}
  .bench-row{{margin-bottom:7px}}
  .bench-label{{font-size:9px;color:var(--muted);margin-bottom:3px;display:flex;justify-content:space-between}}
  .bench-label span{{color:var(--text);font-weight:600}}
  .bench-bar-bg{{height:5px;background:#27272a;border-radius:3px}}
  .bench-bar{{height:5px;border-radius:3px}}

  /* platform grid on cover */
  .cover-platforms{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px 14px}}
  .cover-platforms-title{{font-size:8px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:8px}}
  .platform-grid{{display:flex;gap:6px;flex-wrap:wrap}}
  .plat-item{{display:flex;flex-direction:column;align-items:center;gap:5px;flex:1;min-width:80px;background:#18181b;border:1px solid var(--border);border-radius:8px;padding:12px 8px}}
  .plat-icon{{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:white}}
  .plat-name{{font-size:9px;color:var(--muted);text-align:center;line-height:1.3}}
  .plat-status{{font-size:9px;font-weight:700;text-align:center}}

  /* footer */
  .cover-footer{{padding:14px 40px 18px;border-top:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;gap:16px;margin-top:auto}}
  .cover-footer-left{{display:flex;align-items:center;gap:14px}}
  .cover-footer-divider{{width:1px;height:34px;background:var(--border);flex-shrink:0}}
  .cover-footer-tagline{{font-size:9.5px;color:var(--muted);line-height:1.6;max-width:320px}}
  .cover-trust-badges{{display:flex;gap:16px}}
  .trust-badge{{display:flex;flex-direction:column;align-items:center;gap:3px;font-size:7.5px;color:var(--muted);text-align:center;letter-spacing:0.5px;text-transform:uppercase;max-width:64px}}
  .trust-icon{{font-size:15px}}

  /* ══ CONTENT PAGES ══ */
  .content-page{{padding:48px 52px 20px 52px;height:297mm;page-break-after:always;position:relative;background:var(--bg);overflow:hidden}}
  .content-page-auto{{padding:48px 52px 20px 52px;page-break-after:always;background:var(--bg);position:relative}}
  .content-page::before,.content-page-auto::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--cyan) 0%,transparent 60%)}}
  .page-label{{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-bottom:8px}}
  .section-title{{font-size:28px;color:var(--text);margin-bottom:6px;font-weight:bold}}
  .section-title em{{color:var(--cyan);font-style:normal}}
  .section-sub{{font-size:12px;color:var(--muted);margin-bottom:28px}}
  .section-divider{{height:1px;background:var(--border);margin:28px 0}}
  .profile-description{{font-size:12px;color:var(--text);line-height:1.7;padding:16px 20px;background:var(--card);border:1px solid var(--border);border-left:3px solid var(--cyan);border-radius:8px;margin-bottom:20px}}
  .company-profile-block{{display:grid;grid-template-columns:1fr 260px;gap:20px;margin-bottom:20px}}
  .profile-left{{display:flex;flex-direction:column;gap:12px}}
  .profile-section{{display:flex;flex-direction:column;gap:6px}}
  .profile-section-label{{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:4px}}
  .profile-tag{{display:flex;align-items:flex-start;gap:8px;font-size:11px;padding:7px 12px;border-radius:6px;line-height:1.4}}
  .profile-tag.strength{{background:#052e16;color:#86efac;border:1px solid #16a34a30}}
  .profile-tag.strength span{{color:#22c55e;flex-shrink:0}}
  .profile-tag.gap{{background:#1c0a00;color:#fca5a5;border:1px solid #dc262630}}
  .profile-tag.gap span{{color:#ef4444;flex-shrink:0}}
  .profile-right{{display:flex;flex-direction:column;gap:12px}}
  .profile-meta-card{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px}}
  .profile-meta-row{{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border);font-size:11px}}
  .profile-meta-row:last-child{{border-bottom:none}}
  .meta-label{{color:var(--muted)}}
  .meta-value{{color:var(--text);font-weight:500;text-align:right;max-width:150px}}
  .profile-meta-divider{{height:1px;background:#22d3ee30;margin:4px 0}}
  .scores-table{{width:100%;margin-bottom:20px}}
  .scores-table-header{{display:grid;grid-template-columns:1fr 100px 80px 80px;padding:8px 12px;background:var(--card);border:1px solid var(--border);border-radius:6px 6px 0 0;font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted)}}
  .scores-table-row{{display:grid;grid-template-columns:1fr 100px 80px 80px;padding:10px 12px;border:1px solid var(--border);border-top:none;font-size:11px}}
  .st-name{{color:var(--text);font-weight:500}}
  .st-score{{font-weight:600}}
  .st-weight{{color:var(--muted)}}
  .st-weighted{{color:var(--cyan);font-weight:500}}
  .scores-table-total{{display:grid;grid-template-columns:1fr 100px 80px 80px;padding:10px 12px;background:var(--card);border:1px solid var(--border);border-top:2px solid var(--cyan);border-radius:0 0 6px 6px;font-size:12px;font-weight:600;color:var(--text)}}
  .chart-wrap{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px 24px;margin-top:8px}}
  .dim-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:28px}}
  .dim-card{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px 16px;display:flex;align-items:center;gap:14px}}
  .dim-gauge{{flex-shrink:0}}
  .dim-name{{font-size:12px;font-weight:600;color:var(--text);margin-bottom:2px}}
  .dim-sub{{font-size:10px;color:var(--muted);margin-bottom:4px;line-height:1.4}}
  .dim-meta{{font-size:10px;color:var(--muted)}}
  .dim-weighted{{font-size:10px;color:var(--cyan)}}
  .platform-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:28px}}
  .platform-badge{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px 12px;text-align:center}}
  .platform-score{{font-size:28px;font-weight:bold;margin-bottom:4px}}
  .platform-name{{font-size:10px;color:var(--muted);margin-bottom:6px}}
  .platform-label{{display:inline-block;font-size:9px;letter-spacing:1px;text-transform:uppercase;font-weight:600;padding:2px 8px;border-radius:3px}}
  .ai-summary-block{{background:var(--card);border:1px solid var(--border);border-left:3px solid var(--cyan);border-radius:8px;padding:14px 18px;font-size:12px;line-height:1.7;color:var(--muted);margin-bottom:20px}}
  .ai-summary-block strong{{color:var(--text)}}
  .platform-table-header{{display:grid;grid-template-columns:1fr 120px 120px;padding:8px 12px;background:var(--card);border:1px solid var(--border);border-radius:6px 6px 0 0;font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted)}}
  .platform-table-row{{display:grid;grid-template-columns:1fr 120px 120px;padding:10px 12px;border:1px solid var(--border);border-top:none;font-size:11px;color:var(--text)}}
  .pt-name{{color:var(--text);font-weight:500}}
  .pt-score{{font-weight:600}}
  .pt-label{{display:inline-block;font-size:9px;letter-spacing:1px;text-transform:uppercase;font-weight:600;padding:2px 8px;border-radius:3px;align-self:center}}
  .crawler-table{{width:100%;border-collapse:collapse;font-size:11px}}
  .crawler-table th{{background:var(--card2);color:var(--muted);font-size:9px;letter-spacing:2px;text-transform:uppercase;padding:8px 12px;text-align:left;border-bottom:1px solid var(--border)}}
  .crawler-table td{{padding:8px 12px;border-bottom:1px solid var(--border);color:var(--text)}}
  .finding-group{{margin-bottom:24px;page-break-inside:avoid}}
  .finding-group-header{{display:flex;align-items:center;gap:10px;padding:8px 14px;border-radius:6px 6px 0 0}}
  .finding-group-badge{{font-size:9px;letter-spacing:1.5px;font-weight:700;padding:2px 8px;border-radius:3px;text-transform:uppercase}}
  .finding-group-label{{font-size:11px;color:var(--muted);font-weight:500}}
  .finding-summary{{font-size:11px;color:var(--muted);margin-bottom:16px}}
  .finding-card{{border-left:3px solid;background:var(--card);border-top:1px solid var(--border);border-right:1px solid var(--border);border-bottom:1px solid var(--border);border-radius:0 6px 6px 0;padding:14px 16px;margin-bottom:10px;page-break-inside:avoid}}
  .finding-header{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
  .severity-badge{{font-size:9px;letter-spacing:1.5px;font-weight:700;padding:2px 8px;border-radius:3px;text-transform:uppercase;flex-shrink:0}}
  .finding-title{{font-size:12px;font-weight:600;color:var(--text)}}
  .finding-body{{font-size:11px;color:var(--muted);line-height:1.6}}
  .action-tier{{margin-bottom:28px;page-break-inside:avoid}}
  .tier-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}}
  .tier-label{{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--muted)}}
  .tier-badge{{font-size:9px;letter-spacing:1px;text-transform:uppercase;font-weight:600;padding:3px 12px;border-radius:3px}}
  .action-item{{display:flex;gap:14px;align-items:flex-start;padding:12px 14px;background:var(--card);border:1px solid var(--border);border-radius:7px;margin-bottom:8px;page-break-inside:avoid}}
  .action-num{{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0}}
  .action-content{{flex:1}}
  .action-title{{font-size:12px;font-weight:600;color:var(--text);margin-bottom:3px;display:flex;align-items:center;gap:10px}}
  .action-time{{font-size:9px;color:var(--muted);background:var(--card2);border:1px solid var(--border);padding:1px 7px;border-radius:3px;font-weight:400}}
  .action-desc{{font-size:11px;color:var(--muted);line-height:1.5}}
  .page-footer{{position:absolute;bottom:20px;left:52px;right:52px;display:grid;grid-template-columns:1fr 1fr 1fr;align-items:center;border-top:1px solid var(--border);padding-top:10px;font-size:9px;color:var(--muted)}}
  .page-footer-static{{position:relative;margin-top:32px;left:0;right:0;display:grid;grid-template-columns:1fr 1fr 1fr;align-items:center;border-top:1px solid var(--border);padding-top:10px;font-size:9px;color:var(--muted)}}
  .footer-brand{{color:var(--cyan);font-weight:600}}
  .footer-page{{text-align:center;color:var(--muted)}}
  .footer-right{{text-align:right}}
  .methodology-text{{font-size:12px;color:var(--muted);line-height:1.75;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:20px 24px;margin-bottom:20px}}
  .glossary-table-header{{display:grid;grid-template-columns:140px 1fr;padding:8px 12px;background:var(--card);border:1px solid var(--border);border-radius:6px 6px 0 0;font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted)}}
  .glossary-table-row{{display:grid;grid-template-columns:140px 1fr;padding:9px 12px;border:1px solid var(--border);border-top:none;font-size:11px}}
  .gt-term{{color:var(--cyan);font-weight:600}}
  .gt-def{{color:var(--muted);line-height:1.5}}
  .disclaimer-block{{font-size:10px;color:var(--muted);line-height:1.6;padding:14px 18px;background:var(--card);border:1px solid var(--border);border-radius:6px;margin-top:8px}}
  @media print{{.cover,.content-page{{page-break-after:always}}}}
</style>
</head>
<body>
<div class="run-footer-brand">{b['name']}</div>
<div class="run-footer-page">Pagina <span style="content:counter(page)"></span></div>
<div class="run-footer-right">Vertrouwelijk · {audit_date}</div>
<div class="page">

<!-- COVER -->
<div class="cover">
  <div class="cover-line"></div>
  <div class="cover-header">
    <div class="cover-brand-logo">
      <svg width="34" height="34" viewBox="0 0 34 34">
        <circle cx="17" cy="7"  r="4" fill="#22d3ee"/>
        <circle cx="27" cy="23" r="4" fill="#22d3ee"/>
        <circle cx="7"  cy="23" r="4" fill="#22d3ee" opacity="0.6"/>
        <circle cx="17" cy="30" r="3" fill="#22d3ee" opacity="0.35"/>
        <line x1="17" y1="7"  x2="27" y2="23" stroke="#22d3ee" stroke-width="1.5" opacity="0.5"/>
        <line x1="17" y1="7"  x2="7"  y2="23" stroke="#22d3ee" stroke-width="1.5" opacity="0.5"/>
        <line x1="27" y1="23" x2="17" y2="30" stroke="#22d3ee" stroke-width="1"   opacity="0.3"/>
        <line x1="7"  y1="23" x2="17" y2="30" stroke="#22d3ee" stroke-width="1"   opacity="0.3"/>
      </svg>
      <div class="cover-brand-text">
        <div class="cover-brand-name">{b['name']}</div>
        <div class="cover-brand-tag">GEO Intelligence Report</div>
        <div class="cover-brand-sub">AI Visibility Assessment voor {company}</div>
      </div>
    </div>
    <div class="cover-confidential">🔒 Vertrouwelijk</div>
  </div>
  <div class="cover-divider"></div>

  <div class="cover-body">
    <!-- LEFT -->
    <div class="cover-left">
      <div class="cover-eyebrow">GEO Visibility Report</div>
      <div class="cover-title">{company}</div>
      <div class="cover-url">{url} &bull; {audit_date}</div>
      {'<div class="cover-stats">' + stats_html + '</div>' if stats else ''}
      <div class="cover-impact">
        <div class="cover-impact-title">Geschatte Impact</div>
        {cover_impact_html}
        <div class="cover-impact-footer">
          <div class="impact-pill">
            <span class="impact-pill-label">Potentiële gemiste AI-leads</span>
            <span class="impact-pill-val" style="color:#ef4444">{risk_label}</span>
          </div>
          <div style="width:1px;background:#27272a"></div>
          <div class="impact-pill">
            <span class="impact-pill-label">Geschatte AI-zichtbaarheid</span>
            <span class="impact-pill-val" style="color:#ef4444">{vis_pct}%</span>
          </div>
        </div>
      </div>
    </div>
    <!-- RIGHT -->
    <div class="cover-right">
      <div class="cover-score-card">
        <div class="cover-score-card-label">GEO Score</div>
        <div class="cover-score-big">{overall}<span class="cover-score-denom">/100</span></div>
        <div class="cover-score-badge">⚠ {overall_label}</div>
        <div class="cover-score-verdict">{tagline}</div>
        <div class="cover-score-gauge">{gauge_svg(overall, 120)}</div>
      </div>
      <div class="cover-benchmark">
        <div class="cover-benchmark-title">GEO Score Benchmark</div>
        <div class="bench-row">
          <div class="bench-label">{company} <span>{overall}/100</span></div>
          <div class="bench-bar-bg"><div class="bench-bar" style="width:{overall}%;background:{overall_color}"></div></div>
        </div>
        <div class="bench-row">
          <div class="bench-label">Concurrenten (gem.) <span>61/100</span></div>
          <div class="bench-bar-bg"><div class="bench-bar" style="width:61%;background:#22d3ee"></div></div>
        </div>
        <div class="bench-row">
          <div class="bench-label">Top spelers <span>82/100</span></div>
          <div class="bench-bar-bg"><div class="bench-bar" style="width:82%;background:#22d3ee60"></div></div>
        </div>
        <div style="font-size:8px;color:#52525b;margin-top:5px">Hoe hoger de score, hoe beter zichtbaar in AI-antwoorden.</div>
      </div>
    </div>
  </div>

  <!-- FULL-WIDTH PLATFORM ROW -->
  <div style="margin:8px 40px 0;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px 16px;">
    <div style="font-size:8px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:10px;font-weight:600">GEO Analyse over AI-Platforms</div>
    <div style="display:flex;gap:10px;">
      {cover_platforms_html}
    </div>
  </div>

  <!-- TAGLINE BLOK -->
  <div style="margin:10px 40px 0;border-top:1px solid #27272a;display:flex;flex-direction:column;">
    <div style="display:flex;align-items:center;gap:14px;padding:14px 18px;">
      <svg width="120" height="30" viewBox="0 0 120 30">
        <circle cx="10" cy="5"  r="4" fill="#22d3ee"/>
        <circle cx="20" cy="15" r="4" fill="#22d3ee"/>
        <circle cx="10" cy="25" r="4" fill="#22d3ee" opacity="0.6"/>
        <circle cx="3"  cy="15" r="2.5" fill="#22d3ee" opacity="0.35"/>
        <line x1="10" y1="5"  x2="20" y2="15" stroke="#22d3ee" stroke-width="1.5" opacity="0.5"/>
        <line x1="10" y1="25" x2="20" y2="15" stroke="#22d3ee" stroke-width="1.5" opacity="0.5"/>
        <line x1="10" y1="5"  x2="3"  y2="15" stroke="#22d3ee" stroke-width="1" opacity="0.25"/>
        <line x1="10" y1="25" x2="3"  y2="15" stroke="#22d3ee" stroke-width="1" opacity="0.25"/>
        <text x="30" y="14" font-family="Arial" font-size="11" font-weight="800" fill="#22d3ee" letter-spacing="2">AI-SYAH.NL</text>
      </svg>
      <div style="width:1px;height:36px;background:#27272a;flex-shrink:0"></div>
      <p style="font-size:13px;font-weight:700;color:#ffffff;line-height:1.5;">Dit rapport is samengesteld door team AI-syah.nl om inzicht te geven in de AI-zichtbaarheid van uw bedrijf binnen de grote LLM's en AI-zoekmachines.</p>
    </div>
    <div style="display:flex;justify-content:space-around;padding:12px 18px 16px;border-top:1px solid #27272a;">
      <div style="display:flex;flex-direction:column;align-items:center;gap:5px;font-size:8px;color:#a1a1aa;text-align:center;text-transform:uppercase;letter-spacing:0.5px;max-width:80px;"><span style="font-size:20px;">🛡</span>Onafhankelijk en objectief</div>
      <div style="display:flex;flex-direction:column;align-items:center;gap:5px;font-size:8px;color:#a1a1aa;text-align:center;text-transform:uppercase;letter-spacing:0.5px;max-width:80px;"><span style="font-size:20px;">📊</span>Data-gedreven inzichten</div>
      <div style="display:flex;flex-direction:column;align-items:center;gap:5px;font-size:8px;color:#a1a1aa;text-align:center;text-transform:uppercase;letter-spacing:0.5px;max-width:80px;"><span style="font-size:20px;">✅</span>Praktische actiepunten</div>
      <div style="display:flex;flex-direction:column;align-items:center;gap:5px;font-size:8px;color:#a1a1aa;text-align:center;text-transform:uppercase;letter-spacing:0.5px;max-width:80px;"><span style="font-size:20px;">🔒</span>100% vertrouwelijk</div>
    </div>
  </div>
</div>

<!-- PAGE 2: EXECUTIVE SUMMARY -->
<div class="content-page">
  <div class="page-label">Executive Summary</div>
  <div class="section-title">Uw GEO <em>Zichtbaarheid</em></div>
  <div class="section-sub">{url} — Audit uitgevoerd {audit_date}</div>
  <div class="profile-description">{profile.get('description', summary)}</div>
  <div class="company-profile-block">
    <div class="profile-left">{strengths_html}{gaps_html}</div>
    <div class="profile-right">
      <div class="profile-meta-card">
        <div class="profile-meta-row"><span class="meta-label">Bedrijf</span><span class="meta-value">{company}</span></div>
        <div class="profile-meta-row"><span class="meta-label">Website</span><span class="meta-value">{url}</span></div>
        {f'<div class="profile-meta-row"><span class="meta-label">Opgericht</span><span class="meta-value">{profile.get("founded","")}</span></div>' if profile.get("founded") else ""}
        {f'<div class="profile-meta-row"><span class="meta-label">Locatie</span><span class="meta-value">{profile.get("location","")}</span></div>' if profile.get("location") else ""}
        {f'<div class="profile-meta-row"><span class="meta-label">Industrie</span><span class="meta-value">{profile.get("industry","")}</span></div>' if profile.get("industry") else ""}
        <div class="profile-meta-divider"></div>
        <div class="profile-meta-row"><span class="meta-label">Audit datum</span><span class="meta-value">{audit_date}</span></div>
      </div>
    </div>
  </div>
  <div class="section-divider"></div>
  <div class="page-label">Score Breakdown</div>
  <div class="scores-table">
    <div class="scores-table-header"><span>Categorie</span><span>Score</span><span>Gewicht</span><span>Gewogen</span></div>
    {"".join(f'<div class="scores-table-row"><span class="st-name">{d.get("name","")}</span><span class="st-score" style="color:{score_color(d.get("score",0))}">{d.get("score",0)}/100</span><span class="st-weight">{d.get("weight","")}</span><span class="st-weighted">{d.get("weighted_score","")} pts</span></div>' for d in dimensions)}
    <div class="scores-table-total"><span>Totale GEO Score</span><span></span><span>100%</span><span style="color:{overall_color};font-weight:bold">{overall} pts</span></div>
  </div>
</div>

<!-- PAGE 3: SCORE BREAKDOWN VISUAL -->
<div class="content-page">
  <div class="page-label">Score Breakdown</div>
  <div class="section-title"><em>Zes</em> Dimensies</div>
  <div class="section-sub">Elke gewogen dimensie draagt bij aan je totale GEO score.</div>
  <div class="dim-grid">{dim_cards_html}</div>
  <div class="section-divider"></div>
  <div class="page-label">Visueel Overzicht</div>
  <div class="chart-wrap">{chart_html}</div>
</div>

<!-- PAGE 4: AI GEREEDHEID -->
<div class="content-page">
  <div class="page-label">AI Gereedheid</div>
  <div class="section-title">Platform <em>Scores</em></div>
  <div class="section-sub">Hoe waarschijnlijk het is dat elk AI-platform jouw content citeert.</div>
  <div class="ai-summary-block"><p>{platform_summary}</p></div>
  <div class="chart-wrap" style="margin-bottom:20px">{platform_bar_html}</div>
  <div class="platform-table-header"><span>AI Platform</span><span>Score</span><span>Status</span></div>
  {platform_table_html}
</div>

<!-- PAGE 5: CRAWLER STATUS -->
<div class="content-page">
  <div class="page-label">Crawler Toegang</div>
  <div class="section-title">Crawler <em>Status</em></div>
  <div class="section-sub">Expliciete crawler-toestemmingen signaleren AI-vriendelijkheid aan zoekmachines.</div>
  <div class="ai-summary-block"><p>AI-crawlers zijn gespecialiseerde bots die content indexeren voor AI-platforms. Door expliciete toestemming te geven in <strong>robots.txt</strong> signaleert {company} dat het AI-vriendelijk is — dit verhoogt de kans op citatie significant.</p></div>
  <table class="crawler-table">
    <thead><tr><th>Crawler</th><th>Platform</th><th>Status</th><th>Aanbeveling</th></tr></thead>
    <tbody>{crawler_rows_html}</tbody>
  </table>
</div>

<!-- PAGE 6+: BEVINDINGEN (auto, meerdere paginas mogelijk) -->
<div class="content-page-auto">
  <div class="page-label">Bevindingen</div>
  <div class="section-title">Wat We <em>Vonden</em></div>
  <div class="finding-summary">{len(findings)} problemen gevonden. {finding_summary}</div>
  {findings_grouped}
</div>

<!-- ACTIEPLAN (auto, meerdere paginas mogelijk) -->
<div class="content-page-auto">
  <div class="page-label">Actieplan</div>
  <div class="section-title">Wat Nu <em>Te Doen</em></div>
  <div class="section-sub">Geprioriteerd op impact en inspanning.</div>
  {'<div class="action-tier"><div class="tier-header"><span class="tier-label">Deze Week · Quick Wins</span><span class="tier-badge" style="color:'+c['secondary']+';background:'+c['secondary']+'18;border:1px solid '+c['secondary']+'40">Direct Uitvoerbaar</span></div>'+qw_html+'</div>' if quick_wins else ''}
  {'<div class="action-tier"><div class="tier-header"><span class="tier-label">Deze Maand</span><span class="tier-badge" style="color:'+c['primary']+';background:'+c['primary']+'18;border:1px solid '+c['primary']+'40">Content + Autoriteit</span></div>'+mt_html+'</div>' if medium_term else ''}
  {'<div class="action-tier"><div class="tier-header"><span class="tier-label">Dit Kwartaal · Strategisch</span><span class="tier-badge" style="color:#9B59B6;background:#9B59B618;border:1px solid #9B59B640">Lange Termijn</span></div>'+str_html+'</div>' if strategic else ''}
</div>

<!-- APPENDIX -->
<div class="content-page">
  <div class="page-label">Appendix</div>
  <div class="section-title"><em>Methodologie</em></div>
  <div class="methodology-text">
    {methodology or "Deze GEO audit analyseerde de website op zes gewogen dimensies: AI Citability &amp; Visibility (25%), Brand Authority Signals (20%), Content Quality &amp; E-E-A-T (20%), Technical Foundations (15%), Schema &amp; Structured Data (10%), en Platform Optimization (10%)."}
    <div style="margin-top:12px"><strong style="color:var(--text)">Platforms beoordeeld:</strong> Google AI Overviews, ChatGPT Web Search, Perplexity AI, Google Gemini, Bing Copilot</div>
    <div style="margin-top:8px"><strong style="color:var(--text)">Standaarden gebruikt:</strong> Google Search Quality Rater Guidelines, Schema.org specificatie, llms.txt standaard, Core Web Vitals</div>
  </div>
  <div class="section-divider"></div>
  <div class="page-label">Begrippenlijst</div>
  <div class="section-title">Glossary</div>
  <div class="glossary-table-header"><span>Term</span><span>Definitie</span></div>
  <div class="glossary-table-row"><span class="gt-term">GEO</span><span class="gt-def">Generative Engine Optimization — optimaliseren van content voor AI-zoekmachine citatie</span></div>
  <div class="glossary-table-row"><span class="gt-term">AIO</span><span class="gt-def">AI Overviews — door Google gegenereerde AI-antwoorden bovenaan zoekresultaten</span></div>
  <div class="glossary-table-row"><span class="gt-term">E-E-A-T</span><span class="gt-def">Experience, Expertise, Authoritativeness, Trustworthiness — kwaliteitssignalen voor AI</span></div>
  <div class="glossary-table-row"><span class="gt-term">llms.txt</span><span class="gt-def">Machine-leesbaar bestand dat AI-systemen informeert over de inhoud van een website</span></div>
  <div class="glossary-table-row"><span class="gt-term">JSON-LD</span><span class="gt-def">JavaScript Object Notation for Linked Data — gestructureerde data voor zoekmachines</span></div>
  <div class="glossary-table-row"><span class="gt-term">Schema.org</span><span class="gt-def">Vocabulaire voor gestructureerde data, herkend door alle grote zoekmachines</span></div>
  <div class="glossary-table-row"><span class="gt-term">SSR</span><span class="gt-def">Server-Side Rendering — HTML genereren op de server voor optimale crawler toegang</span></div>
  <div class="glossary-table-row"><span class="gt-term">IndexNow</span><span class="gt-def">Protocol voor directe notificatie van zoekmachines bij content wijzigingen</span></div>
  <div class="section-divider"></div>
  <div class="disclaimer-block">Dit rapport is gegenereerd door {b['name']}. Scores en aanbevelingen zijn gebaseerd op geautomatiseerde analyse en industrie benchmarks. Resultaten dienen gevalideerd te worden met platform-specifieke testing. © {datetime.now().year} {b['name']} · Vertrouwelijk</div>
</div>

</div></body></html>"""
    return html


def generate_pdf(html: str, output_path: str):
    try:
        from weasyprint import HTML
        HTML(string=html, base_url=None).write_pdf(output_path)
        print(f"  PDF opgeslagen: {output_path}")
    except Exception as e:
        print(f"  Fout WeasyPrint: {e}")
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.set_content(html, wait_until="networkidle")
                page.pdf(path=output_path, format="A4", print_background=True,
                         margin={"top":"0","bottom":"0","left":"0","right":"0"})
                browser.close()
            print(f"  PDF opgeslagen via Playwright: {output_path}")
        except Exception as e2:
            print(f"  Fout Playwright: {e2}")
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
    print(f"  Client: {data.get('company_name','Unknown')}")
    print(f"  Score:  {data.get('overall_score',0)}/100\n")
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
