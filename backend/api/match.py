from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

router = APIRouter(prefix="/api")

class ExtractRequest(BaseModel):
    url: str

class ExtractResponse(BaseModel):
    links: List[str]

class MatchRequest(BaseModel):
    figma_file_key: str
    figma_token: str
    urls: List[str]

def absolutify(base: str, href: str) -> Optional[str]:
    try:
        return urljoin(base, href)
    except Exception:
        return None

async def extract_links_from_html(url: str) -> List[str]:
    headers = {"User-Agent": "figma-web-matcher/1.0"}
    async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
        html = r.text

    soup = BeautifulSoup(html, "lxml")
    found = set()

    # common tag attributes that can contain links
    for tag, attr in [
        ("a", "href"),
        ("area", "href"),
        ("link", "href"),
        ("img", "src"),
        ("script", "src"),
        ("iframe", "src"),
        ("source", "src"),
        ("form", "action"),
    ]:
        for el in soup.find_all(tag):
            v = el.get(attr)
            if not v:
                continue
            absu = absolutify(url, v)
            if absu:
                found.add(absu)

    # meta refresh
    for meta in soup.find_all("meta", attrs={"http-equiv": "refresh"}):
        content = meta.get("content", "")
        if ";" in content:
            parts = content.split(";", 1)
            if len(parts) > 1:
                urlpart = parts[1].strip()
                if urlpart.lower().startswith("url="):
                    candidate = urlpart[4:].strip().strip("'\"")
                    absu = absolutify(url, candidate)
                    if absu:
                        found.add(absu)

    # normalize and return sorted
    return sorted(found)

async def fetch_figma_file(file_key: str, token: str) -> Dict[str, Any]:
    url = f"https://api.figma.com/v1/files/{file_key}"
    headers = {"X-Figma-Token": token}
    async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
        r = await client.get(url)
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Figma API returned {r.status_code}")
        return r.json()

def collect_text_nodes(node: Dict[str, Any], out: List[Dict[str, str]]):
    if not isinstance(node, dict):
        return
    # node may have 'characters' (text node) or type == 'TEXT'
    name = node.get("name", "")
    text = node.get("characters") or ""
    node_type = node.get("type", "")
    if text or node_type == "TEXT":
        out.append({"id": node.get("id", ""), "name": name, "text": text})
    for c in node.get("children", []) or []:
        collect_text_nodes(c, out)
    return out

@router.post("/extract-links", response_model=ExtractResponse)
async def extract_links(req: ExtractRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="missing url")
    try:
        links = await extract_links_from_html(req.url)
        return {"links": links}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.post("/figma-match")
async def figma_match(req: MatchRequest):
    if not req.figma_file_key or not req.figma_token or not isinstance(req.urls, list):
        raise HTTPException(status_code=400, detail="missing figma_file_key, figma_token or urls")

    try:
        data = await fetch_figma_file(req.figma_file_key, req.figma_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    document = data.get("document", {})
    nodes = collect_text_nodes(document, [])

    # prepare searchable strings
    nodes_norm = []
    for n in nodes:
        searchable = ((n.get("text", "") or "") + " " + (n.get("name", "") or "")).lower()
        nodes_norm.append({**n, "searchable": searchable})

    matches: Dict[str, List[Dict[str, str]]] = {}

    for url in req.urls:
        try:
            parsed = urlparse(url)
        except Exception:
            parsed = None

        domain = parsed.hostname.lower() if parsed and parsed.hostname else ""
        path = (parsed.path or "").lower()
        last_seg = (path.split("/")[-1] if path else "").lower()

        candidates: List[Dict[str, str]] = []

        for n in nodes_norm:
            s = n["searchable"]
            if domain and domain in s:
                candidates.append({"id": n["id"], "name": n["name"], "text": n["text"]})
                continue
            if path and path in s:
                candidates.append({"id": n["id"], "name": n["name"], "text": n["text"]})
                continue
            if last_seg and last_seg in s:
                candidates.append({"id": n["id"], "name": n["name"], "text": n["text"]})
                continue
            # match by host+path segments
            if parsed:
                hostpath = (parsed.netloc + parsed.path).lower()
                if hostpath and hostpath in s:
                    candidates.append({"id": n["id"], "name": n["name"], "text": n["text"]})
                    continue

        # fallback: try matching any significant path segment
        if not candidates and parsed and path:
            segs = [seg for seg in path.split("/") if seg]
            for seg in segs:
                for n in nodes_norm:
                    if seg in n["searchable"]:
                        candidates.append({"id": n["id"], "name": n["name"], "text": n["text"]})
                        if len(candidates) >= 10:
                            break
                if len(candidates) >= 10:
                    break

        # dedupe by id and limit
        seen = set()
        deduped = []
        for c in candidates:
            if c["id"] in seen:
                continue
            seen.add(c["id"])
            deduped.append(c)
            if len(deduped) >= 10:
                break

        matches[url] = deduped

    return {"matches": matches}
