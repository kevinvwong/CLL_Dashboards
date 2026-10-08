"""The in-app guide: render committed docs/*.md, curated by a manifest.

The guide is single-sourced from the repository's own markdown so it cannot
drift from the docs a developer reads. A manifest (docs/guide.yaml) chooses
which files appear, in what order and group, and to which audience (user or
technical). Files are read from Config().DOCS_PATH and rendered with
Python-Markdown, then sanitised with bleach so a document can never inject
script into the app.

Rendering is cached by (path, mtime), so a request re-reads only when a file
changes. Path safety: a manifest entry that escapes the docs root is refused.
"""
import os
import threading

from markupsafe import Markup

from app.config import Config

try:
    import yaml
except ImportError:  # pragma: no cover - the dependency is in requirements.txt
    yaml = None

# Sanitiser allow-list: the HTML Python-Markdown emits for ordinary documents.
_ALLOWED_TAGS = [
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "hr", "blockquote",
    "ul", "ol", "li", "dl", "dt", "dd", "table", "thead", "tbody", "tr",
    "th", "td", "code", "pre", "em", "strong", "a", "img", "sup", "sub",
]
_ALLOWED_ATTRS = {"a": ["href", "title"], "img": ["src", "alt", "title"]}

_CACHE = {}
_LOCK = threading.Lock()


def _docs_root() -> str:
    root = os.path.abspath(Config().DOCS_PATH)
    return root


def _safe_join(root: str, rel: str):
    """An absolute path inside the docs root, or None if it escapes."""
    candidate = os.path.abspath(os.path.join(root, rel))
    if candidate == root or candidate.startswith(root + os.sep):
        return candidate
    return None


def load_manifest() -> list[dict]:
    """The guide manifest, as a list of entries with a resolved absolute path.

    Each entry: slug, title, group, order, audience, path, exists. An entry whose
    file is missing is kept (so the index can show it as unavailable) but flagged.
    """
    root = _docs_root()
    manifest_path = os.path.join(root, "guide.yaml")
    if yaml is None or not os.path.exists(manifest_path):
        return []
    with open(manifest_path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    entries = raw.get("chapters", raw) if isinstance(raw, dict) else raw
    out = []
    for index, entry in enumerate(entries or []):
        rel = str(entry.get("path", "")).strip()
        joined = _safe_join(root, rel) if rel else None
        out.append({
            "slug": str(entry.get("slug") or rel.replace("/", "-")).strip(),
            "title": str(entry.get("title") or rel),
            "group": str(entry.get("group") or "Guide"),
            "order": int(entry.get("order", index)),
            "audience": str(entry.get("audience") or "user"),
            "path": joined,
            "exists": bool(joined and os.path.exists(joined)),
        })
    out.sort(key=lambda e: (e["order"], e["title"]))
    return out


def _render_file(path: str) -> str:
    """Read and render one markdown file to sanitised HTML (mtime-cached)."""
    import bleach
    import markdown

    mtime = os.path.getmtime(path)
    cached = _CACHE.get(path)
    if cached and cached[0] == mtime:
        return cached[1]
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    html = markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists", "toc", "attr_list"])
    clean = bleach.clean(
        html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS,
        protocols=["http", "https", "mailto"], strip=True)
    with _LOCK:
        _CACHE[path] = (mtime, clean)
    return clean


def chapter(slug: str):
    """The rendered chapter for a slug, or None if there is no such chapter."""
    for entry in load_manifest():
        if entry["slug"] == slug and entry["exists"]:
            return {**entry, "html": Markup(_render_file(entry["path"]))}
    return None


def audience_of(slug: str) -> str:
    for entry in load_manifest():
        if entry["slug"] == slug:
            return entry["audience"]
    return "user"
