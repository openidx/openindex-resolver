from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json

app = FastAPI(
    title="OpenIndex Resolver",
    version="0.2"
)

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
RECORDS_DIR = BASE_DIR / "records"

# Templates
templates = Jinja2Templates(
    directory=BASE_DIR / "app" / "templates"
)

# -----------------------------
# Utility functions
# -----------------------------

def load_json(path: Path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# -----------------------------
# Namespace resolution
# -----------------------------
# Example: /earthpress
# -----------------------------

@app.get("/{namespace}", response_class=HTMLResponse)
async def resolve_namespace(request: Request, namespace: str):
    namespace_dir = RECORDS_DIR / namespace
    namespace_file = namespace_dir / "_namespace.json"

    if not namespace_file.exists():
        raise HTTPException(status_code=404, detail="Namespace not found")

    namespace_data = load_json(namespace_file)

    # Load all records in namespace
    records = []
    for file in namespace_dir.glob("*.json"):
        if file.name == "_namespace.json":
            continue
        record = load_json(file)
        if record:
            records.append(record)

    accept = request.headers.get("accept", "")

    # JSON response
    if "application/json" in accept:
        return JSONResponse({
            "namespace": namespace_data,
            "records": records
        })

    # JSON-LD response (minimal)
    if "application/ld+json" in accept:
        return JSONResponse({
            "@id": namespace_data.get("openindex"),
            "@type": "Collection",
            "name": namespace_data.get("name"),
            "hasPart": [r.get("openindex") for r in records]
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

# -----------------------------
# Record resolution
# -----------------------------
# Example: /earthpress/tartarian-world
# -----------------------------

@app.get("/{namespace}/{slug}", response_class=HTMLResponse)
async def resolve_record(request: Request, namespace: str, slug: str):
    record_path = RECORDS_DIR / namespace / f"{slug}.json"
    record = load_json(record_path)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    accept = request.headers.get("accept", "")

    # JSON response
    if "application/json" in accept:
        return JSONResponse(record)

    # JSON-LD response (placeholder)
    if "application/ld+json" in accept:
        return JSONResponse({
            "@id": record.get("openindex"),
            "@type": record.get("type"),
            "name": record.get("title")
        })

    # Default: HTML
    return templates.TemplateResponse(
        "record.html",
        {
            "request": request,
            "record": record
        }
    )
