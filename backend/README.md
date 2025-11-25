FastAPI + Playwright backend for Price Hunter

Quick start (PowerShell)

1) Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies:

```powershell
pip install -r requirements.txt
```

3) Install Playwright browsers (required):

```powershell
python -m playwright install
```

4) Run the server:

```powershell
python main.py
# or with uvicorn for auto-reload during dev
uvicorn main:app --reload --port 8000
```

5) Use the endpoints:
- Health: `GET http://localhost:8000/`
- Scrape all targets: `GET http://localhost:8000/scrape`
- Scrape a single store: `GET http://localhost:8000/scrape?store=Amazon%20MX`

Integration with Angular
- From your Angular app running on `http://localhost:3000` you can call `http://localhost:8000/scrape` (CORS for that origin is enabled).

Notes
- Playwright is headless by default in this server. If a specific site blocks headless scraping, consider setting `headless=False` in `main.py` for that target or running the process on a machine with a display.
- Adjust `SEMAPHORE` concurrency or add caching if you plan many frequent requests.
