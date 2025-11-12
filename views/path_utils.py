from pathlib import Path
import os
def expand(s: str) -> str:
    """
    Expand environment variables and user references in a string.
    Returns an expanded string. If s is None or not a string it returns an empty string.
    """
    if not isinstance(s, str):
        return ""
    return os.path.expanduser(os.path.expandvars(s))

def normalize_dir(path_str: str):
    """
    Normalizes a directory path:
    1. Expand env vars
    2. Resolves to an absolute path
    3. Validates that its a directory
    
    Returns a dict:
        ok: bool
        normalized: str | None
        reason: str | None
        raw: str (original input)
    """
    raw = path_str
    if not isinstance(path_str, str) or not path_str.strip():
        return {
                "ok": False, 
                "normalized": None, 
                "reason": "Empty or invalid path", 
                "raw": raw
                }

    expanded = expand(path_str)
    try:
        p = Path(expanded).resolve()
    except Exception as e:
        return {
                "ok": False,
                "normalized": None,
                "reason": f"Failed to resolve path: {e}",
                "raw": raw
                }
    if not p.exists():
        return {
                "ok": False,
                "normalized": str(p),
                "reason": f"Path does not exists: {p}",
                "raw": raw
                }
    if not p.is_dir():
        return {
                "ok": False,
                "normalized": str(p),
                "reason": f"Path is not a directory: {p}", 
                "raw": raw
                }
    return {"ok": True, "normalized": str(p), "reason": None, "raw": raw}

def ensure_allowed_root(path_str: str, allowed_roots: list[str] | None = None) -> dict:
    """
    check that a given path is inside one of the allowed root directories.
    """
    norm = normalize_dir(path_str)
    if not norm["ok"]:
        return norm
    
    if not allowed_roots:
        return norm
    
    normalized = Path(norm["normalized"])
    for root in allowed_roots:
        try:
            root_path = Path(expand(root)).resolve()
            if root_path in normalized.parents or root_path == normalized:
                return norm
        except Exception:
            continue
    norm["ok"] = False
    norm["reason"] = f"Path {normalized} is outside allowed roots: {allowed_roots}"
    return norm

def exists_dir(path_str: str) -> bool:
    """A boolean version of normalize_dir for quick checks."""
    res = normalize_dir(path_str)
    return res["ok"]

def safe_join(base: str, *paths: str) -> str | None:
    """ 
    Join and resolve paths safely, preventing traversal outside base.
    Returns absolute paths or None if unsafe.
    """
    base_path = Path(expand(base)).resolve()
    target = base_path.joinpath(*paths).resolve()
    if base_path in target.parents or base_path == target:
        return str(target)
    return None
