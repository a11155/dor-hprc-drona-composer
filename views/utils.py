from flask import request, jsonify, current_app as app
import os
import json
from .error_handler import APIError, handle_api_error
from pathlib import Path
from tempfile import NamedTemporaryFile

from runtime_support.migrate_history import migrate as migrate_legacy_history

import shutil

CONFIG_DIR = Path.home() / ".drona"
CONFIG_FILE = CONFIG_DIR / "config.json"

def create_folder_if_not_exist(dir_path):
    """Create a directory if it doesn't exist"""
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    
def _read_config_json():
    if not CONFIG_FILE.exists():
        return {"ok": False, "reason": f"Config file not found: {CONFIG_FILE}"}
    try:
        cfg = json.loads(CONFIG_FILE.read_text())
        if not isinstance(cfg, dict):
            return {"ok": False, "reason": "Config file must be a JSON object."}
        dd = cfg.get("drona_dir", "")
        if not isinstance(dd, str) or not dd.strip():
            return {"ok": False, "reason": "Config missing 'drona_dir' key."}
        p = Path(dd).expanduser().resolve()
        if not p.exists() or not p.is_dir():
            return {"ok": False, "reason": f"drona_dir does not exist: {p}"}
        return {"ok": True, "cfg": cfg, "drona_dir": str(p)}
    except json.JSONDecodeError:
        return {"ok": False, "reason": "Config file is invalid JSON."}
    except Exception as e:
        return {"ok": False, "reason": f"Failed to read config: {e}"}
        
def _read_config_json():
    if not CONFIG_FILE.exists():
        return {"ok": False, "reason": f"Config file not found: {CONFIG_FILE}"}
    try:
        cfg = json.loads(CONFIG_FILE.read_text())
        if not isinstance(cfg, dict):
            return {"ok": False, "reason": "Config file must be a JSON object."}

        dd = cfg.get("drona_dir", "")
        if not isinstance(dd, str) or not dd.strip():
            return {"ok": False, "reason": "Config missing 'drona_dir' key."}

        # Keep the raw path for comparison (so we can distinguish drona_wfe vs drona_composer)
        raw_path = Path(dd).expanduser()

        resolved = raw_path.resolve()
        if not resolved.exists() or not resolved.is_dir():
            return {"ok": False, "reason": f"drona_dir does not exist: {resolved}"}

        # IMPORTANT: return the raw path, not the resolved one
        return {
            "ok": True,
            "cfg": cfg,
            "drona_dir": str(raw_path),           # e.g. "/scratch/.../drona_wfe"
            "drona_dir_resolved": str(resolved),  # e.g. "/scratch/.../drona_composer"
        }
    except json.JSONDecodeError:
        return {"ok": False, "reason": "Config file is invalid JSON."}
    except Exception as e:
        return {"ok": False, "reason": f"Failed to read config: {e}"}

        
def _write_config_json_atomically(drona_dir_abs: str):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_DIR / "config.tmp"
    data = {"drona_dir": drona_dir_abs}
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, CONFIG_FILE)
    
def _safe_rename(src: Path, dst: Path):
    try:
        os.replace(src, dst)  # atomic if same fs
    except OSError:
        shutil.move(str(src), str(dst))
        
def probe_and_autofix_config():
    """
    1) If ~/.drona/config.json is valid:
         - If it points at $SCRATCH/drona_composer, migrate to drona_wfe.
         - If it points at $SCRATCH/drona_wfe (symlink), do nothing.
         - Otherwise, just return ok.
    2) Else, if $SCRATCH/drona_composer exists -> create a symlink to drona_wfe, write to config.json, return warning.
    3) Else -> ask user to select, we'll create <SELECTED>/drona_wfe later.
    """
    user = os.getenv("USER", "").strip()
    scratch_path = Path("/scratch/user") / user
    dc = scratch_path / "drona_composer"
    target = scratch_path / "drona_wfe"

    # 1) Try existing config first
    r = _read_config_json()
    if r.get("ok"):
        # IMPORTANT: don't resolve here, so we can distinguish the symlink path
        cfg_path = Path(r["drona_dir"]).expanduser()

        # Already pointing at drona_wfe → everything is good
        if cfg_path == target:
            return {
                "ok": True,
                "missing_config": False,
                "drona_dir": str(cfg_path),
                "notice": None,
                "action": "ok",
            }

        # If it's pointing somewhere that is NOT the old drona_composer → also fine
        if cfg_path != dc:
            return {
                "ok": True,
                "missing_config": False,
                "drona_dir": str(cfg_path),
                "notice": None,
                "action": "ok",
            }

        # At this point, cfg_path == dc → config still points at old drona_composer
        if dc.exists():
            try:
                if not target.exists():
                    os.symlink(dc, target)
                _write_config_json_atomically(str(target))
                return {
                    "ok": True,
                    "missing_config": False,
                    "drona_dir": str(target),
                    "notice": (
                        f"Existing config pointed at '{dc}'. Created symlink "
                        f"'{target.name}' -> 'drona_composer' and updated Drona "
                        f"location in ~/.drona/config.json."
                    ),
                    "action": "migrated",
                }
            except Exception as e:
                return {
                    "ok": False,
                    "missing_config": True,
                    "reason": f"Failed to migrate {dc} -> {target}: {e}",
                    "action": "error",
                }

        # Config points at dc, but dc no longer exists → fall through to select-needed

    # 2) No valid config: check for old drona_composer to migrate
    if scratch_path.exists() and dc.exists() and dc.is_dir():
        try:
            if not target.exists():
                os.symlink(dc, target)
            _write_config_json_atomically(str(target))
            return {
                "ok": True,
                "missing_config": False,
                "drona_dir": str(target),
                "notice": (
                    f"Found existing '{dc}'. Created symlink '{target.name}' -> "
                    f"'drona_composer' and updated Drona location in ~/.drona/config.json."
                ),
                "action": "migrated",
            }
        except Exception as e:
            return {
                "ok": False,
                "missing_config": True,
                "reason": f"Failed to migrate {dc} -> {target}: {e}",
                "action": "error",
            }

    # 3) No valid config, no drona_composer to migrate → user must choose a location
    return {
        "ok": True,
        "missing_config": True,
        "reason": "No config found and no $SCRATCH/drona_composer to migrate. Please choose a location.",
        "action": "select_needed",
    }

    
def maybe_migrate_legacy_history():
    """
    If a legacy $SCRATCH/drona_composer/jobs/{USER}_history.json exists
    and we haven't migrated yet, run migrate_history.migrate() once.
    """
    user = (
        os.environ.get("USER")
    )

    # Marker so we don't run this on every request
    marker = CONFIG_DIR / "history_migrated"
    if marker.exists():
        return

    scratch = os.environ.get("SCRATCH") or f"/scratch/user/{user}"
    scratch = os.path.expanduser(os.path.expandvars(scratch))
    json_path = Path(scratch) / "drona_composer" / "jobs" / f"{user}_history.json"

    if not json_path.exists():
        # nothing to migrate
        return

    try:
        # Default behavior of migrate(): no args = use current user + default paths
        migrate_legacy_history(user=None, json_path=None, db_path=None, overwrite=False, delete_json=False)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("ok\n")
        logging.getLogger(__name__).info("Legacy Drona history migrated for user %s", user)
    except FileNotFoundError:
        # JSON vanished between check and run; just skip
        return
    except Exception as e:
        logging.getLogger(__name__).warning("History migration failed for user %s: %s", user, e)


def get_drona_config():
    """
    Returns:
      {"ok": True, "BASE_USER_ROOT": "<str>", "drona_dir": "<str>"}  or
      {"ok": False, "reason": "..."}
    """
    r = _read_config_json()
    if not r.get("ok"):
        p = probe_and_autofix_config()  # may migrate from scratch or say "select_needed"
        if not p.get("ok") or p.get("missing_config"):
            return {"ok": False, "reason": p.get("reason", "Config not available")}
        dd = Path(p["drona_dir"]).expanduser().resolve()
        return {"ok": True, "BASE_USER_ROOT": str(dd.parent), "drona_dir": str(dd)}

    dd = Path(r["drona_dir"]).expanduser().resolve()
    if not dd.exists() or not dd.is_dir():
        return {"ok": False, "reason": f"drona_dir does not exist: {dd}"}

    return {"ok": True, "BASE_USER_ROOT": str(dd.parent), "drona_dir": str(dd)}

def get_drona_dir():
    """
    Returns:
      {"ok": True, "drona_dir": "<str>"} or {"ok": False, "reason": "..."}
    """
    cfg = get_drona_config()
    if not cfg.get("ok"):
        return {"ok": False, "reason": cfg.get("reason", "Unknown error")}
    return {"ok": True, "drona_dir": cfg["drona_dir"]}

def get_envs_dir():
    g = get_drona_dir()
    if not g.get("ok"):
        return {"ok": False, "reason": g.get("reason", "drona_dir not configured")}
    return {"ok": True, "path": os.path.join(g["drona_dir"], "environments")}

def get_runs_dir():
    g = get_drona_dir()
    if not g.get("ok"):
        return {"ok": False, "reason": g.get("reason", "drona_dir not configured")}
    return {"ok": True, "path": os.path.join(g["drona_dir"], "runs")}

@handle_api_error
def get_main_paths_route():
    """Get system and user paths for file operations"""
    default_paths = request.args.get('defaultPaths')
    use_hpc_default_paths = request.args.get('useHPCDefaultPaths')

    paths = {"/": "/"}

    if use_hpc_default_paths != "False" and use_hpc_default_paths != "false":
        current_user = os.getenv("USER")
        group_names = os.popen(f'groups {current_user}').read().split(":")[1].split()
        group_names = [s.strip() for s in group_names]

        paths["Home"] = f"/home/{current_user}"
        paths["Scratch"] = f"/scratch/user/{current_user}"

        for group_name in group_names:
            groupdir = f"/scratch/group/{group_name}"
            if os.path.exists(groupdir):
                paths[group_name] = groupdir

    if default_paths:
        try:
            custom_paths = json.loads(default_paths)
            for key, path in custom_paths.items():
                expanded_path = os.path.expandvars(path)
                paths[key] = expanded_path
        except Exception as e:
            raise APIError(
                "Failed to handle paths",
                status_code=400,
                details=str(e)
            )
    
    return jsonify(paths)

def register_utility_routes(blueprint):
    """Register all utility routes to the blueprint"""
    blueprint.route('/mainpaths', methods=['GET'])(get_main_paths_route)
