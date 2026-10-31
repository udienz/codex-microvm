import asyncio
import json
import os
import secrets
from typing import AsyncIterator

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Codex MicroVM API", docs_url=None, redoc_url=None)
API_TOKEN = os.environ.get("API_BEARER_TOKEN", "")
WORKSPACE = os.environ.get("CODEX_WORKSPACE", "/workspace")
CODEX_BIN = os.environ.get("CODEX_BIN", "/usr/local/bin/codex")
TASK_TIMEOUT_SECONDS = int(os.environ.get("TASK_TIMEOUT_SECONDS", "1800"))


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20000)


async def require_token(x_api_key: str | None = Header(default=None)) -> None:
    # DigitalOcean reserves Authorization: Bearer for endpoint access.
    if not API_TOKEN:
        raise HTTPException(status_code=503, detail="API token is not configured")
    if not x_api_key or not secrets.compare_digest(x_api_key, API_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/v1/tasks", dependencies=[Depends(require_token)])
async def run_task(request: TaskRequest):
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Prompt must not be blank")

    async def events() -> AsyncIterator[str]:
        process = await asyncio.create_subprocess_exec(
            CODEX_BIN, "exec", "--json", "--sandbox", "workspace-write",
            "--cd", WORKSPACE, prompt,
            cwd=WORKSPACE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        yield "event: started\ndata: {}\n\n"
        stderr = b""
        try:
            async with asyncio.timeout(TASK_TIMEOUT_SECONDS):
                assert process.stdout is not None
                async for line in process.stdout:
                    payload = line.decode("utf-8", errors="replace").rstrip()
                    yield f"event: codex\ndata: {json.dumps(payload)}\n\n"
                await process.wait()
                if process.stderr:
                    stderr = await process.stderr.read()
            yield "event: done\ndata: " + json.dumps({
                "exit_code": process.returncode,
                "stderr": stderr.decode("utf-8", errors="replace")[-4000:],
            }) + "\n\n"
        except TimeoutError:
            process.kill()
            await process.wait()
            yield "event: error\ndata: " + json.dumps({
                "error": f"Task exceeded {TASK_TIMEOUT_SECONDS} seconds"
            }) + "\n\n"
        except asyncio.CancelledError:
            process.kill()
            await process.wait()
            raise
        except Exception as exc:
            process.kill()
            await process.wait()
            yield "event: error\ndata: " + json.dumps({"error": str(exc)}) + "\n\n"

    return StreamingResponse(
        events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
