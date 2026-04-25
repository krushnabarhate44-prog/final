# RIGA Angel One Backend

Safe read-only backend for your RIGA Custom GPT.

## What this does
- Connects to Angel One SmartAPI
- Provides `/ltp` endpoint for Last Traded Price
- Provides `/riga-signal-demo` endpoint
- Does NOT place orders
- Keeps Angel One keys in environment variables

## Files
- `main.py` - FastAPI backend
- `requirements.txt` - Python packages
- `.env.example` - environment variable template
- `openapi_schema_for_custom_gpt.json` - paste this into Custom GPT Actions after replacing server URL

## Local run

```bash
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Open:
```text
http://127.0.0.1:8000/health
```

## Render deployment

1. Create new Web Service on Render
2. Upload this repo/files to GitHub
3. Build command:
```bash
pip install -r requirements.txt
```

4. Start command:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

5. Add Environment Variables in Render:
```text
ANGEL_API_KEY
ANGEL_CLIENT_CODE
ANGEL_PASSWORD
ANGEL_TOTP_SECRET
RIGA_ACTION_TOKEN
```

## Custom GPT Action setup

1. Open your GPT builder
2. Configure → Actions → Create new action
3. Paste `openapi_schema_for_custom_gpt.json`
4. Replace:
```text
https://YOUR-RENDER-URL.onrender.com
```
with your real Render URL

5. Authentication:
- Type: API Key / Bearer
- Value: your `RIGA_ACTION_TOKEN`

## Example LTP call

```text
/ltp?exchange=NSE&tradingsymbol=SBIN-EQ&symboltoken=3045
```

Important: You need correct Angel One symbol token for each instrument.
