from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
import anthropic
import os
import json
import tempfile
import base64
import sys
import sqlite3
from datetime import datetime
from contextlib import contextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from beautifier import generate_html, generate_pdf, BRAND

app = FastAPI(title="GEO API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai-syah.nl", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Clients & Keys ───────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
RESEND_API_KEY   = os.environ.get("RESEND_API_KEY")
MOLLIE_API_KEY   = os.environ.get("MOLLIE_API_KEY")
BASE_URL         = os.environ.get("BASE_URL", "https://geo-api-eqn1.onrender.com")
FRONTEND_URL     = os.environ.get("FRONTEND_URL", "https://ai-syah.nl")

# ── Prijzen ──────────────────────────────────────────────────────────────────
PRICE_FIRST      = "9.99"   # eerste rapport
PRICE_EXTRA      = "49.99"  # extra losse scan
PRICE_SUB_MONTH  = "29.99"  # maandelijks abonnement

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE (SQLite)
# ─────────────────────────────────────────────────────────────────────────────
DB_PATH = os.environ.get("DB_PATH", "/tmp/geo_database.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Gebruikers tabel
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT UNIQUE NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # Orders tabel (eenmalige betalingen)
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            mollie_id       TEXT UNIQUE NOT NULL,
            email           TEXT NOT NULL,
            url             TEXT NOT NULL,
            amount          TEXT NOT NULL,
            status          TEXT DEFAULT 'open',
            report_sent     INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now')),
            paid_at         TEXT
        )
    """)

    # Subscriptions tabel
    c.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            mollie_customer_id  TEXT NOT NULL,
            mollie_sub_id       TEXT,
            email               TEXT NOT NULL,
            status              TEXT DEFAULT 'pending',
            created_at          TEXT DEFAULT (datetime('now')),
            next_payment_at     TEXT
        )
    """)

    # Rapport geschiedenis tabel
    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT NOT NULL,
            url         TEXT NOT NULL,
            geo_score   INTEGER,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()

init_db()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def count_user_reports(email: str) -> int:
    """Tel hoeveel betaalde rapporten dit emailadres al heeft."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM reports WHERE email = ?", (email,)
        ).fetchone()
    return row["cnt"] if row else 0

def save_report(email: str, url: str, geo_score: int):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO reports (email, url, geo_score) VALUES (?, ?, ?)",
            (email, url, geo_score)
        )
        conn.commit()

# ─────────────────────────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────────────────────────────────────
class AuditRequest(BaseModel):
    url: str

class FullReportRequest(BaseModel):
    url: str
    email: str

class PaymentRequest(BaseModel):
    email: str
    url: str
    plan: str  # "single" of "subscription"

class CheckReportRequest(BaseModel):
    email: str

# ─────────────────────────────────────────────────────────────────────────────
# WEBSITE FETCHER
# ─────────────────────────────────────────────────────────────────────────────
def fetch_website(url: str) -> dict:
    if not url.startswith("http"):
        url = "https://" + url
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; GEOBot/1.0; +https://ai-syah.nl)"}
        response = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
        soup = BeautifulSoup(response.text, "html.parser")

        has_meta_description = bool(soup.find("meta", {"name": "description"}))
        has_og_tags          = bool(soup.find("meta", {"property": "og:title"}))
        has_structured_data  = bool(soup.find("script", {"type": "application/ld+json"}))
        has_h1               = bool(soup.find("h1"))
        title                = soup.find("title")
        title_text           = title.text if title else ""
        meta_desc            = soup.find("meta", {"name": "description"})
        meta_desc_text       = meta_desc.get("content", "") if meta_desc else ""
        brand_name           = title_text.split("-")[0].strip() if title_text else \
                               url.replace("https://", "").replace("www.", "").split(".")[0].capitalize()

        robots_url     = url.rstrip("/") + "/robots.txt"
        robots_content = ""
        try:
            robots_response = httpx.get(robots_url, timeout=5)
            robots_content  = robots_response.text
        except:
            pass

        gptbot_allowed   = "GPTBot" not in robots_content or "Allow: /" in robots_content
        claudebot_allowed = "ClaudeBot" not in robots_content or "Allow: /" in robots_content

        llms_url    = url.rstrip("/") + "/llms.txt"
        has_llms_txt = False
        try:
            llms_response = httpx.get(llms_url, timeout=5)
            has_llms_txt  = llms_response.status_code == 200
        except:
            pass

        for script in soup(["script", "style"]):
            script.decompose()
        page_text = soup.get_text()[:3000]

        return {
            "url": url, "brand_name": brand_name, "title": title_text,
            "meta_description": meta_desc_text,
            "has_meta_description": has_meta_description,
            "has_og_tags": has_og_tags, "has_structured_data": has_structured_data,
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

# ─────────────────────────────────────────────────────────────────────────────
# EMAIL HELPER
# ─────────────────────────────────────────────────────────────────────────────
async def send_report_email(to_email: str, brand_name: str, geo_score: int, pdf_bytes: bytes) -> bool:
    if not RESEND_API_KEY:
        print("⚠️  RESEND_API_KEY niet ingesteld — email wordt overgeslagen")
        return False

    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    safe_name  = brand_name.replace(" ", "-").replace("|", "").strip("-")
    filename   = f"GEO-Rapport-{safe_name}.pdf"

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
        "to":   [to_email],
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

# ─────────────────────────────────────────────────────────────────────────────
# RAPPORT GENERATOR (shared logic)
# ─────────────────────────────────────────────────────────────────────────────
async def generate_and_send_report(email: str, url: str) -> dict:
    site_data = fetch_website(url)

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
  "executive_summary": "<3-4 zinnen specifieke samenvatting>",
  "company_profile": {{
    "description": "<2-3 zinnen over wat dit bedrijf doet>",
    "founded": "<oprichtingsjaar of leeg>",
    "location": "<locatie of leeg>",
    "industry": "<branche in 2-4 woorden>",
    "strengths": ["<sterkte 1>", "<sterkte 2>", "<sterkte 3>"],
    "critical_gaps": ["<gap 1>", "<gap 2>", "<gap 3>"]
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
    {{"severity": "critical", "title": "<titel>", "description": "<uitleg>"}},
    {{"severity": "critical", "title": "<titel>", "description": "<uitleg>"}},
    {{"severity": "high", "title": "<titel>", "description": "<uitleg>"}},
    {{"severity": "high", "title": "<titel>", "description": "<uitleg>"}},
    {{"severity": "medium", "title": "<titel>", "description": "<uitleg>"}},
    {{"severity": "medium", "title": "<titel>", "description": "<uitleg>"}},
    {{"severity": "low", "title": "<titel>", "description": "<uitleg>"}}
  ],
  "quick_wins": ["<actie 1>", "<actie 2>", "<actie 3>", "<actie 4>", "<actie 5>"],
  "medium_term": ["<strategische actie 1>", "<strategische actie 2>", "<strategische actie 3>"],
  "strategic": ["<langetermijn actie 1>", "<langetermijn actie 2>", "<langetermijn actie 3>"],
  "crawler_access": {{
    "GPTBot": {{"platform": "ChatGPT", "status": "{'Allowed' if site_data['gptbot_allowed'] else 'Blocked'}", "recommendation": "{'Behoud toestemming' if site_data['gptbot_allowed'] else 'Voeg expliciete Allow toe in robots.txt'}"}},
    "ClaudeBot": {{"platform": "Claude", "status": "{'Allowed' if site_data['claudebot_allowed'] else 'Not Mentioned'}", "recommendation": "{'Behoud toestemming' if site_data['claudebot_allowed'] else 'Voeg expliciete Allow toe in robots.txt'}"}},
    "PerplexityBot": {{"platform": "Perplexity", "status": "Allowed", "recommendation": "Behoud toestemming"}},
    "Google-Extended": {{"platform": "Gemini", "status": "Allowed", "recommendation": "Behoud toestemming"}},
    "Bingbot": {{"platform": "Bing Copilot", "status": "Allowed", "recommendation": "Behoud toestemming"}}
  }}
}}

Scoring richtlijnen:
- schema: 0-10 als GEEN JSON-LD, 10-40 als basis, 40+ als uitgebreid
- ai_citability: max 30 als geen llms.txt, max 50 als geen structured data
- technical: 40 basis voor werkende site, -10 per ontbrekend element
- geo_score = ai_citability*0.25 + brand_authority*0.20 + content_eeat*0.20 + technical*0.15 + schema*0.10 + platform_optimization*0.10"""

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

    scores          = report_data.get("scores", {})
    platforms_raw   = report_data.get("platforms", {})
    crawlers_raw    = report_data.get("crawler_access", {})
    quick_wins      = report_data.get("quick_wins", [])
    medium_term     = report_data.get("medium_term", [])
    strategic       = report_data.get("strategic", [])
    findings_raw    = report_data.get("findings", [])
    overall         = report_data.get("geo_score", 0)
    company_profile = report_data.get("company_profile", {})
    n_critical_high = len([f for f in findings_raw if f.get("severity", "").lower() in ["critical", "high"]])

    beautifier_data = {
        "company_name":    report_data.get("brand_name", site_data["brand_name"]),
        "url":             url,
        "audit_date":      datetime.now().strftime("%B %d, %Y"),
        "overall_score":   overall,
        "company_tagline": report_data.get("executive_summary", "")[:120],
        "stats": [
            {"value": str(overall),         "label": "GEO Score"},
            {"value": str(n_critical_high), "label": "Kritieke Issues"},
            {"value": str(len(quick_wins)), "label": "Quick Wins"},
            {"value": datetime.now().strftime("%Y"), "label": "Audit Jaar"},
        ],
        "executive_summary": report_data.get("executive_summary", ""),
        "company_profile": {
            "description":   company_profile.get("description", report_data.get("executive_summary", "")),
            "founded":       company_profile.get("founded", ""),
            "location":      company_profile.get("location", ""),
            "industry":      company_profile.get("industry", ""),
            "strengths":     company_profile.get("strengths", []),
            "critical_gaps": company_profile.get("critical_gaps", []),
        },
        "dimensions": [
            {"name": "AI Citability & Visibility",  "description": "Kunnen AI-platforms je content vinden?",     "score": scores.get("ai_citability", 0),         "weight": "25%", "weighted_score": str(round(scores.get("ai_citability", 0) * 0.25, 1))},
            {"name": "Brand Authority Signals",      "description": "Externe signalen die valideren wie je bent", "score": scores.get("brand_authority", 0),       "weight": "20%", "weighted_score": str(round(scores.get("brand_authority", 0) * 0.20, 1))},
            {"name": "Content Quality & E-E-A-T",   "description": "Diepgang en betrouwbaarheid van content",    "score": scores.get("content_eeat", 0),          "weight": "20%", "weighted_score": str(round(scores.get("content_eeat", 0) * 0.20, 1))},
            {"name": "Technical Foundations",        "description": "Technische basis voor AI-toegankelijkheid",  "score": scores.get("technical", 0),             "weight": "15%", "weighted_score": str(round(scores.get("technical", 0) * 0.15, 1))},
            {"name": "Schema & Structured Data",     "description": "Gestructureerde data voor zoekmachines",    "score": scores.get("schema", 0),                "weight": "10%", "weighted_score": str(round(scores.get("schema", 0) * 0.10, 1))},
            {"name": "Platform Optimization",        "description": "Optimalisatie per AI-platform",             "score": scores.get("platform_optimization", 0), "weight": "10%", "weighted_score": str(round(scores.get("platform_optimization", 0) * 0.10, 1))},
        ],
        "platforms": [{"name": k, "score": v} for k, v in platforms_raw.items()],
        "crawlers": [
            {"name": k, "platform": v.get("platform", ""), "status": v.get("status", ""), "recommendation": v.get("recommendation", "")}
            for k, v in crawlers_raw.items()
        ],
        "findings": [
            {"severity": f.get("severity", "LOW").upper(), "title": f.get("title", ""), "description": f.get("description", "")}
            for f in findings_raw
        ],
        "action_plan": {
            "quick_wins":  [{"title": a, "description": "", "time_estimate": "30 min"} if isinstance(a, str) else a for a in quick_wins],
            "medium_term": [{"title": a, "description": "", "time_estimate": "1 week"} if isinstance(a, str) else a for a in medium_term],
            "strategic":   [{"title": a, "description": "", "time_estimate": "1 maand"} if isinstance(a, str) else a for a in strategic],
        },
        "methodology": f"Deze GEO audit analyseerde {url} op zes gewogen dimensies.",
    }

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        pdf_path = tmp.name
    html = generate_html(beautifier_data)
    generate_pdf(html, pdf_path)
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    os.unlink(pdf_path)

    email_sent = await send_report_email(
        to_email=email,
        brand_name=beautifier_data["company_name"],
        geo_score=overall,
        pdf_bytes=pdf_bytes,
    )

    save_report(email=email, url=url, geo_score=overall)

    return {
        "report":     report_data,
        "pdf_base64": base64.b64encode(pdf_bytes).decode('utf-8'),
        "url":        url,
        "email_sent": email_sent,
    }

# ─────────────────────────────────────────────────────────────────────────────
# MOLLIE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
async def mollie_create_customer(email: str) -> str:
    """Maak Mollie klant aan en geef customer_id terug."""
    async with httpx.AsyncClient() as http:
        resp = await http.post(
            "https://api.mollie.com/v2/customers",
            headers={"Authorization": f"Bearer {MOLLIE_API_KEY}"},
            json={"name": email, "email": email},
        )
    data = resp.json()
    if "id" not in data:
        raise HTTPException(status_code=500, detail=f"Mollie customer error: {data}")
    return data["id"]

async def mollie_create_payment(amount: str, description: str, redirect_url: str, webhook_url: str, metadata: dict) -> dict:
    """Maak eenmalige Mollie betaling aan."""
    async with httpx.AsyncClient() as http:
        resp = await http.post(
            "https://api.mollie.com/v2/payments",
            headers={"Authorization": f"Bearer {MOLLIE_API_KEY}"},
            json={
                "amount":      {"currency": "EUR", "value": amount},
                "description": description,
                "redirectUrl": redirect_url,
                "webhookUrl":  webhook_url,
                "metadata":    metadata,
                "locale":      "nl_NL",
            },
        )
    return resp.json()

async def mollie_create_subscription(customer_id: str, email: str, url: str, webhook_url: str) -> dict:
    """Maak Mollie subscription aan (maandelijks €29,99)."""
    # Eerst een mandaat betaling nodig — stuur klant naar first payment
    async with httpx.AsyncClient() as http:
        resp = await http.post(
            "https://api.mollie.com/v2/payments",
            headers={"Authorization": f"Bearer {MOLLIE_API_KEY}"},
            json={
                "amount":       {"currency": "EUR", "value": PRICE_SUB_MONTH},
                "description":  "GEO Monitor Abonnement — eerste maand",
                "redirectUrl":  f"{FRONTEND_URL}/betaling/succes?plan=subscription",
                "webhookUrl":   webhook_url,
                "customerId":   customer_id,
                "sequenceType": "first",
                "locale":       "nl_NL",
                "metadata": {
                    "type":     "subscription_first",
                    "email":    email,
                    "url":      url,
                    "customer_id": customer_id,
                },
            },
        )
    return resp.json()

async def mollie_activate_subscription(customer_id: str, mandate_id: str, email: str, url: str, webhook_url: str) -> str:
    """Activeer recurring subscription na eerste betaling."""
    async with httpx.AsyncClient() as http:
        resp = await http.post(
            f"https://api.mollie.com/v2/customers/{customer_id}/subscriptions",
            headers={"Authorization": f"Bearer {MOLLIE_API_KEY}"},
            json={
                "amount":      {"currency": "EUR", "value": PRICE_SUB_MONTH},
                "interval":    "1 month",
                "description": "GEO Monitor Abonnement",
                "webhookUrl":  webhook_url,
                "metadata":    {"email": email, "url": url, "type": "subscription_recurring"},
            },
        )
    data = resp.json()
    return data.get("id", "")

async def mollie_get_payment(payment_id: str) -> dict:
    async with httpx.AsyncClient() as http:
        resp = await http.get(
            f"https://api.mollie.com/v2/payments/{payment_id}",
            headers={"Authorization": f"Bearer {MOLLIE_API_KEY}"},
        )
    return resp.json()

# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "GEO API is running", "version": "2.0.0"}


@app.post("/check-reports")
def check_reports(req: CheckReportRequest):
    """Controleer hoeveel rapporten dit email al heeft + abonnement status."""
    count = count_user_reports(req.email)
    with get_db() as conn:
        sub = conn.execute(
            "SELECT status FROM subscriptions WHERE email = ? ORDER BY id DESC LIMIT 1",
            (req.email,)
        ).fetchone()

    has_subscription = sub and sub["status"] == "active"
    price = PRICE_FIRST if count == 0 else PRICE_EXTRA

    return {
        "email":            req.email,
        "report_count":     count,
        "has_subscription": has_subscription,
        "next_price":       price,
        "is_first_report":  count == 0,
    }


@app.post("/payment/create")
async def create_payment(req: PaymentRequest):
    """
    Maak betaallink aan.
    plan = "single"       → eenmalige scan (€9,99 of €49,99)
    plan = "subscription" → maandelijks abonnement (€29,99/maand)
    """
    if not MOLLIE_API_KEY:
        raise HTTPException(status_code=500, detail="MOLLIE_API_KEY niet ingesteld")

    webhook_url  = f"{BASE_URL}/payment/webhook"

    if req.plan == "subscription":
        customer_id = await mollie_create_customer(req.email)
        # Sla subscription op als pending
        with get_db() as conn:
            conn.execute(
                "INSERT INTO subscriptions (mollie_customer_id, email, status) VALUES (?, ?, 'pending')",
                (customer_id, req.email)
            )
            conn.commit()

        payment = await mollie_create_subscription(customer_id, req.email, req.url, webhook_url)
        if "id" not in payment:
            raise HTTPException(status_code=500, detail=f"Mollie fout: {payment}")

        return {
            "payment_id":   payment["id"],
            "checkout_url": payment["_links"]["checkout"]["href"],
            "plan":         "subscription",
            "amount":       PRICE_SUB_MONTH,
        }

    else:  # single
        count  = count_user_reports(req.email)
        amount = PRICE_FIRST if count == 0 else PRICE_EXTRA
        desc   = f"GEO Rapport — {req.url} ({'eerste scan' if count == 0 else 'extra scan'})"

        redirect_url = f"{FRONTEND_URL}/betaling/succes?plan=single"
        payment = await mollie_create_payment(
            amount=amount,
            description=desc,
            redirect_url=redirect_url,
            webhook_url=webhook_url,
            metadata={"type": "single", "email": req.email, "url": req.url},
        )

        if "id" not in payment:
            raise HTTPException(status_code=500, detail=f"Mollie fout: {payment}")

        # Sla order op in DB
        with get_db() as conn:
            conn.execute(
                "INSERT INTO orders (mollie_id, email, url, amount, status) VALUES (?, ?, ?, ?, 'open')",
                (payment["id"], req.email, req.url, amount)
            )
            conn.commit()

        return {
            "payment_id":   payment["id"],
            "checkout_url": payment["_links"]["checkout"]["href"],
            "plan":         "single",
            "amount":       amount,
        }


@app.post("/payment/webhook")
async def payment_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Mollie stuurt hier de betaalstatus naartoe.
    Verwerk betaling en genereer rapport op de achtergrond.
    """
    form = await request.form()
    payment_id = form.get("id")

    if not payment_id:
        return JSONResponse({"status": "no payment id"}, status_code=200)

    payment = await mollie_get_payment(payment_id)
    status  = payment.get("status")
    meta    = payment.get("metadata", {})

    print(f"📩 Webhook ontvangen: {payment_id} — status: {status}")

    if status != "paid":
        # Update order status als het geen betaling is
        with get_db() as conn:
            conn.execute(
                "UPDATE orders SET status = ? WHERE mollie_id = ?",
                (status, payment_id)
            )
            conn.commit()
        return JSONResponse({"status": "ok"}, status_code=200)

    payment_type = meta.get("type", "single")
    email        = meta.get("email", "")
    url          = meta.get("url", "")

    if payment_type in ("single", "subscription_first", "subscription_recurring"):
        # Update order
        with get_db() as conn:
            conn.execute(
                "UPDATE orders SET status = 'paid', paid_at = ? WHERE mollie_id = ?",
                (datetime.now().isoformat(), payment_id)
            )
            conn.commit()

        # Activeer subscription na eerste betaling
        if payment_type == "subscription_first":
            customer_id = meta.get("customer_id", "")
            mandate_id  = payment.get("mandateId", "")
            webhook_url = f"{BASE_URL}/payment/webhook"
            if customer_id and mandate_id:
                sub_id = await mollie_activate_subscription(customer_id, mandate_id, email, url, webhook_url)
                with get_db() as conn:
                    conn.execute(
                        "UPDATE subscriptions SET status = 'active', mollie_sub_id = ? WHERE mollie_customer_id = ?",
                        (sub_id, customer_id)
                    )
                    conn.commit()

        # Genereer rapport op achtergrond zodat webhook snel antwoordt
        if email and url:
            background_tasks.add_task(generate_and_send_report, email, url)

    return JSONResponse({"status": "ok"}, status_code=200)


@app.get("/payment/status/{payment_id}")
async def payment_status(payment_id: str):
    """Check betaalstatus (voor polling vanuit de frontend)."""
    with get_db() as conn:
        order = conn.execute(
            "SELECT * FROM orders WHERE mollie_id = ?", (payment_id,)
        ).fetchone()

    if order:
        return {
            "payment_id": payment_id,
            "status":     order["status"],
            "email":      order["email"],
            "url":        order["url"],
            "amount":     order["amount"],
            "paid_at":    order["paid_at"],
        }

    # Fallback: vraag Mollie zelf
    payment = await mollie_get_payment(payment_id)
    return {
        "payment_id": payment_id,
        "status":     payment.get("status"),
        "amount":     payment.get("amount", {}).get("value"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# BESTAANDE AUDIT ROUTES (ongewijzigd)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/audit/basic")
async def basic_audit(request: AuditRequest):
    site_data = fetch_website(request.url)

    prompt = f"""Je bent een GEO expert. Analyseer deze website en geef een nauwkeurige GEO audit.

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
  "geo_score": <getal 0-100>,
  "executive_summary": "<2-3 zinnen samenvatting>",
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
}}"""

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
    """Directe audit zonder betaling (intern gebruik / testen)."""
    return await generate_and_send_report(request.email, request.url)
