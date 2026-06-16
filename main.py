from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
import anthropic
import os
import json
import tempfile
import base64
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from beautifier import generate_html, generate_pdf, BRAND

app = FastAPI(title="GEO API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai-syah.nl", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

class AuditRequest(BaseModel):
    url: str

class FullReportRequest(BaseModel):
    url: str
    email: str

def fetch_website(url: str) -> dict:
    if not url.startswith("http"):
        url = "https://" + url
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; GEOBot/1.0; +https://ai-syah.nl)"}
        response = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
        soup = BeautifulSoup(response.text, "html.parser")

        has_meta_description = bool(soup.find("meta", {"name": "description"}))
        has_og_tags = bool(soup.find("meta", {"property": "og:title"}))
        has_structured_data = bool(soup.find("script", {"type": "application/ld+json"}))
        has_h1 = bool(soup.find("h1"))
        title = soup.find("title")
        title_text = title.text if title else ""
        meta_desc = soup.find("meta", {"name": "description"})
        meta_desc_text = meta_desc.get("content", "") if meta_desc else ""

        brand_name = title_text.split("-")[0].strip() if title_text else url.replace("https://", "").replace("www.", "").split(".")[0].capitalize()

        robots_url = url.rstrip("/") + "/robots.txt"
        robots_content = ""
        try:
            robots_response = httpx.get(robots_url, timeout=5)
            robots_content = robots_response.text
        except:
            pass

        gptbot_allowed = "GPTBot" not in robots_content or "Allow: /" in robots_content
        claudebot_allowed = "ClaudeBot" not in robots_content or "Allow: /" in robots_content

        llms_url = url.rstrip("/") + "/llms.txt"
        has_llms_txt = False
        try:
            llms_response = httpx.get(llms_url, timeout=5)
            has_llms_txt = llms_response.status_code == 200
        except:
            pass

        for script in soup(["script", "style"]):
            script.decompose()
        page_text = soup.get_text()[:3000]

        return {
            "url": url, "brand_name": brand_name, "title": title_text,
            "meta_description": meta_desc_text,
            "has_meta_description": has_meta_description,
            "has_og_tags": has_og_tags,
            "has_structured_data": has_structured_data,
            "has_h1": has_h1, "has_llms_txt": has_llms_txt,
            "gptbot_allowed": gptbot_allowed, "claudebot_allowed": claudebot_allowed,
            "page_text": page_text, "status_code": response.status_code,
        }
    except Exception as e:
        brand_name = url.replace("https://", "").replace("www.", "").split(".")[0].capitalize()
        return {
            "url": url, "brand_name": brand_name, "error": str(e),
            "title": "", "meta_description": "",
            "has_meta_description": False, "has_og_tags": False,
            "has_structured_data": False, "has_h1": False,
            "has_llms_txt": False, "gptbot_allowed": True, "claudebot_allowed": True,
            "page_text": "", "status_code": 0,
        }


async def send_report_email(to_email: str, brand_name: str, geo_score: int, pdf_bytes: bytes) -> bool:
    """Verstuur het GEO rapport als PDF bijlage via Resend."""
    if not RESEND_API_KEY:
        print("⚠️  RESEND_API_KEY niet ingesteld — email wordt overgeslagen")
        return False

    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    safe_name = brand_name.replace(" ", "-").replace("|", "").strip("-")
    filename = f"GEO-Rapport-{safe_name}.pdf"

    if geo_score >= 70:
        score_label, score_color = "Goed", "#22c55e"
    elif geo_score >= 40:
        score_label, score_color = "Developing", "#f97316"
    else:
        score_label, score_color = "Kritiek", "#ef4444"

    html_body = f"""<!DOCTYPE html>
<html lang="nl"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:'Helvetica Neue',Arial,sans-serif;color:#e5e5e5;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#111;border-radius:12px;overflow:hidden;border:1px solid #222;">
        <tr>
          <td style="background:linear-gradient(135deg,#0a0a0a 0%,#1a1a1a 100%);padding:40px;text-align:center;border-bottom:1px solid #222;">
            <p style="margin:0 0 8px;font-size:11px;letter-spacing:4px;color:#00d4ff;text-transform:uppercase;">AI-SYAH.NL</p>
            <h1 style="margin:0;font-size:28px;font-weight:700;color:#fff;">GEO Intelligence Report</h1>
            <p style="margin:12px 0 0;color:#888;font-size:14px;">Uw persoonlijke AI-zichtbaarheidsanalyse is klaar</p>
          </td>
        </tr>
        <tr>
          <td style="padding:40px;text-align:center;">
            <p style="margin:0 0 8px;font-size:12px;letter-spacing:2px;color:#888;text-transform:uppercase;">GEO SCORE</p>
            <div style="display:inline-block;background:#1a1a1a;border:2px solid {score_color};border-radius:50%;width:100px;height:100px;line-height:100px;text-align:center;">
              <span style="font-size:36px;font-weight:800;color:{score_color};">{geo_score}</span>
            </div>
            <p style="margin:16px 0 0;font-size:16px;font-weight:600;color:{score_color};">{score_label}</p>
            <p style="margin:6px 0 0;color:#666;font-size:13px;">voor {brand_name}</p>
          </td>
        </tr>
        <tr><td style="padding:0 40px;"><hr style="border:none;border-top:1px solid #222;margin:0;"></td></tr>
        <tr>
          <td style="padding:32px 40px;">
            <p style="margin:0 0 16px;font-size:15px;line-height:1.7;color:#ccc;">
              Bedankt voor uw aanvraag. In de bijlage vindt u uw volledige <strong style="color:#fff;">GEO Visibility Report</strong> met:
            </p>
            <ul style="margin:0 0 24px;padding:0 0 0 20px;color:#aaa;font-size:14px;line-height:2;">
              <li>Score breakdown over 6 GEO-dimensies</li>
              <li>AI-platform analyse (ChatGPT, Gemini, Perplexity, e.a.)</li>
              <li>Gevonden issues met prioriteit</li>
              <li>Concreet actieplan met quick wins</li>
            </ul>
            <p style="margin:0;font-size:14px;color:#666;line-height:1.6;">
              Vragen? Neem contact op via <a href="mailto:info@ai-syah.nl" style="color:#00d4ff;text-decoration:none;">info@ai-syah.nl</a>
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 40px 40px;text-align:center;">
            <a href="https://ai-syah.nl" style="display:inline-block;background:#00d4ff;color:#000;font-weight:700;font-size:14px;padding:14px 32px;border-radius:6px;text-decoration:none;">Bekijk ai-syah.nl →</a>
          </td>
        </tr>
        <tr>
          <td style="background:#0d0d0d;padding:24px 40px;text-align:center;border-top:1px solid #1a1a1a;">
            <p style="margin:0;font-size:12px;color:#444;">© {datetime.now().year} AI-syah.nl · Dit rapport is 100% vertrouwelijk</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body></html>"""

    payload = {
        "from": "AI-syah.nl <rapport@ai-syah.nl>",
        "to": [to_email],
        "subject": f"🔍 Uw GEO Rapport voor {brand_name} — Score: {geo_score}/100",
        "html": html_body,
        "attachments": [{"filename": filename, "content": pdf_base64, "content_type": "application/pdf"}],
    }

    try:
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                json=payload, timeout=15,
            )
        if resp.status_code in (200, 201):
            print(f"✅ Email verstuurd naar {to_email}")
            return True
        else:
            print(f"❌ Resend fout {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Email versturen mislukt: {e}")
        return False


@app.get("/")
def root():
    return {"status": "GEO API is running", "version": "1.0.0"}


@app.post("/audit/basic")
async def basic_audit(request: AuditRequest):
    site_data = fetch_website(request.url)

    prompt = f"""Je bent een GEO (Generative Engine Optimization) expert. Analyseer deze website data en geef een nauwkeurige GEO audit.

Website: {site_data['url']}
Brand naam: {site_data['brand_name']}
Title: {site_data['title']}
Meta Description aanwezig: {site_data['has_meta_description']}
Meta Description: {site_data['meta_description'][:200] if site_data['meta_description'] else 'Geen'}
Open Graph tags: {site_data['has_og_tags']}
Structured Data (JSON-LD): {site_data['has_structured_data']}
H1 aanwezig: {site_data['has_h1']}
llms.txt aanwezig: {site_data['has_llms_txt']}
GPTBot toegestaan: {site_data['gptbot_allowed']}
ClaudeBot toegestaan: {site_data['claudebot_allowed']}
Pagina inhoud preview: {site_data['page_text'][:1000]}

Geef je antwoord ALLEEN als geldig JSON object zonder markdown of uitleg:
{{
  "url": "{site_data['url']}",
  "brand_name": "{site_data['brand_name']}",
  "date": "{datetime.now().isoformat()}",
  "geo_score": <getal 0-100 gebaseerd op echte data>,
  "executive_summary": "<2-3 zinnen samenvatting van de GEO status>",
  "scores": {{
    "ai_citability": <0-100>,
    "brand_authority": <0-100>,
    "content_eeat": <0-100>,
    "technical": <0-100>,
    "schema": <0-100>,
    "platform_optimization": <0-100>
  }},
  "platforms": {{
    "ChatGPT": <0-100>,
    "Gemini": <0-100>,
    "Perplexity": <0-100>,
    "Bing Copilot": <0-100>,
    "Google AIO": <0-100>
  }},
  "findings": [
    {{"severity": "critical", "title": "<titel>", "description": "<uitleg>"}},
    {{"severity": "critical", "title": "<titel>", "description": "<uitleg>"}},
    {{"severity": "high", "title": "<titel>", "description": "<uitleg>"}},
    {{"severity": "high", "title": "<titel>", "description": "<uitleg>"}},
    {{"severity": "medium", "title": "<titel>", "description": "<uitleg>"}},
    {{"severity": "medium", "title": "<titel>", "description": "<uitleg>"}}
  ],
  "quick_wins": ["<actie 1>", "<actie 2>", "<actie 3>"]
}}

Scoring richtlijnen (wees realistisch en streng):
- schema score: 0-10 als geen JSON-LD, 10-40 als basis aanwezig
- ai_citability: laag als geen llms.txt, geen structured data
- technical: basis punten voor werkende site, aftrekken voor ontbrekende meta
- geo_score is gewogen gemiddelde: ai_citability*0.25 + brand_authority*0.20 + content_eeat*0.20 + technical*0.15 + schema*0.10 + platform_optimization*0.10"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


@app.post("/audit/full")
async def full_audit(request: FullReportRequest):
    site_data = fetch_website(request.url)

    # ── STAP 1: Uitgebreide Claude analyse ──────────────────────────────────
    prompt = f"""Je bent een senior GEO expert. Analyseer deze website grondig en geef een volledig rapport als JSON.

Website: {site_data['url']}
Brand naam: {site_data['brand_name']}
Title: {site_data['title']}
Meta Description: {site_data['meta_description']}
Open Graph tags: {site_data['has_og_tags']}
Structured Data (JSON-LD): {site_data['has_structured_data']}
H1 aanwezig: {site_data['has_h1']}
llms.txt aanwezig: {site_data['has_llms_txt']}
GPTBot toegestaan: {site_data['gptbot_allowed']}
ClaudeBot toegestaan: {site_data['claudebot_allowed']}
Pagina inhoud (3000 tekens): {site_data['page_text'][:3000]}

Geef je antwoord ALLEEN als geldig JSON zonder markdown of uitleg:
{{
  "url": "{site_data['url']}",
  "brand_name": "{site_data['brand_name']}",
  "date": "{datetime.now().strftime('%Y-%m-%d')}",
  "geo_score": <0-100 gewogen score>,
  "executive_summary": "<3-4 zinnen specifieke samenvatting van sterktes en zwaktes op basis van de pagina-inhoud>",
  "company_profile": {{
    "description": "<2-3 zinnen over wat dit bedrijf doet, afgeleid van de pagina-inhoud>",
    "founded": "<oprichtingsjaar als bekend uit de tekst, anders leeglaten>",
    "location": "<locatie/stad als bekend uit de tekst, anders leeglaten>",
    "industry": "<branche/sector in 2-4 woorden>",
    "strengths": [
      "<concrete sterkte 1 specifiek voor dit bedrijf>",
      "<concrete sterkte 2>",
      "<concrete sterkte 3>"
    ],
    "critical_gaps": [
      "<kritieke gap 1 specifiek voor dit bedrijf>",
      "<kritieke gap 2>",
      "<kritieke gap 3>"
    ]
  }},
  "scores": {{
    "ai_citability": <0-100>,
    "brand_authority": <0-100>,
    "content_eeat": <0-100>,
    "technical": <0-100>,
    "schema": <0-100>,
    "platform_optimization": <0-100>
  }},
  "platforms": {{
    "Google AI Overviews": <0-100>,
    "ChatGPT": <0-100>,
    "Perplexity": <0-100>,
    "Gemini": <0-100>,
    "Bing Copilot": <0-100>
  }},
  "findings": [
    {{"severity": "critical", "title": "<specifieke titel>", "description": "<concrete uitleg met context van deze website>"}},
    {{"severity": "critical", "title": "<specifieke titel>", "description": "<concrete uitleg>"}},
    {{"severity": "high", "title": "<specifieke titel>", "description": "<concrete uitleg>"}},
    {{"severity": "high", "title": "<specifieke titel>", "description": "<concrete uitleg>"}},
    {{"severity": "medium", "title": "<specifieke titel>", "description": "<concrete uitleg>"}},
    {{"severity": "medium", "title": "<specifieke titel>", "description": "<concrete uitleg>"}},
    {{"severity": "low", "title": "<specifieke titel>", "description": "<concrete uitleg>"}}
  ],
  "quick_wins": [
    "<concrete actie 1 specifiek voor dit bedrijf>",
    "<concrete actie 2>",
    "<concrete actie 3>",
    "<concrete actie 4>",
    "<concrete actie 5>"
  ],
  "medium_term": [
    "<strategische actie 1>",
    "<strategische actie 2>",
    "<strategische actie 3>"
  ],
  "strategic": [
    "<langetermijn actie 1>",
    "<langetermijn actie 2>",
    "<langetermijn actie 3>"
  ],
  "crawler_access": {{
    "GPTBot": {{"platform": "ChatGPT", "status": "{'Allowed' if site_data['gptbot_allowed'] else 'Blocked'}", "recommendation": "{'Behoud toestemming' if site_data['gptbot_allowed'] else 'Voeg expliciete Allow toe in robots.txt'}"}},
    "ClaudeBot": {{"platform": "Claude", "status": "{'Allowed' if site_data['claudebot_allowed'] else 'Not Mentioned'}", "recommendation": "{'Behoud toestemming' if site_data['claudebot_allowed'] else 'Voeg expliciete Allow toe in robots.txt'}"}},
    "PerplexityBot": {{"platform": "Perplexity", "status": "Allowed", "recommendation": "Behoud toestemming"}},
    "Google-Extended": {{"platform": "Gemini", "status": "Allowed", "recommendation": "Behoud toestemming"}},
    "Bingbot": {{"platform": "Bing Copilot", "status": "Allowed", "recommendation": "Behoud toestemming"}}
  }}
}}

Scoring richtlijnen (wees realistisch en streng):
- schema: 0-10 als GEEN JSON-LD gevonden, 10-40 als basis aanwezig, 40+ als uitgebreid
- ai_citability: max 30 als geen llms.txt, max 50 als geen structured data
- technical: 40 basis voor werkende site, -10 per ontbrekend element (meta, h1, OG)
- geo_score = ai_citability*0.25 + brand_authority*0.20 + content_eeat*0.20 + technical*0.15 + schema*0.10 + platform_optimization*0.10
- Wees specifiek: vermijd generieke tekst, gebruik de echte bedrijfsnaam en context uit de pagina"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    report_data = json.loads(text.strip())

    # ── STAP 2: Bouw beautifier_data op ─────────────────────────────────────
    scores       = report_data.get("scores", {})
    platforms_raw = report_data.get("platforms", {})
    crawlers_raw  = report_data.get("crawler_access", {})
    quick_wins   = report_data.get("quick_wins", [])
    medium_term  = report_data.get("medium_term", [])
    strategic    = report_data.get("strategic", [])
    findings_raw = report_data.get("findings", [])
    overall      = report_data.get("geo_score", 0)
    company_profile = report_data.get("company_profile", {})

    n_critical_high = len([f for f in findings_raw if f.get("severity","").lower() in ["critical","high"]])

    beautifier_data = {
        "company_name":    report_data.get("brand_name", site_data["brand_name"]),
        "url":             request.url,
        "audit_date":      datetime.now().strftime("%B %d, %Y"),
        "overall_score":   overall,
        "company_tagline": report_data.get("executive_summary", "")[:120],
        "stats": [
            {"value": str(overall),          "label": "GEO Score"},
            {"value": str(n_critical_high),  "label": "Kritieke Issues"},
            {"value": str(len(quick_wins)),  "label": "Quick Wins"},
            {"value": datetime.now().strftime("%Y"), "label": "Audit Jaar"},
        ],
        "executive_summary": report_data.get("executive_summary", ""),

        # ← Dit veld was leeg — nu gevuld vanuit Claude
        "company_profile": {
            "description":   company_profile.get("description", report_data.get("executive_summary", "")),
            "founded":       company_profile.get("founded", ""),
            "location":      company_profile.get("location", ""),
            "industry":      company_profile.get("industry", ""),
            "strengths":     company_profile.get("strengths", []),
            "critical_gaps": company_profile.get("critical_gaps", []),
        },

        "dimensions": [
            {"name": "AI Citability & Visibility",  "description": "Kunnen AI-platforms je content vinden?",     "score": scores.get("ai_citability", 0),        "weight": "25%", "weighted_score": str(round(scores.get("ai_citability", 0) * 0.25, 1))},
            {"name": "Brand Authority Signals",      "description": "Externe signalen die valideren wie je bent", "score": scores.get("brand_authority", 0),      "weight": "20%", "weighted_score": str(round(scores.get("brand_authority", 0) * 0.20, 1))},
            {"name": "Content Quality & E-E-A-T",   "description": "Diepgang en betrouwbaarheid van content",    "score": scores.get("content_eeat", 0),         "weight": "20%", "weighted_score": str(round(scores.get("content_eeat", 0) * 0.20, 1))},
            {"name": "Technical Foundations",        "description": "Technische basis voor AI-toegankelijkheid",  "score": scores.get("technical", 0),            "weight": "15%", "weighted_score": str(round(scores.get("technical", 0) * 0.15, 1))},
            {"name": "Schema & Structured Data",     "description": "Gestructureerde data voor zoekmachines",    "score": scores.get("schema", 0),               "weight": "10%", "weighted_score": str(round(scores.get("schema", 0) * 0.10, 1))},
            {"name": "Platform Optimization",        "description": "Optimalisatie per AI-platform",             "score": scores.get("platform_optimization", 0),"weight": "10%", "weighted_score": str(round(scores.get("platform_optimization", 0) * 0.10, 1))},
        ],
        "platforms": [{"name": k, "score": v} for k, v in platforms_raw.items()],
        "crawlers": [
            {"name": k, "platform": v.get("platform",""), "status": v.get("status",""), "recommendation": v.get("recommendation","")}
            for k, v in crawlers_raw.items()
        ],
        "findings": [
            {"severity": f.get("severity","LOW").upper(), "title": f.get("title",""), "description": f.get("description","")}
            for f in findings_raw
        ],
        "action_plan": {
            "quick_wins":  [{"title": a, "description": "", "time_estimate": "30 min"} if isinstance(a, str) else a for a in quick_wins],
            "medium_term": [{"title": a, "description": "", "time_estimate": "1 week"} if isinstance(a, str) else a for a in medium_term],
            "strategic":   [{"title": a, "description": "", "time_estimate": "1 maand"} if isinstance(a, str) else a for a in strategic],
        },
        "methodology": f"Deze GEO audit analyseerde {request.url} op zes gewogen dimensies.",
    }

    # ── STAP 3: Genereer PDF ─────────────────────────────────────────────────
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        pdf_path = tmp.name

    html = generate_html(beautifier_data)
    generate_pdf(html, pdf_path)

    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    os.unlink(pdf_path)

    # ── STAP 4: Verstuur email ───────────────────────────────────────────────
    email_sent = await send_report_email(
        to_email=request.email,
        brand_name=beautifier_data["company_name"],
        geo_score=overall,
        pdf_bytes=pdf_bytes,
    )

    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

    return {
        "report":     report_data,
        "pdf_base64": pdf_base64,
        "url":        request.url,
        "email_sent": email_sent,
    }
