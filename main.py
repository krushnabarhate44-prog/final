import os
from typing import Optional

import pyotp
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query
from SmartApi import SmartConnect

load_dotenv()

app = FastAPI(
    title="RIGA Angel One Read-Only Backend",
    version="1.0.0",
    description="Read-only backend for RIGA Custom GPT to fetch Angel One SmartAPI market data."
)

ANGEL_API_KEY = os.getenv("ANGEL_API_KEY")
ANGEL_CLIENT_CODE = os.getenv("ANGEL_CLIENT_CODE")
ANGEL_PASSWORD = os.getenv("ANGEL_PASSWORD")
ANGEL_TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")
RIGA_ACTION_TOKEN = os.getenv("RIGA_ACTION_TOKEN", "")

_smart_api: Optional[SmartConnect] = None
_jwt_token: Optional[str] = None
_feed_token: Optional[str] = None


def check_auth(authorization: Optional[str]) -> None:
    """Simple bearer-token protection for your backend."""
    if not RIGA_ACTION_TOKEN:
        return
    expected = f"Bearer {RIGA_ACTION_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def get_client() -> SmartConnect:
    """Login to Angel One SmartAPI and cache client."""
    global _smart_api, _jwt_token, _feed_token

    if not all([ANGEL_API_KEY, ANGEL_CLIENT_CODE, ANGEL_PASSWORD, ANGEL_TOTP_SECRET]):
        raise HTTPException(
            status_code=500,
            detail="Angel One environment variables are missing."
        )

    if _smart_api is not None and _jwt_token:
        return _smart_api

    try:
        smart_api = SmartConnect(api_key=ANGEL_API_KEY)
        totp = pyotp.TOTP(ANGEL_TOTP_SECRET).now()
        session = smart_api.generateSession(
            ANGEL_CLIENT_CODE,
            ANGEL_PASSWORD,
            totp
        )

        if not session or not session.get("status"):
            raise HTTPException(status_code=500, detail=f"Angel login failed: {session}")

        data = session.get("data", {})
        _jwt_token = data.get("jwtToken")
        _feed_token = smart_api.getfeedToken()
        _smart_api = smart_api
        return smart_api

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Angel login error: {str(exc)}")


@app.get("/")
def root():
    return {
        "name": "RIGA Angel One Backend",
        "mode": "read-only",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ltp")
def get_ltp(
    exchange: str = Query(..., description="Exchange, e.g. NSE, NFO, BSE"),
    tradingsymbol: str = Query(..., description="Trading symbol, e.g. SBIN-EQ"),
    symboltoken: str = Query(..., description="Angel One symbol token"),
    authorization: Optional[str] = Header(default=None)
):
    """
    Fetch Last Traded Price from Angel One SmartAPI.
    Example:
    /ltp?exchange=NSE&tradingsymbol=SBIN-EQ&symboltoken=3045
    """
    check_auth(authorization)
    client = get_client()

    try:
        response = client.ltpData(exchange, tradingsymbol, symboltoken)
        if not response or not response.get("status"):
            raise HTTPException(status_code=502, detail=response)

        return {
            "exchange": exchange,
            "tradingsymbol": tradingsymbol,
            "symboltoken": symboltoken,
            "angel_response": response
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LTP fetch error: {str(exc)}")


@app.get("/riga-signal-demo")
def riga_signal_demo(
    exchange: str = Query(...),
    tradingsymbol: str = Query(...),
    symboltoken: str = Query(...),
    authorization: Optional[str] = Header(default=None)
):
    """
    Demo endpoint: fetches LTP and returns NO TRADE.
    Real RIGA logic should be added later after stable data feed.
    """
    check_auth(authorization)
    client = get_client()

    try:
        response = client.ltpData(exchange, tradingsymbol, symboltoken)
        ltp = None
        if response and response.get("status"):
            ltp = response.get("data", {}).get("ltp")

        return {
            "symbol": tradingsymbol,
            "ltp": ltp,
            "bias": "NO TRADE",
            "reason": "Demo endpoint only. Full RIGA logic not connected yet."
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
