import os
import sys
import time
import threading
import urllib.request
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from .api import auth, accounts, emails, settings as settings_api, dashboard, system

# Safely attempt database table creation without blocking startup
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"DB Metadata init note: {e}")

app = FastAPI(title=settings.APP_NAME)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RENDER_URL = os.environ.get("RENDER_BACKEND_URL", "https://risabh-demo.onrender.com")

@app.middleware("http")
async def proxy_to_render_if_vercel(request: Request, call_next):
    # If running on Vercel lambda and calling API routes, proxy to Render single-source backend
    if (os.environ.get("VERCEL") == "1" or os.environ.get("VERCEL_ENV")) and request.url.path.startswith("/api/"):
        if request.headers.get("x-proxied-from-vercel"):
            return await call_next(request)
        try:
            target_url = f"{RENDER_URL}{request.url.path}"
            if request.url.query:
                target_url += f"?{request.url.query}"

            req_headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host", "content-length", "accept-encoding"]}
            req_headers["x-proxied-from-vercel"] = "1"
            req_headers["accept-encoding"] = "identity"

            body = await request.body()
            req = urllib.request.Request(
                target_url,
                data=body if body else None,
                headers=req_headers,
                method=request.method
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_body = resp.read()
                if resp_body.startswith(b'\x1f\x8b') or resp.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    try:
                        resp_body = gzip.decompress(resp_body)
                    except Exception:
                        pass
                return Response(
                    content=resp_body,
                    status_code=resp.status,
                    media_type="application/json; charset=utf-8"
                )
        except Exception as e:
            print(f"Proxy to Render note: {e}")
            return await call_next(request)

    return await call_next(request)

@app.get("/")
@app.get("/health")
def root_health():
    return {"status": "ok", "service": "email-automation"}

# Register Routers
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(emails.router)
app.include_router(settings_api.router)
app.include_router(dashboard.router)
app.include_router(system.router)

