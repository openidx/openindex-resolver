from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from copy import deepcopy
import json

app = FastAPI(
    title="OpenIndex Resolver",
    version="0.3"
)

# -------------------------------------------------
# Base paths
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
RECORDS_DIR = BASE_DIR / "records"
CONTEXTS_DIR = BASE_DIR / "contexts"

# -------------------------------------------------
# Templates
# -------------------------------------------------

templates = Jinja2Templates(
    directory=BASE_DIR / "app" / "templates"
)

# -------------------------------------------------
# Static serving for JSON-LD contexts
# -------------------------------------------------

app.mount(
    "/contexts",
    StaticFiles(directory=CONTEXTS_DIR),
    name="contexts"
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

# -------------------------------------------------
# Context lookup table
# -------------------------------------------------

CONTEXT_MAP = {
    "namespace": "https://openindex.id/contexts/namespace.jsonld",
    "Work": "https://openindex.id/contexts/work.jsonld",
    "Edition": "https://openindex.id/contexts/edition.jsonld",
    "DigitalObject": "https://openindex.id/contexts/digital-object.jsonld"
}

def get_context_for_record(record: dict) -> Optional[str]:
    return CONTEXT_MAP.get(record.get("type"))


# -------------------------------------------------
# favicon for html response
# -------------------------------------------------

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(BASE_DIR / "static" / "favicon.ico")

# -------------------------------------------------
# Utility functions
# -------------------------------------------------

def load_json(path: Path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def wrap_record(record: dict, include_context: bool = False) -> dict:
    """
    Return a safe response copy of a record.
    Injects @context only when requested.
    """
    response = deepcopy(record)

    if include_context:
        context_url = get_context_for_record(record)
        if context_url:
            response["@context"] = context_url

    return response

# -------------------------------------------------
# Namespace resolution
# Example: /earthpress
# -------------------------------------------------

@app.get("/{namespace}", response_class=HTMLResponse)
async def resolve_namespace(request: Request, namespace: str):
    namespace_dir = RECORDS_DIR / namespace
    namespace_file = namespace_dir / "_namespace.json"

    if not namespace_file.exists():
        raise HTTPException(status_code=404, detail="Namespace not found")

    namespace_data = load_json(namespace_file)

    records = []
    for file in namespace_dir.glob("*.json"):
        if file.name == "_namespace.json":
            continue
        record = load_json(file)
        if record:
            records.append(record)

    accept = request.headers.get("accept", "")

    # JSON-LD response
    if "application/ld+json" in accept:
        response = {
            "@context": CONTEXT_MAP.get("namespace"),
            "@id": namespace_data.get("openindex"),
            "@type": "Collection",
            "name": namespace_data.get("name"),
            "hasPart": [r.get("openindex") for r in records]
        }
        return JSONResponse(response, media_type="application/ld+json")

    # JSON response
    if "application/json" in accept:
        return JSONResponse({
            "namespace": namespace_data,
            "records": records
        })

    # Default: HTML
    return templates.TemplateResponse(
        "namespace.html",
        {
            "request": request,
            "namespace": namespace_data,
            "records": records
        }
    )

# -------------------------------------------------
# Record resolution
# Example: /earthpress/tartarian-world
# -------------------------------------------------

@app.get("/{namespace}/{slug}", response_class=HTMLResponse)
async def resolve_record(request: Request, namespace: str, slug: str):
    record_path = RECORDS_DIR / namespace / f"{slug}.json"
    record = load_json(record_path)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    accept = request.headers.get("accept", "")

    # JSON-LD response
    if "application/ld+json" in accept:
        response = wrap_record(record, include_context=True)
        return JSONResponse(response, media_type="application/ld+json")

    # JSON response
    if "application/json" in accept:
        return JSONResponse(record)

    # Default: HTML
    return templates.TemplateResponse(
        "record.html",
        {
            "request": request,
            "record": record
        }
    )
