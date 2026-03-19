# Job Finder — Full-Stack Web App

A full-stack job search tool where you can upload your resume, specify a target role and location, and instantly see matching roles from the Jooble API. The current version ranks results by posting date and exposes a **“Run AI Scoring”** button that will be wired to a semantic scoring pipeline in a future phase.

_Screenshot placeholder: add a screenshot of the frontend dashboard here._

---

## Tech Stack

- **Frontend**: React (Vite), TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python)
- **Job Source**: Jooble API
- **Styling**: Dark theme (matching the Streamlit dashboard)
- **Deployment**:
  - Frontend: Vercel
  - Backend: Render

Project structure:

```text
job-finder/
  frontend/   # React + Vite + Tailwind
  backend/    # FastAPI + Jooble client
  README.md
```

---

## Local Development

### 1. Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt

# Set your Jooble API key (or use backend/.env)
export JOOBLE_API_KEY=your_jooble_api_key_here

# Run the API
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

Health check:

```bash
curl http://localhost:8000/health
```

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

The app will be available at the URL printed by Vite (typically `http://localhost:5173`).

During local development, the Vite dev server proxies `/api/*` to `http://localhost:8000` (configured in `vite.config.ts`), so the frontend can call `/api/search` without CORS issues.

---

## Testing the /search Endpoint

With the backend running:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "AI Engineer Intern",
    "location": "New York",
    "max_results": 5
  }'
```

You should receive a JSON response:

```json
{
  "total_fetched": 5,
  "jobs": [
    {
      "id": "...",
      "title": "AI Engineer Intern",
      "company": "Example Co",
      "location": "New York, NY",
      "posted_at": "2026-03-16",
      "url": "https://jooble.org/...",
      "description": "First 400 chars...",
      "job_type": "INTERN",
      "ai_score": null
    }
  ]
}
```

---

## Deployment

### Backend — Render

1. Push this repository to GitHub.
2. In Render:
   - Create a new **Web Service**.
   - Connect your GitHub repo.
   - Set **Root Directory** to `backend`.
   - Render will automatically read `render.yaml`:
     - `buildCommand`: `pip install -r requirements.txt`
     - `startCommand`: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - In the Render dashboard, add an environment variable:
     - `JOOBLE_API_KEY` — your Jooble API key (do **not** commit this to Git).
3. Deploy and note the public URL, e.g. `https://job-finder-api.onrender.com`.

### Frontend — Vercel

1. In Vercel:
   - Create a new project from the same GitHub repo.
   - Set **Root Directory** to `frontend`.
   - Framework preset: **Vite** (React).
2. Add an environment variable:
   - `VITE_API_URL` = `https://job-finder-api.onrender.com`
3. Deploy.

The frontend will now call `POST {VITE_API_URL}/search` in production.

---

## Notes

- The Jooble API key is **only** used server-side in the FastAPI backend and is never exposed to the React frontend.
- Saved jobs on the frontend are stored in `localStorage` under the key `jobfinder_saved_jobs`, so they persist across page refreshes.
- The **“Run AI Scoring ✨”** button currently shows a “Coming soon” message; it is reserved for a future phase that will integrate your existing semantic scoring pipeline.

