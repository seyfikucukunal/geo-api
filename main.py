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
from generate_pdf_report import generate_report

app = FastAPI(title="GEO API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai-syah.nl", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

class AuditRequest(BaseModel):
    url: str

class FullReportRequest(BaseModel):
    url: str
    email: str

def fetch_website(url: str) -> dict:
    if not url.startswith("http"):
        url = "https://" + url
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; GEOBot/1.0; +https://ai-syah.nl)"
        }
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
            "url": url,
            "brand_name": brand_name,
            "title": title_text,
            "meta_description": meta_desc_text,
            "has_meta_description": has_meta_description,
            "has_og_tags": has_og_tags,
            "has_structured_data": has_structured_data,
            "has_h1": has_h1,
            "has_llms_txt": has_llms_txt,
            "gptbot_allowed": gptbot_allowed,
            "claudebot_allowed": claudebot_allowed,
            "page_text": page_text,
            "status_code": response.status_code,
        }
    except Exception as e:
        brand_name = url.replace("https://", "").replace("www.", "").split(".")[0].capitalize()
        return {
            "url": url,
            "brand_name": brand_name,
            "error": str(e),
            "title": "",
            "meta_description": "",
            "has_meta_description": False,
            "has_og_tags": False,
            "has_structured_data": False,
            "has_h1": False,
            "has_llms_txt": False,
            "gptbot_allowed": True,
            "claudebot_allowed": True,
            "page_text": "",
            "status_code": 0,
        }

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
  "quick_wins": [
    "<actie 1>",
    "<actie 2>",
    "<actie 3>"
  ]
}}

Scoring richtlijnen (wees realistisch en streng):
- schema score: 0-10 als geen JSON-LD, 10-40 als basis aanwezig
- ai_citability: laag als geen llms.txt, geen structured data
- technical: basis punten voor werkende site, aftrekken voor ontbrekende meta
- geo_score is gewogen gemiddelde: ai_citability*0.25 + brand_authority*0.20 + content_eeat*0.20 + technical*0.15 + schema*0.10 + platform_optimization*0.10"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    
    result = json.loads(text)
    return result

@app.post("/audit/full")
async def full_audit(request: FullReportRequest):
    site_data = fetch_website(request.url)
    
    prompt = f"""Je bent een GEO expert. Analyseer deze website data en geef een uitgebreid GEO audit rapport terug als JSON.

Website: {site_data['url']}
Brand naam: {site_data['brand_name']}
Title: {site_data['title']}
Meta Description: {site_data['meta_description']}
Open Graph tags: {site_data['has_og_tags']}
Structured Data: {site_data['has_structured_data']}
llms.txt: {site_data['has_llms_txt']}
GPTBot toegestaan: {site_data['gptbot_allowed']}
ClaudeBot toegestaan: {site_data['claudebot_allowed']}
Pagina inhoud: {site_data['page_text'][:2000]}

Geef je antwoord ALLEEN als geldig JSON zonder markdown:
{{
  "url": "{site_data['url']}",
  "brand_name": "{site_data['brand_name']}",
  "date": "{datetime.now().strftime('%Y-%m-%d')}",
  "geo_score": <0-100>,
  "executive_summary": "<2-3 zinnen>",
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
  "medium_term": ["<actie 1>", "<actie 2>", "<actie 3>"],
  "strategic": ["<actie 1>", "<actie 2>", "<actie 3>"],
  "crawler_access": {{
    "GPTBot": {{"platform": "ChatGPT", "status": "{'Allowed' if site_data['gptbot_allowed'] else 'Blocked'}", "recommendation": "Behoud toestemming"}},
    "ClaudeBot": {{"platform": "Claude", "status": "{'Allowed' if site_data['claudebot_allowed'] else 'Blocked'}", "recommendation": "Behoud toestemming"}},
    "PerplexityBot": {{"platform": "Perplexity", "status": "Allowed", "recommendation": "Behoud toestemming"}},
    "Google-Extended": {{"platform": "Gemini", "status": "Allowed", "recommendation": "Behoud toestemming"}},
    "Bingbot": {{"platform": "Bing Copilot", "status": "Allowed", "recommendation": "Behoud toestemming"}}
  }}
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    
    report_data = json.loads(text)
    
    # Genereer PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        pdf_path = tmp.name
    
    generate_report(report_data, pdf_path)
    
    # Lees PDF en converteer naar base64
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    
    # Verwijder tijdelijk bestand
    os.unlink(pdf_path)
    
    return {
        "report": report_data,
        "pdf_base64": pdf_base64,
        "url": request.url
    }