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

## Deploy to Render

For this single-process FastAPI app, Render's Python web service is the simplest setup: it builds from the existing `backend/requirements.txt`, serves the existing static frontend from FastAPI, and provides an environment variable for the SerpApi key. The included root-level `render.yaml` configures a **Free** web service, health check, and secret placeholder. It does not contain any key.

1. Push the reviewed repository to GitHub yourself, then sign in to [Render](https://render.com/) and choose **New → Blueprint**. Connect the CareerScout AI GitHub repository and select its `main` branch.
2. Review the Blueprint before applying it. Confirm the `careerscout-ai` service uses the **Free** plan. During initial creation, Render prompts for `SERPAPI_KEY` because the Blueprint marks it `sync: false`; enter the key only in Render's private prompt. If creating a Web Service manually instead, use root directory `backend`, build command `pip install -r requirements.txt`, start command `uvicorn main:app --host 0.0.0.0 --port $PORT`, health check path `/health`, and add `SERPAPI_KEY` in the service's **Environment** dashboard. Never put the key in GitHub or `render.yaml`.
3. Wait for the build/deploy to finish, then open the generated `https://<service-name>.onrender.com/` URL. Check `/health` for `status: ok` and `serpapi_configured: true`; then make a Google Jobs search and investigate a listing. `/health` reports only whether a key is configured.
4. Keep the service on Free unless you explicitly choose otherwise. Free Render services spin down after 15 minutes idle and the next visit may take about a minute to wake. Review current usage/billing settings: Render documents monthly bandwidth and build-pipeline limits, and overages may be billable when a payment method is attached. Do not select a paid plan or add paid resources unless you intend to.

**Before sharing the public URL:** anyone who can reach this app can trigger Google Jobs and Evidence Dossier searches, which consume your SerpApi allowance. This MVP has no account login or per-user rate limiting. Share it accordingly and monitor your SerpApi usage. The service requires outbound internet access to SerpApi; its free-tier ephemeral filesystem is fine because the app stores no persistent user data.

You must complete the GitHub connection, enter the secret in Render, approve the Blueprint, and review billing/usage settings yourself. No deployment or paid resource has been created as part of this repository change.

## Architecture

- The browser loads the static page, styles, and JavaScript from the FastAPI app (`/`, `/static/*`).
- The search form calls the same-origin `/api/jobs` endpoint with a role and location.
- FastAPI loads `backend/.env`, calls SerpApi, normalizes returned Google Jobs records, and adds cautious text-based risk signals.
- The browser renders records returned by the API and links back to Google/SerpApi-provided listing evidence.
- Each job has an **Investigate this job** action. It triggers one Google Search request on demand and renders only linkable organic results returned by SerpApi, with the provided title/snippet, a statement of what that result may support, unknowns, cautious observations, and a practical checklist. A successful dossier is cached in that card for the current page session so opening/closing it costs no additional search.

## SerpApi engine and evidence

- The app uses SerpApi's `google_jobs` engine for structured job listings and its `google` engine for the user-triggered Evidence Dossier. Google Search returns organic result titles, links, and snippets that can help a user find employer/listing context; those snippets do not independently authenticate an employer or listing.
- Requests use `q`, `location`, `gl=in`, and `hl=en` for an India location and English results.
- Dossier requests use `engine=google`, a query composed from the selected job's company, title, and location, and `gl=in`/`hl=en`. One dossier investigation makes one SerpApi request. Investigations do not run automatically when jobs load. Successful results are cached in the rendered card for that page session; retrying after an error makes another request.
- Evidence links come from SerpApi's Google Jobs `link` or `share_link` fields. No synthetic listings are used.
- Optional posting time is shown only when SerpApi provides it.
- Caution signals use listing text and missing fields (for example, upfront fee language, WhatsApp/Telegram application directions, missing company name, or missing evidence URL). They are deliberately not a fraud score or legitimacy guarantee.

## Limits

Results can be incomplete, stale, duplicated, or unavailable and depend on SerpApi quota and Google coverage. A dossier source/snippet is a lead to inspect, not proof a job is authentic or still open. No returned sources or missing warning phrases are not proof of fraud or safety. The app does not visit/validate each source, contact employers, or independently verify companies, recruiter relationships, compensation, or working conditions. Each dossier search consumes API allowance. Search requests require an active SerpApi key and internet access.

## Three-minute demo

## Two-minute demo

1. **0:00–0:20 — Introduction:** Introduce CareerScout AI and explain the problem it solves for freshers.
2. **0:20–0:45 — Search:** Show the job role and location fields.
3. **0:45–1:20 — Job listings:** Demonstrate the job search results and listing cards.
4. **1:20–2:00 — Investigate a job:** Show the evidence dossier, source links, cautions, unknowns, and checklist.
5. **2:00–2:16 — Conclusion:** Explain that the tool helps freshers investigate job listings but cannot guarantee job legitimacy.
6. ## Demo Video
[Watch CareerScout AI Demo]
link- https://drive.google.com/file/d/1gmLGhxxAJ6qs07EH6xsNrcRCEiAQczs0/view?usp=sharing

## Tests

Run from the project root after installing `backend/requirements-dev.txt`:

```powershell
python -m unittest discover -s backend -p "test_*.py" -v
```

Tests mock SerpApi at the HTTP boundary, so they verify request parameters, response normalization, job evidence/caution signals, dossier source links/snippets, absent-source language, and provider/timeout errors without spending API credits or fabricating live results. A live API smoke check requires a valid key in `backend/.env`.

## AI tools used

OpenAI Codex assisted with repository inspection, implementation, and test authoring. Runtime job data and evidence are supplied by SerpApi; no language model generates job listings or evidence.
