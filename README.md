# CareerScout AI — Fresher Job Verifier

CareerScout searches Google Jobs through SerpApi and shows the result's evidence link alongside a few transparent caution signals. It helps freshers decide what to verify; it cannot determine whether a listing is legitimate.

## Run locally

1. Use Python 3.10 or newer. From the project root, create and activate a virtual environment:

   ```powershell
   py -m venv backend/.venv
   .\backend\.venv\Scripts\Activate.ps1
   pip install -r backend/requirements-dev.txt
   ```

2. Copy `backend/.env.example` to `backend/.env` and set `SERPAPI_KEY` to your own key. The app loads this exact file path even when launched from a different current directory. `.env` files and virtual environments are ignored by Git. Never paste a key into source code or commit it.

3. Start the app:

   ```powershell
   uvicorn main:app --app-dir backend --reload
   ```

4. Open http://127.0.0.1:8000. Health/configuration is available at `/health`; search is available at `/api/jobs?role=Python%20Intern&location=Bengaluru,%20India`.

## Architecture

- The browser loads the static page, styles, and JavaScript from the FastAPI app (`/`, `/static/*`).
- The search form calls the same-origin `/api/jobs` endpoint with a role and location.
- FastAPI loads `backend/.env`, calls SerpApi, normalizes returned Google Jobs records, and adds cautious text-based risk signals.
- The browser renders records returned by the API and links back to Google/SerpApi-provided listing evidence.

## SerpApi engine and evidence

- The app uses SerpApi's `google_jobs` engine because it returns structured job fields such as title, company, location, description, and evidence links in the same search response. It is the only SerpApi engine used; no general web-search engine is needed for this MVP's job-listing flow.
- Requests use `q`, `location`, `gl=in`, and `hl=en` for an India location and English results.
- Evidence links come from SerpApi's Google Jobs `link` or `share_link` fields. No synthetic listings are used.
- Optional posting time is shown only when SerpApi provides it.
- Caution signals use listing text and missing fields (for example, upfront fee language, WhatsApp/Telegram application directions, missing company name, or missing evidence URL). They are deliberately not a fraud score or legitimacy guarantee.

## Limits

Results can be incomplete, stale, duplicated, or unavailable and depend on SerpApi quota and Google Jobs coverage. An evidence link is a place to inspect the result, not proof that a job is authentic or still open. The app does not contact employers or independently verify companies. Search requests require an active SerpApi key and internet access.

## Three-minute demo

1. **0:00–0:25 — Introduce the problem:** show the search page and explain that freshers need to inspect listings and their source evidence.
2. **0:25–0:50 — Start locally:** show the app at `http://127.0.0.1:8000` and the role/location fields.
3. **0:50–1:35 — Run a live search:** search `Python Intern` in `Bengaluru, India`; show the current result count and cards. Results can change between runs.
4. **1:35–2:20 — Inspect a result:** point out its company, location, posting time when available, and open the listing evidence link.
5. **2:20–2:45 — Explain caution signals:** show that these are prompts to verify, not proof of fraud or legitimacy.
6. **2:45–3:00 — Close with limits:** mention SerpApi quota/coverage, stale or incomplete listings, and the need to verify with employers.

## Tests

Run from the project root after installing `backend/requirements-dev.txt`:

```powershell
python -m unittest discover -s backend -p "test_*.py" -v
```

Tests mock SerpApi at the HTTP boundary, so they verify request parameters, response normalization, evidence handling, caution signals, and error behavior without spending API credits or fabricating live results. A live API smoke check requires a valid key in `backend/.env`.

## AI tools used

OpenAI Codex assisted with repository inspection, implementation, and test authoring. Runtime job data and evidence are supplied by SerpApi; no language model generates job listings or evidence.
