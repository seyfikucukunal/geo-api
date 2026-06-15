#!/usr/bin/env python3
"""
AI-syah.nl — GEO Audit PDF Generator (HTML/CSS via xhtml2pdf)
Professional dark-themed report.
"""

import sys
import json
import os
from datetime import datetime

try:
    from xhtml2pdf import pisa
except ImportError:
    print("ERROR: pip install xhtml2pdf")
    sys.exit(1)


def score_color(s):
    if s >= 70: return "#22c55e"
    if s >= 40: return "#eab308"
    return "#ef4444"

def score_label(s):
    if s >= 70: return "Goed"
    if s >= 40: return "Verbetering nodig"
    return "Kritiek"

def severity_color(sev):
    sev = sev.lower()
    if sev == "critical": return "#ef4444"
    if sev == "high":     return "#f97316"
    if sev == "medium":   return "#eab308"
    return "#22d3ee"

def severity_label(sev):
    sev = sev.lower()
    if sev == "critical": return "KRITIEK"
    if sev == "high":     return "HOOG"
    if sev == "medium":   return "MEDIUM"
    return "LAAG"

def render_score_bar(label, value, weight=""):
    color = score_color(value)
    pct = value
    return f"""
    <tr>
        <td style="color:#a1a1aa; font-size:8pt; padding:3pt 6pt;">{label}</td>
        <td style="color:{color}; font-weight:bold; font-size:8pt; padding:3pt 6pt; text-align:center;">{value}/100</td>
        <td style="color:#52525b; font-size:7pt; padding:3pt 6pt; text-align:center;">{weight}</td>
        <td style="padding:3pt 6pt;">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="background:#27272a; height:6pt; border-radius:3pt;">
                        <table width="{pct}%" cellpadding="0" cellspacing="0">
                            <tr><td style="background:{color}; height:6pt; border-radius:3pt;">&nbsp;</td></tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
        <td style="color:{color}; font-size:8pt; padding:3pt 6pt;">{score_label(value)}</td>
    </tr>
    """

def render_finding(f):
    sev = f.get("severity", "medium")
    col = severity_color(sev)
    lab = severity_label(sev)
    title = f.get("title", "")
    desc = f.get("description", "")
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:3pt;">
        <tr>
            <td width="4pt" style="background:{col};">&nbsp;</td>
            <td style="background:#18181b; padding:6pt 8pt;">
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td>
                            <span style="background:{col}20; color:{col}; font-size:6.5pt; font-weight:bold; padding:1pt 5pt; border:1pt solid {col}40;">{lab}</span>
                            &nbsp;
                            <span style="color:#ffffff; font-size:9pt; font-weight:bold;">{title}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="color:#71717a; font-size:8pt; padding-top:3pt; line-height:1.5;">{desc}</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    """

def render_action(i, text, color):
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:1pt;">
        <tr>
            <td style="background:#18181b; padding:4pt 8pt; border-bottom:0.3pt solid #27272a;">
                <span style="color:{color}; font-weight:bold; font-size:9pt;">{i:02d}&nbsp;&nbsp;</span>
                <span style="color:#a1a1aa; font-size:8.5pt;">{text}</span>
            </td>
        </tr>
    </table>
    """

def generate_html(data):
    url         = data.get("url", "")
    brand       = data.get("brand_name", "Website")
    date_str    = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    geo_score   = data.get("geo_score", 0)
    scores      = data.get("scores", {})
    platforms   = data.get("platforms", {})
    findings    = data.get("findings", [])
    quick_wins  = data.get("quick_wins", [])
    medium_term = data.get("medium_term", [])
    strategic   = data.get("strategic", [])
    summary     = data.get("executive_summary", "")
    crawlers    = data.get("crawler_access", {})

    score_col = score_color(geo_score)
    score_lbl = score_label(geo_score)

    score_items = [
        ("AI Citability & Visibility", scores.get("ai_citability", 0), "25%"),
        ("Brand Authority Signals",    scores.get("brand_authority", 0), "20%"),
        ("Content Quality & E-E-A-T",  scores.get("content_eeat", 0), "20%"),
        ("Technical Foundations",      scores.get("technical", 0), "15%"),
        ("Structured Data",            scores.get("schema", 0), "10%"),
        ("Platform Optimization",      scores.get("platform_optimization", 0), "10%"),
    ]

    score_rows = "".join(render_score_bar(l, v, w) for l, v, w in score_items)

    platform_rows = ""
    for name, val in platforms.items():
        col = score_color(val)
        platform_rows += f"""
        <tr>
            <td style="color:#a1a1aa; font-size:8pt; padding:3pt 6pt; width:35%;">{name}</td>
            <td style="padding:3pt 6pt;">
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td style="background:#27272a; height:8pt;">
                            <table width="{val}%" cellpadding="0" cellspacing="0">
                                <tr><td style="background:{col}; height:8pt;">&nbsp;</td></tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
            <td style="color:{col}; font-weight:bold; font-size:8pt; padding:3pt 6pt; width:15%; text-align:right;">{val}/100</td>
        </tr>
        """

    findings_html = "".join(render_finding(f) for f in findings)

    crit = sum(1 for f in findings if f.get("severity","").lower() == "critical")
    high = sum(1 for f in findings if f.get("severity","").lower() == "high")
    med  = sum(1 for f in findings if f.get("severity","").lower() == "medium")
    low  = sum(1 for f in findings if f.get("severity","").lower() == "low")

    qw_html = "".join(render_action(i, a if isinstance(a,str) else a.get("action",""), "#22c55e")
                      for i, a in enumerate(quick_wins or ["Voeg llms.txt toe"], 1))
    mt_html = "".join(render_action(i, a if isinstance(a,str) else a.get("action",""), "#eab308")
                      for i, a in enumerate(medium_term or ["Structured data uitbreiden"], 1))
    st_html = "".join(render_action(i, a if isinstance(a,str) else a.get("action",""), "#22d3ee")
                      for i, a in enumerate(strategic or ["Brand entity opbouwen"], 1))

    crawler_rows = ""
    for name, info in crawlers.items():
        if isinstance(info, dict):
            status = info.get("status", "Unknown")
            plat   = info.get("platform", "")
            rec    = info.get("recommendation", "")
        else:
            status, plat, rec = str(info), "", ""
        status_col = "#22c55e" if "allow" in status.lower() else "#ef4444"
        crawler_rows += f"""
        <tr>
            <td style="color:#a1a1aa; font-size:8pt; padding:4pt 6pt;">{name}</td>
            <td style="color:#a1a1aa; font-size:8pt; padding:4pt 6pt;">{plat}</td>
            <td style="color:{status_col}; font-weight:bold; font-size:8pt; padding:4pt 6pt;">{status}</td>
            <td style="color:#71717a; font-size:8pt; padding:4pt 6pt;">{rec}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @page {{ size: A4; margin: 0; }}
  body {{ font-family: Helvetica, Arial, sans-serif; background: #000000; color: #a1a1aa; margin: 0; padding: 0; }}
  .page {{ background: #000000; padding: 18mm 20mm 16mm; page-break-after: always; }}
  .cover {{ background: #000000; padding: 0; page-break-after: always; min-height: 297mm; }}
  .th {{ background: #27272a; color: #22d3ee; font-size: 7.5pt; font-weight: bold; padding: 4pt 6pt; text-align: left; }}
  .td {{ background: #18181b; color: #a1a1aa; font-size: 8pt; padding: 4pt 6pt; border-bottom: 0.3pt solid #27272a; }}
  .td-alt {{ background: #111111; }}
</style>
</head>
<body>

<!-- COVER -->
<div class="cover">
  <!-- Cyan top bar -->
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td style="background:#22d3ee; height:10mm;">&nbsp;</td></tr>
  </table>

  <table width="100%" cellpadding="0" cellspacing="0" style="padding:12mm 20mm;">
    <tr>
      <td style="padding:0 20mm;">
        <p style="color:#22d3ee; font-size:12pt; font-weight:bold; margin:8mm 0 1mm;">AI-syah.nl</p>
        <p style="color:#52525b; font-size:8pt; margin:0 0 6mm;">Generative Engine Optimization</p>
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr><td style="background:#3f3f46; height:0.3pt;">&nbsp;</td></tr>
        </table>
        <p style="color:#22d3ee; font-size:8pt; font-weight:bold; letter-spacing:2pt; margin:10mm 0 4mm;">GEO AUDIT RAPPORT</p>
        <p style="color:#ffffff; font-size:28pt; font-weight:bold; margin:0 0 3mm; line-height:1.1;">{brand}</p>
        <p style="color:#52525b; font-size:10pt; margin:0 0 10mm;">{url}</p>

        <!-- Score circle using table -->
        <table cellpadding="0" cellspacing="0" style="margin-bottom:10mm;">
          <tr>
            <td>
              <table cellpadding="0" cellspacing="0" style="border:4pt solid {score_col}; border-radius:50%; width:40mm; height:40mm; text-align:center;">
                <tr><td style="text-align:center; vertical-align:middle; padding:8mm;">
                  <p style="color:{score_col}; font-size:28pt; font-weight:bold; margin:0; line-height:1;">{geo_score}</p>
                  <p style="color:#52525b; font-size:8pt; margin:0;">/100</p>
                </td></tr>
              </table>
              <p style="color:{score_col}; font-size:9pt; font-weight:bold; text-align:center; margin:2mm 0;">{score_lbl}</p>
              <p style="color:#52525b; font-size:7pt; text-align:center; margin:0;">{date_str}</p>
            </td>
            <td width="10mm">&nbsp;</td>
            <td style="vertical-align:top;">
              <p style="color:#52525b; font-size:7pt; font-weight:bold; letter-spacing:1.5pt; margin:0 0 4mm;">SCORE OVERZICHT</p>
              <table width="100%" cellpadding="0" cellspacing="2">
                {score_rows}
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>

  <!-- Bottom bar -->
  <table width="100%" cellpadding="0" cellspacing="0" style="position:absolute; bottom:0;">
    <tr><td style="background:#18181b; padding:3mm 20mm;">
      <p style="color:#3f3f46; font-size:7pt; margin:0;">Vertrouwelijk — AI-syah.nl GEO Audit Rapport &nbsp;|&nbsp; {datetime.now().strftime("%d %B %Y")}</p>
    </td></tr>
  </table>
</div>

<!-- PAGE 2: SAMENVATTING -->
<div class="page">
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:5mm; border-bottom:0.3pt solid #27272a; padding-bottom:3mm;">
    <tr>
      <td style="color:#22d3ee; font-size:8pt; font-weight:bold;">AI-syah.nl</td>
      <td style="color:#3f3f46; font-size:8pt;">&nbsp;·&nbsp;</td>
      <td style="color:#52525b; font-size:8pt;">GEO Audit Rapport — {brand}</td>
    </tr>
  </table>

  <p style="color:#ffffff; font-size:16pt; font-weight:bold; margin:0 0 1mm;">Executive Summary</p>
  <p style="color:#52525b; font-size:8pt; margin:0 0 5mm;">Overzicht van de GEO-status en prioriteiten</p>
  <p style="color:#a1a1aa; font-size:9pt; line-height:1.6; margin:0 0 6mm;">{summary}</p>

  <p style="color:#22d3ee; font-size:7pt; font-weight:bold; letter-spacing:1.5pt; margin:0 0 3mm;">● SCORE BREAKDOWN</p>
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:6mm;">
    <tr>
      <td class="th" style="width:38%;">Component</td>
      <td class="th" style="width:12%; text-align:center;">Score</td>
      <td class="th" style="width:10%; text-align:center;">Gewicht</td>
      <td class="th" style="width:20%;">Voortgang</td>
      <td class="th">Status</td>
    </tr>
    {score_rows}
    <tr>
      <td style="background:#27272a; color:#ffffff; font-weight:bold; font-size:8pt; padding:4pt 6pt;">OVERALL GEO SCORE</td>
      <td style="background:#27272a; color:{score_col}; font-weight:bold; font-size:8pt; padding:4pt 6pt; text-align:center;">{geo_score}/100</td>
      <td style="background:#27272a; color:#52525b; font-size:7pt; padding:4pt 6pt; text-align:center;">100%</td>
      <td style="background:#27272a; padding:4pt 6pt;"></td>
      <td style="background:#27272a; color:{score_col}; font-weight:bold; font-size:8pt; padding:4pt 6pt;">{score_lbl}</td>
    </tr>
  </table>

  <p style="color:#22d3ee; font-size:7pt; font-weight:bold; letter-spacing:1.5pt; margin:0 0 3mm;">● AI PLATFORM ZICHTBAARHEID</p>
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:6mm;">
    {platform_rows}
  </table>

  <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:6mm; border-top:0.3pt solid #27272a; padding-top:3mm;">
    <tr>
      <td style="color:#3f3f46; font-size:7pt;">AI-syah.nl — Vertrouwelijk</td>
      <td style="color:#3f3f46; font-size:7pt; text-align:right;">Gegenereerd op {datetime.now().strftime("%d %B %Y")}</td>
    </tr>
  </table>
</div>

<!-- PAGE 3: BEVINDINGEN -->
<div class="page">
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:5mm; border-bottom:0.3pt solid #27272a; padding-bottom:3mm;">
    <tr>
      <td style="color:#22d3ee; font-size:8pt; font-weight:bold;">AI-syah.nl</td>
      <td style="color:#3f3f46; font-size:8pt;">&nbsp;·&nbsp;</td>
      <td style="color:#52525b; font-size:8pt;">Bevindingen</td>
    </tr>
  </table>

  <p style="color:#ffffff; font-size:16pt; font-weight:bold; margin:0 0 1mm;">Bevindingen</p>
  <p style="color:#52525b; font-size:8pt; margin:0 0 5mm;">Geïdentificeerde problemen gesorteerd op prioriteit</p>

  <!-- Summary badges -->
  <table width="100%" cellpadding="0" cellspacing="4" style="margin-bottom:5mm;">
    <tr>
      <td style="background:#18181b; text-align:center; padding:5mm; border:0.3pt solid #27272a;">
        <p style="color:#ef4444; font-size:18pt; font-weight:bold; margin:0; line-height:1;">{crit}</p>
        <p style="color:#ef4444; font-size:7pt; margin:1mm 0 0;">Kritiek</p>
      </td>
      <td width="3mm">&nbsp;</td>
      <td style="background:#18181b; text-align:center; padding:5mm; border:0.3pt solid #27272a;">
        <p style="color:#f97316; font-size:18pt; font-weight:bold; margin:0; line-height:1;">{high}</p>
        <p style="color:#f97316; font-size:7pt; margin:1mm 0 0;">Hoog</p>
      </td>
      <td width="3mm">&nbsp;</td>
      <td style="background:#18181b; text-align:center; padding:5mm; border:0.3pt solid #27272a;">
        <p style="color:#eab308; font-size:18pt; font-weight:bold; margin:0; line-height:1;">{med}</p>
        <p style="color:#eab308; font-size:7pt; margin:1mm 0 0;">Medium</p>
      </td>
      <td width="3mm">&nbsp;</td>
      <td style="background:#18181b; text-align:center; padding:5mm; border:0.3pt solid #27272a;">
        <p style="color:#22d3ee; font-size:18pt; font-weight:bold; margin:0; line-height:1;">{low}</p>
        <p style="color:#22d3ee; font-size:7pt; margin:1mm 0 0;">Laag</p>
      </td>
    </tr>
  </table>

  {findings_html}

  <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:6mm; border-top:0.3pt solid #27272a; padding-top:3mm;">
    <tr>
      <td style="color:#3f3f46; font-size:7pt;">AI-syah.nl — Vertrouwelijk</td>
      <td style="color:#3f3f46; font-size:7pt; text-align:right;">Gegenereerd op {datetime.now().strftime("%d %B %Y")}</td>
    </tr>
  </table>
</div>

<!-- PAGE 4: ACTIEPLAN -->
<div class="page">
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:5mm; border-bottom:0.3pt solid #27272a; padding-bottom:3mm;">
    <tr>
      <td style="color:#22d3ee; font-size:8pt; font-weight:bold;">AI-syah.nl</td>
      <td style="color:#3f3f46; font-size:8pt;">&nbsp;·&nbsp;</td>
      <td style="color:#52525b; font-size:8pt;">Geprioriteerd Actieplan</td>
    </tr>
  </table>

  <p style="color:#ffffff; font-size:16pt; font-weight:bold; margin:0 0 1mm;">Geprioriteerd Actieplan</p>
  <p style="color:#52525b; font-size:8pt; margin:0 0 5mm;">Concrete stappen om je GEO score te verbeteren</p>

  <!-- Quick Wins -->
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:1pt;">
    <tr><td style="background:#27272a; padding:4mm 6mm; border-left:4pt solid #22c55e;">
      <p style="color:#22c55e; font-size:10pt; font-weight:bold; margin:0;">⚡ Quick Wins — Deze Week</p>
      <p style="color:#52525b; font-size:7.5pt; margin:0;">Hoge impact, weinig inspanning</p>
    </td></tr>
  </table>
  {qw_html}

  <p style="margin:4mm 0 0;">&nbsp;</p>

  <!-- Deze Maand -->
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:1pt;">
    <tr><td style="background:#27272a; padding:4mm 6mm; border-left:4pt solid #eab308;">
      <p style="color:#eab308; font-size:10pt; font-weight:bold; margin:0;">📈 Verbeteringen Deze Maand</p>
      <p style="color:#52525b; font-size:7.5pt; margin:0;">Significante impact, matige inspanning</p>
    </td></tr>
  </table>
  {mt_html}

  <p style="margin:4mm 0 0;">&nbsp;</p>

  <!-- Strategisch -->
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:1pt;">
    <tr><td style="background:#27272a; padding:4mm 6mm; border-left:4pt solid #22d3ee;">
      <p style="color:#22d3ee; font-size:10pt; font-weight:bold; margin:0;">🚀 Strategische Initiatieven</p>
      <p style="color:#52525b; font-size:7.5pt; margin:0;">Lange termijn concurrentievoordeel</p>
    </td></tr>
  </table>
  {st_html}

  <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:6mm; border-top:0.3pt solid #27272a; padding-top:3mm;">
    <tr>
      <td style="color:#3f3f46; font-size:7pt;">AI-syah.nl — Vertrouwelijk</td>
      <td style="color:#3f3f46; font-size:7pt; text-align:right;">Gegenereerd op {datetime.now().strftime("%d %B %Y")}</td>
    </tr>
  </table>
</div>

<!-- PAGE 5: CRAWLERS + METHODOLOGIE -->
<div class="page">
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:5mm; border-bottom:0.3pt solid #27272a; padding-bottom:3mm;">
    <tr>
      <td style="color:#22d3ee; font-size:8pt; font-weight:bold;">AI-syah.nl</td>
      <td style="color:#3f3f46; font-size:8pt;">&nbsp;·&nbsp;</td>
      <td style="color:#52525b; font-size:8pt;">AI Crawlers &amp; Methodologie</td>
    </tr>
  </table>

  <p style="color:#ffffff; font-size:16pt; font-weight:bold; margin:0 0 1mm;">AI Crawler Toegang</p>
  <p style="color:#52525b; font-size:8pt; margin:0 0 5mm;">Status van AI-crawlers op jouw website</p>

  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:8mm;">
    <tr>
      <td class="th" style="width:20%;">Crawler</td>
      <td class="th" style="width:20%;">Platform</td>
      <td class="th" style="width:15%;">Status</td>
      <td class="th">Aanbeveling</td>
    </tr>
    {crawler_rows}
  </table>

  <p style="color:#ffffff; font-size:16pt; font-weight:bold; margin:0 0 1mm;">Methodologie</p>
  <p style="color:#71717a; font-size:8.5pt; line-height:1.6; margin:0 0 4mm;">
    Audit uitgevoerd op {date_str} voor {url}.
    De analyse evalueert zes dimensies: AI Citability &amp; Visibility (25%),
    Brand Authority (20%), Content E-E-A-T (20%), Technical Foundations (15%),
    Structured Data (10%) en Platform Optimization (10%).
  </p>

  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:6mm;">
    <tr>
      <td class="th" style="width:20%;">Term</td>
      <td class="th">Definitie</td>
    </tr>
    <tr><td class="td">GEO</td><td class="td">Generative Engine Optimization — optimaliseren voor AI-zoekcitatie</td></tr>
    <tr><td class="td td-alt">E-E-A-T</td><td class="td td-alt">Experience, Expertise, Authoritativeness, Trustworthiness</td></tr>
    <tr><td class="td">llms.txt</td><td class="td">Standaard bestand dat AI-systemen begeleidt over site-inhoud</td></tr>
    <tr><td class="td td-alt">JSON-LD</td><td class="td td-alt">Gestructureerde data formaat voor AI-begrip</td></tr>
    <tr><td class="td">IndexNow</td><td class="td">Protocol voor directe notificatie van zoekmachines</td></tr>
  </table>

  <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:6mm; border-top:0.3pt solid #27272a; padding-top:3mm;">
    <tr>
      <td style="color:#3f3f46; font-size:7pt;">Dit rapport is gegenereerd door AI-syah.nl — specialist in Generative Engine Optimization.</td>
    </tr>
  </table>
</div>

</body>
</html>"""


def generate_report(data, output_path="GEO-RAPPORT.pdf"):
    html_content = generate_html(data)
    with open(output_path, "wb") as f:
        pisa.CreatePDF(html_content, dest=f)
    return output_path


if __name__ == "__main__":
    sample = {
        "url": "https://fues.nl",
        "brand_name": "FUES",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "geo_score": 28,
        "executive_summary": (
            "FUES heeft een sterke certificeringenportefeuille maar scoort kritiek laag op GEO "
            "vanwege ontbrekende schema markup en llms.txt. De website heeft uitstekende technische "
            "fundamenten maar mist cruciale AI-optimalisaties die nodig zijn voor zichtbaarheid "
            "in ChatGPT, Gemini en Perplexity."
        ),
        "scores": {
            "ai_citability": 28, "brand_authority": 25,
            "content_eeat": 35, "technical": 40,
            "schema": 3, "platform_optimization": 22,
        },
        "platforms": {
            "Google AI Overviews": 35, "ChatGPT": 25,
            "Perplexity": 28, "Gemini": 35, "Bing Copilot": 25,
        },
        "findings": [
            {"severity": "critical", "title": "Geen Schema Markup",
             "description": "Geen JSON-LD structured data gevonden. AI-modellen kunnen entiteiten niet herkennen."},
            {"severity": "critical", "title": "Geen llms.txt",
             "description": "Het llms.txt bestand ontbreekt waardoor AI-crawlers geen context hebben."},
            {"severity": "high", "title": "Geen meta descriptions",
             "description": "Geen van de pagina's heeft een meta description."},
            {"severity": "high", "title": "Open Graph ontbreekt",
             "description": "Geen OG tags waardoor sociale deling en AI-preview generatie beperkt is."},
            {"severity": "medium", "title": "Beperkte content diepte",
             "description": "Pagina's bevatten te weinig diepgaande content voor AI citability."},
        ],
        "quick_wins": [
            "Voeg llms.txt toe aan de website root",
            "Implementeer LocalBusiness JSON-LD schema op homepage",
            "Configureer meta descriptions voor alle pagina's",
            "Activeer Open Graph tags",
            "Voeg KvK en AGB code toe aan footer",
        ],
        "medium_term": [
            "FAQ pagina met FAQPage schema markup aanmaken",
            "Teamprofielen uitbreiden met kwalificaties",
            "Blog/kennisbank lanceren met sector-specifieke content",
        ],
        "strategic": [
            "Brand entity presence opbouwen via Wikidata",
            "Thought leadership content strategie ontwikkelen",
            "Review pipeline opzetten",
        ],
        "crawler_access": {
            "GPTBot": {"platform": "ChatGPT", "status": "Allowed", "recommendation": "Behoud toestemming"},
            "ClaudeBot": {"platform": "Claude", "status": "Allowed", "recommendation": "Behoud toestemming"},
            "PerplexityBot": {"platform": "Perplexity", "status": "Allowed", "recommendation": "Behoud toestemming"},
            "Google-Extended": {"platform": "Gemini", "status": "Allowed", "recommendation": "Behoud toestemming"},
            "Bingbot": {"platform": "Bing Copilot", "status": "Allowed", "recommendation": "Behoud toestemming"},
        },
    }
    out = generate_report(sample, "GEO-RAPPORT-sample.pdf")
    print(f"Rapport gegenereerd: {out}")