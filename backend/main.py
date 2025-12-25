from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.api.match import router as match_router
from backend.figma.client import fetch_figma_stub
from backend.web.renderer import fetch_web_stub
from backend.ai.matcher import match_stub

app = FastAPI(
    title="Figma Web Matcher",
    docs_url="/swagger",       # Swagger UI available at /swagger
    redoc_url="/redoc",        # Redoc at /redoc
    openapi_url="/openapi.json"
)

# Allow requests from the browser (use restrictive origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(match_router)

@app.get("/")
def root():
    return {"status": "running"}

@app.post("/match")
def match_proxy(figma_url: Optional[str] = Query(None), website_url: Optional[str] = Query(None)):
    """
    Convenience endpoint for the frontend (matches existing frontend/app.js usage).
    Uses the local stubs in backend/figma/client.py, backend/web/renderer.py and backend/ai/matcher.py.
    """
    figma = fetch_figma_stub(figma_url or "")
    web = fetch_web_stub(website_url or "")
    result = match_stub(figma, web)
    return {"figma": figma, "web": web, "match": result}
