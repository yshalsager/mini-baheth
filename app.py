# /// script
# dependencies = ["nanodjango", "orjson", "uvicorn"]
# ///
#
import asyncio
from pathlib import Path

import orjson
from django.http import HttpResponse, StreamingHttpResponse
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
async def search(request: HttpResponse, query: str, directory: str, file_filter: str):
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

    async def stream_results():
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=data_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            previous_match = ""
            async for line in proc.stdout:
                try:
                    result = orjson.loads(line.decode())
                    if result.get("type") == "match":
                        data = result.get("data", {})
                        result_data = {
                            "path": data.get("path", {}).get("text", ""),
                            "line_number": data.get("line_number", 0),
                            "lines": data.get("lines", {}).get("text", ""),
                            "submatches": data.get("submatches", []),
                            "context_before": "",
                            "context_after": "",
                        }
                        result_data["highlighted_text"] = highlight_matches(
                            result_data["lines"], result_data["submatches"]
                        )
                    elif result.get("type") == "context":
                        if previous_match:
                            data = result.get("data", {})
                            previous_match["context_after"] = data.get("lines", {}).get(
                                "text", ""
                            ).strip()
                            yield orjson.dumps(previous_match).decode() + "\n"
                            previous_match = None
                        else:
                            context_before = (
                                result.get("data", {}).get("lines", {}).get("text", "").strip()
                            )
                            continue

                    if result.get("type") == "match":
                        if context_before:
                            result_data["context_before"] = context_before
                            context_before = ""
                        previous_match = result_data

                except orjson.JSONDecodeError:
                    continue
            await proc.wait()

        except Exception as e:
            yield f"<p class='text-red-500'>Error: {str(e)}</p>"

    return StreamingHttpResponse(stream_results(), content_type="text/html")


if __name__ == "__main__":
    app.run()
