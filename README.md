# fashion-marketplace

Run the full stack with Docker Compose:

```powershell
docker compose up --build
```

This starts:

- MongoDB on `mongodb://localhost:27017`
- Backend on `http://localhost:8001`
- Frontend on `http://localhost:3000`

The backend seeds indexes, demo users, taxonomy, and demo listings on startup.

## Docker setup

The repository now includes:

- [docker-compose.yml](docker-compose.yml)
- [backend/Dockerfile](backend/Dockerfile)
- [frontend/Dockerfile](frontend/Dockerfile)

The compose file sets the required runtime environment for both apps:

- `MONGO_URL=mongodb://mongo:27017`
- `DB_NAME=fashion_marketplace`
- `CORS_ORIGINS=http://localhost:3000`
- `REACT_APP_BACKEND_URL=http://localhost:8001`
- `JWT_SECRET=local-dev-jwt-secret-change-me`

## Manual local run

Use Python 3.11 for the backend. If `py --list` only shows Python 3.14, install 3.11 first and recreate the virtual environment.

The repo includes local env files for manual startup:

- [backend/.env](backend/.env)
- [frontend/.env](frontend/.env)

If you prefer to run without Docker, use the original workflow:

Use Node 20 for the frontend. Node 12 is too old for the current dependency set, and this repo also works with npm, so Yarn is optional.

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

```powershell
cd frontend
npm install
npm start
```

Open `http://localhost:3000` in the browser.