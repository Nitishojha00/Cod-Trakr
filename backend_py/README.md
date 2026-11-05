# Backend (FastAPI port of the Node/Express backend)

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium        # needed for the CodeChef / GFG browser fallbacks
cp .env.example .env               # fill in the values (same names as the Node .env)
python main.py                     # or: uvicorn main:app --host 0.0.0.0 --port 4000
```
Uses the same `.env` variables, MongoDB collections (`users`, `notes`, `chats`),
Redis keys, JWT format (HS256, `_id` + `email`, 1h) and `token` cookie as the Node version,
so existing data and already-issued tokens keep working.
