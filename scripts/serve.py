#!/usr/bin/env python3
"""FastAPI server — search and daf lookup over bavli.db + bavli.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from lib.loci import enrich_loci, load_loci, suppression_score
from lib.search_api import get_daf, list_tractates, search_lines

WEB = ROOT / "web"
DB = ROOT / "data" / "bavli.db"
JSON = ROOT / "data" / "bavli.json"
LOCI = ROOT / "data" / "loci.json"
CHART = ROOT / "data" / "loci_chart.json"

app = FastAPI(
    title="Bavli Uncensored",
    description="Search and browse the uncensored Vilna Bavli corpus",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "ok": True,
        "has_db": DB.exists(),
        "has_json": JSON.exists(),
    }


@app.get("/tractates")
def tractates():
    if not JSON.exists():
        raise HTTPException(503, "bavli.json not found — run build_bavli.py")
    return {"tractates": list_tractates(source=JSON)}


@app.get("/search")
def search(
    q: str = Query(..., min_length=1, description="Hebrew search phrase"),
    tractate: str | None = None,
    layer: str | None = Query(None, pattern="^(gemara|rashi|tosafot)$"),
    limit: int = Query(20, ge=1, le=100),
):
    try:
        hits = search_lines(
            q, db_path=DB, tractate=tractate, layer=layer, limit=limit
        )
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e
    return {"query": q, "count": len(hits), "results": hits}


@app.get("/ref/{ref:path}")
def ref_lookup(ref: str):
    ref = ref.replace("_", " ")
    try:
        daf = get_daf(ref, source=JSON)
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e
    if not daf:
        raise HTTPException(404, f"Unknown ref: {ref}")
    return daf


@app.get("/api/loci")
def loci_chart(live: bool = Query(False, description="Re-verify loci against bavli.json")):
    if not live and CHART.exists():
        return json.loads(CHART.read_text(encoding="utf-8"))
    if not LOCI.exists():
        raise HTTPException(503, "loci.json not found")
    data = enrich_loci(load_loci(), bavli_path=JSON)
    for loc in data["loci"]:
        denial = loc.get("denial", {})
        loc["suppression_index"] = suppression_score(denial)
        loc["available_now"] = denial.get("in_build", 3) == 0
    return data


if WEB.is_dir():
    app.mount("/static", StaticFiles(directory=WEB), name="static")

    @app.get("/")
    def index():
        return FileResponse(WEB / "index.html")

    @app.get("/loci")
    def loci_page():
        return FileResponse(WEB / "loci.html")


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765)


if __name__ == "__main__":
    main()
