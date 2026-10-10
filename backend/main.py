"""CareerScout AI: evidence-first fresher job search backed by SerpApi."""

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env", override=False)
SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

app = FastAPI(title="CareerScout AI", description="Evidence-first job search for freshers")
app.mount("/static", StaticFiles(directory=BACKEND_DIR / "static"), name="static")


def _is_http_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def assess_risk(job: dict[str, Any]) -> dict[str, Any]:
    """Return explainable caution signals, never a fraud verdict."""
    text = " ".join(str(job.get(field) or "") for field in ("title", "description", "extensions")).lower()
    signals: list[str] = []
    if re.search(r"\b(registration|application|training|security) fee\b|pay (?:to|for) (?:apply|the job)", text):
        signals.append("Listing text mentions an upfront fee; verify directly before paying.")
    if re.search(r"\b(whatsapp|telegram)\b", text) and re.search(r"\b(apply|contact|message|send)\b", text):
        signals.append("Application text directs candidates to WhatsApp or Telegram; verify the employer independently.")
    if not str(job.get("company_name") or "").strip():
        signals.append("Company name was not provided in the search result.")
    if not _is_http_url(job.get("link")) and not _is_http_url(job.get("share_link")):
        signals.append("No direct evidence link was provided by the search result.")
    level = "caution" if signals else "no_obvious_signal"
    return {"level": level, "signals": signals,
            "disclaimer": "Heuristic signals are prompts to verify, not proof of fraud or legitimacy."}


def normalize_job(job: dict[str, Any]) -> dict[str, Any]:
    evidence = job.get("link") if _is_http_url(job.get("link")) else job.get("share_link")
    return {
        "title": job.get("title") or "Title not provided",
        "company": job.get("company_name") or "Company not provided",
        "location": job.get("location") or "Location not provided",
        "via": job.get("via"),
        "posted_at": (job.get("detected_extensions") or {}).get("posted_at"),
        "description": job.get("description") or "",
        "evidence_url": evidence if _is_http_url(evidence) else None,
        "risk": assess_risk(job),
    }


@app.get("/")
def home():
    return FileResponse(BACKEND_DIR / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "serpapi_configured": bool(os.getenv("SERPAPI_KEY"))}


@app.get("/api/jobs")
def search_jobs(
    role: str = Query("Python Intern", min_length=2, max_length=100),
    location: str = Query("Bengaluru, India", min_length=2, max_length=100),
    limit: int = Query(10, ge=1, le=20),
):
    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if not api_key or api_key.lower() in {"your_serpapi_key_here", "your_api_key", "placeholder"}:
        raise HTTPException(status_code=503, detail="SerpApi is not configured. Set SERPAPI_KEY in backend/.env.")
    try:
        response = requests.get(
            SERPAPI_ENDPOINT,
            params={"engine": "google_jobs", "q": role, "location": location,
                    "gl": "in", "hl": "en", "api_key": api_key},
            timeout=25,
        )
        response.raise_for_status()
        data = response.json()
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="SerpApi request timed out.")
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Could not retrieve results from SerpApi.")
    except ValueError:
        raise HTTPException(status_code=502, detail="SerpApi returned an invalid response.")

    if data.get("error"):
        raise HTTPException(status_code=502, detail="SerpApi returned an error.")
    raw_jobs = data.get("jobs_results")
    if not isinstance(raw_jobs, list):
        raw_jobs = []
    jobs = [normalize_job(job) for job in raw_jobs[:limit] if isinstance(job, dict)]
    return {"role": role, "location": location, "engine": "google_jobs",
            "count": len(jobs), "jobs": jobs,
            "disclaimer": "Search results are not endorsements. Verify details with the employer before applying or paying.",
            "search_metadata": {"status": (data.get("search_metadata") or {}).get("status")}}
