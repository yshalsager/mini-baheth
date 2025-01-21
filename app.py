# /// script
# dependencies = ["nanodjango", "orjson", "granian", "uvloop"]
# ///
import asyncio
import logging
from pathlib import Path

import orjson
from django.http import StreamingHttpResponse
from django.shortcuts import render
from nanodjango import Django

wdir = Path(__file__).parent
app = Django(
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [wdir / "templates"],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ]
            },
        }
    ]
)
data_dir = wdir / "data"


class ResultStreamProcessor:
    def __init__(self, cmd, data_dir):
        self.cmd = cmd
        self.data_dir = data_dir
        self.previous_match = None
        self.context_before = ""
        self.proc = None

    async def process_match(self, result):
        data = result.get("data", {})
        return {
            "path": data.get("path", {}).get("text", ""),
            "line_number": data.get("line_number", 0),
            "lines": data.get("lines", {}).get("text", ""),
            "submatches": data.get("submatches", []),
            "context_before": "",
            "context_after": "",
            "highlighted_text": highlight_matches(
                data.get("lines", {}).get("text", ""), data.get("submatches", [])
            ),
        }

    def handle_context(self, result):
        if self.previous_match:
            data = result.get("data", {})
            self.previous_match["context_after"] = (
                data.get("lines", {}).get("text", "").strip()
            )
            return True
        else:
            self.context_before = (
                result.get("data", {}).get("lines", {}).get("text", "").strip()
            )
            return False

    async def stream_results(self):
        try:
            self.proc = await asyncio.create_subprocess_exec(
                *self.cmd,
                cwd=self.data_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            async for line in self.proc.stdout:
                try:
                    result = orjson.loads(line.decode())

                    if result.get("type") == "match":
                        result_data = await self.process_match(result)
                        if self.context_before:
                            result_data["context_before"] = self.context_before
                            self.context_before = ""

                        if self.previous_match:
                            yield f"data: {orjson.dumps(self.previous_match).decode()}\n\n"
                        else:
                            self.previous_match = result_data

                    elif result.get("type") == "context":
                        if self.handle_context(result):
                            yield f"data: {orjson.dumps(self.previous_match).decode()}\n\n"
                            self.previous_match = None

                except orjson.JSONDecodeError as e:
                    logging.error(f"JSON decode error: {e}")
                    continue
                except Exception as e:
                    logging.error(f"Error processing line: {e}")
                    continue

            if self.previous_match:
                yield f"data: {orjson.dumps(self.previous_match).decode()}\n\n"

            yield f"data: {orjson.dumps({'complete': True}).decode()}\n\n"

        except Exception as e:
            logging.error(f"Stream processing error: {e}")
            yield f"data: {orjson.dumps({'error': str(e)}).decode()}\n\n"
        finally:
            if self.proc:
                try:
                    await asyncio.wait_for(self.proc.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self.proc.terminate()
                    await self.proc.wait()


def highlight_matches(text: str, submatches: list[dict[str, int]]) -> str:
    """Helper function to highlight matched text with HTML"""
    result = []
    last_end = 0

    for match in sorted(submatches, key=lambda x: x["start"]):
        start, end = match["start"], match["end"]
        result.append(text[last_end:start])
        result.append(f'<span class="bg-yellow-200">{text[start:end]}</span>')
        last_end = end

    result.append(text[last_end:])
    return "".join(result).strip()


@app.route("/")
def index(request):
    return render(
        request,
        "index.html",
        {"directories": [str(p.relative_to(data_dir)) for p in data_dir.glob("**/")]},
    )


@app.api.get("/search")
async def search(
    request: StreamingHttpResponse, query: str, directory: str, file_filter: str
):
    if not query:
        return ""

    cmd = [
        "rg",
        "--json",
        "--max-count",
        "100",
        "-m",
        "500",
        "--no-ignore-vcs",
        "-C",
        "1",
    ]
    if directory:
        cmd.extend(["-g", f"{directory}/**" if directory != "." else "**/"])
    if file_filter:
        if directory:
            _filter = cmd.pop()
            cmd.append(f"{_filter}{'/' if directory != '.' else ''}{file_filter}")
        else:
            cmd.extend(["-g", f"{file_filter}"])
    cmd.append(query)
    processor = ResultStreamProcessor(cmd, data_dir)
    return StreamingHttpResponse(
        processor.stream_results(), content_type="text/event-stream"
    )


if __name__ == "__main__":
    app.run()
