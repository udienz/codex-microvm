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
MAX_PROMPT_CHARS = int(os.environ.get("MAX_PROMPT_CHARS", "20000"))
TASK_TIMEOUT_SECONDS = int(os.environ.get("TASK_TIMEOUT_SECONDS", "1800"))


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20000)


async def require_token(authorization: str | None = Header(default=None)) -> None:
    if not API_TOKEN:
        raise HTTPException(status_code=503, detail="API token is not configured")
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not secrets.compare_digest(supplied, API_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid bearer token")


@app.get("/healthz")
async def healthz():
    # DigitalOcean endpoint authentication still protects this route.
    return {"status": "ok"}


@app.post("/v1/tasks", dependencies=[Depends(require_token)])
async def run_task(request: TaskRequest):
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Prompt must not be blank")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise HTTPException(status_code=413, detail="Prompt is too large")

    async def events() -> AsyncIterator[str]:
        process = await asyncio.create_subprocess_exec(
            CODEX_BIN,
            "exec",
            "--json",
            "--sandbox",
            "workspace-write",
            "--cd",
            WORKSPACE,
            prompt,
            cwd=WORKSPACE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        yield "event: started\ndata: {}\n\n"
        try:
            async def read_stdout():
                assert process.stdout is not None
                while line := await process.stdout.readline():
                    # Codex JSONL events are forwarded as SSE data.
                    payload = line.decode("utf-8", errors="replace").rstrip()
                    yield f"event: codex\ndata: {json.dumps(payload)}\n\n"

            async for item in asyncio.wait_for_stream(read_stdout(), TASK_TIMEOUT_SECONDS):
                yield item

            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
            stderr = await process.stderr.read() if process.stderr else b""
            yield "event: done\ndata: " + json.dumps({
                "exit_code": process.returncode,
                "stderr": stderr.decode("utf-8", errors="replace")[-4000:],
            }) + "\n\n"
        except asyncio.CancelledError:
            process.kill()
            await process.wait()
            raise
        except Exception as exc:
            process.kill()
            await process.wait()
            yield "event: error\ndata: " + json.dumps({"error": str(exc)}) + "\n\n"

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# Small timeout-aware async iterator helper.
class _Asyncio:
    @staticmethod
    async def wait_for_stream(iterator, timeout):
        async def collect():
            async for value in iterator:
                yield value
        # Use an overall task deadline while retaining streaming output.
        queue = asyncio.Queue()
        async def pump():
            try:
                async for value in collect():
                    await queue.put(value)
            finally:
                await queue.put(None)
        task = asyncio.create_task(pump())
        try:
            async with asyncio.timeout(timeout):
                while True:
                    value = await queue.get()
                    if value is None:
                        break
                    yield value
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

asyncio.wait_for_stream = _Asyncio.wait_for_stream
