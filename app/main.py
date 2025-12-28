from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json

app = FastAPI(title="OpenIndex Resolver", version="0.1")

BASE_DIR = Path(__file__).resolve().parent.parent
RECORDS_DIR = BASE_DIR / "records"

templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

def load_record(path: Path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/{namespace}/{slug}", response_class=HTMLResponse)
async def resolve_record(request: Request, namespace: str, slug: str):
    record_path = RECORDS_DIR / namespace / f"{slug}.json"
    record = load_record(record_path)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    accept = request.headers.get("accept", "")

    if "application/json" in accept:
        return JSONResponse(record)

    if "application/ld+json" in accept:
        return JSONResponse(record)

    return templates.TemplateResponse(
        "record.html",
        {"request": request, "record": record}
    )
