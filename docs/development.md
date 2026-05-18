# Development

Run the stack:

```bash
cp .env.example .env
docker compose up --build
```

Backend:

```bash
cd backend
pip install -e ".[scraping,semantic,jobspy,test]"
pytest
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Useful API endpoints:

- `GET /health`
- `GET /api/jobs`
- `GET /api/jobs/{id}`
- `PATCH /api/jobs/{id}`
- `GET /api/sources`
- `PATCH /api/sources/{id}`
- `POST /api/scrape/run`
- `POST /api/scrape/run/{source_id}`
- `GET /api/scrape/runs`
- `GET /api/stats`
- `GET /api/profile`

Testing priority:

- scorer behavior
- source config validation
- dedup/content hashing
- API endpoints
- mocked adapters before live scraping
