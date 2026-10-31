import asyncio
import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path
from typing import AsyncIterator
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="Claude Blog Web Studio", docs_url=None, redoc_url=None)
API_TOKEN = os.environ.get("API_BEARER_TOKEN", "")
STUDIO_PASSWORD_HASH = os.environ.get("STUDIO_PASSWORD_HASH", "")
SESSION_SECRET = os.environ.get("STUDIO_SESSION_SECRET") or API_TOKEN
COOKIE_SECURE = os.environ.get("STUDIO_COOKIE_SECURE", "true").lower() == "true"
WORKSPACE = os.environ.get("CODEX_WORKSPACE", "/workspace")
CODEX_BIN = os.environ.get("CODEX_BIN", "/usr/local/bin/codex")
TASK_TIMEOUT_SECONDS = int(os.environ.get("TASK_TIMEOUT_SECONDS", "1800"))
WEB_DIR = Path(__file__).parent / "web"

if SESSION_SECRET:
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET,
        session_cookie="studio_session",
        max_age=60 * 60 * 12,
        same_site="strict",
        https_only=COOKIE_SECURE,
    )

app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20000)


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=1024)


def studio_ready() -> bool:
    return bool(STUDIO_PASSWORD_HASH and SESSION_SECRET)


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), int(iterations)
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def require_same_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if not origin:
        raise HTTPException(status_code=403, detail="Origin header required")
    parsed = urlsplit(origin)
    if parsed.scheme not in ("https", "http") or parsed.netloc != request.headers.get("host"):
        raise HTTPException(status_code=403, detail="Cross-origin request rejected")


async def require_token(x_api_key: str | None = Header(default=None)) -> None:
    # DigitalOcean reserves Authorization: Bearer for endpoint access.
    if not API_TOKEN:
        raise HTTPException(status_code=503, detail="API token is not configured")
    if not x_api_key or not secrets.compare_digest(x_api_key, API_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid API key")


def require_studio_session(request: Request) -> None:
    if not studio_ready():
        raise HTTPException(status_code=503, detail="Studio login is not configured")
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Authentication required")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/")
async def dashboard():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/auth/me")
async def auth_status(request: Request):
    if not studio_ready():
        return {"configured": False, "authenticated": False}
    return {"configured": True, "authenticated": bool(request.session.get("authenticated"))}


@app.post("/api/auth/login")
async def login(payload: LoginRequest, request: Request):
    require_same_origin(request)
    if not studio_ready():
        raise HTTPException(status_code=503, detail="Set STUDIO_PASSWORD_HASH and STUDIO_SESSION_SECRET")
    if not verify_password(payload.password, STUDIO_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="Password tidak valid")
    request.session.clear()
    request.session["authenticated"] = True
    return {"authenticated": True}


@app.post("/api/auth/logout")
async def logout(request: Request):
    require_same_origin(request)
    if not SESSION_SECRET:
        raise HTTPException(status_code=503, detail="Studio session is not configured")
    request.session.clear()
    return {"authenticated": False}


@app.get("/api/studio")
async def studio_home(request: Request):
    require_studio_session(request)
    return {"name": "Claude Blog Web Studio", "stage": 1, "status": "dashboard-ready"}


@app.post("/v1/tasks", dependencies=[Depends(require_token)])
async def run_task(request: TaskRequest):
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Prompt must not be blank")

    async def events() -> AsyncIterator[str]:
        process = await asyncio.create_subprocess_exec(
            CODEX_BIN, "exec", "--json",
            "--sandbox", "workspace-write",
            "--ask-for-approval", "never",
            "--cd", WORKSPACE, prompt,
            cwd=WORKSPACE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        assert process.stdout is not None
        stderr_task = asyncio.create_task(process.stderr.read()) if process.stderr else None
        yield "event: started\ndata: {}\n\n"
        try:
            async with asyncio.timeout(TASK_TIMEOUT_SECONDS):
                async for line in process.stdout:
                    payload = line.decode("utf-8", errors="replace").rstrip()
                    yield f"event: codex\ndata: {json.dumps(payload)}\n\n"
                await process.wait()
                stderr = await stderr_task if stderr_task else b""
            yield "event: done\ndata: " + json.dumps({
                "exit_code": process.returncode,
                "stderr": stderr.decode("utf-8", errors="replace")[-4000:],
            }) + "\n\n"
        except TimeoutError:
            process.kill()
            await process.wait()
            if stderr_task:
                await stderr_task
            yield "event: error\ndata: " + json.dumps({
                "error": f"Task exceeded {TASK_TIMEOUT_SECONDS} seconds"
            }) + "\n\n"
        except asyncio.CancelledError:
            process.kill()
            await process.wait()
            if stderr_task:
                await stderr_task
            raise
        except Exception as exc:
            process.kill()
            await process.wait()
            if stderr_task:
                await stderr_task
            yield "event: error\ndata: " + json.dumps({"error": str(exc)}) + "\n\n"

    return StreamingResponse(
        events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
