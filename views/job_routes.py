from flask import Response, stream_with_context, Blueprint, send_file, render_template, request, jsonify
import os
import re
import subprocess
import threading
import uuid
from .logger import Logger
from .history_manager import JobHistoryManager
from .utils import create_folder_if_not_exist, get_drona_dir
from machine_driver_scripts.engine import Engine
from .file_utils import save_file

logger = Logger()
socketio = None  # Will be initialized when passed from main app

def extract_job_id(submit_response):
    """Extract job ID from the sbatch submission response"""
    match = re.search(r'Submitted batch job (\d+)', submit_response)
    return match.group(1) if match else None

@logger.log_route(
    extract_fields={
        'user': lambda: os.getenv('USER'),
        'env_dir': lambda: request.form.get('env_dir', 'unknown'),
        'job_name': lambda: request.form.get('name','unknown'),
        'env': lambda: request.form.get('runtime', 'unknown')
    },
    format_string="{timestamp} {user} {env_dir}/{env} {job_name}"
)

# def submit_job_route():
#     """HTTP endpoint for job submission"""
#     files = request.files
    
#     params = dict(request.form)


#     # Require a drona_job_id generated during preview
#     drona_job_id = (params.get('drona_job_id') or "").strip()
#     # if not drona_job_id:
#     #     return jsonify({
#     #         'error': 'Missing drona_job_id. Please preview the job before submitting.'
#     #     }), 400

#     # Require a location computed during preview or rerun
#     location = (params.get('location') or "").strip()
#     if not location:
#         return jsonify({
#             'error': 'Missing location. Please preview the job before submitting.'
#         }), 400
#     params['location'] = location

#     # If no job name provided, default to drona_job_id
#     # (location is already computed during preview/rerun)
#     if not params.get('name') or params.get('name').strip() == '':
#         params['name'] = drona_job_id


#     create_folder_if_not_exist(params.get('location'))
    
#     extra_files = files.getlist('files[]')
#     for file in extra_files:
#         save_file(file, params.get('location'))
    
#     engine = Engine()
#     engine.set_environment(params.get('runtime'), params.get('env_dir'))
#     bash_script_path = engine.generate_script(params)
#     driver_script_path = engine.generate_driver_script(params)
    
#     bash_cmd = f"bash {driver_script_path}"

#     history_manager = JobHistoryManager()

#     # Pass job_id to save_job
#     job_record = history_manager.save_job(
#         params,
#         files,
#         {
#             "bash_script":   bash_script_path,
#             "driver_script": driver_script_path
#         },
#         job_id=drona_job_id
#     )

#     # Handle case where save_job returns False on error
#     if not job_record:
#         # Fall back to the generated ID so the route still responds
#         job_record = {'job_id': drona_job_id}

    
#     return jsonify({
#             'bash_cmd': bash_cmd,
#             'drona_job_id': job_record['job_id'],
#             'location' : params.get('location')
#         })

def submit_job_route():
    """HTTP endpoint for job submission (location must already be computed in preview)"""
    files = request.files
    params = request.form.to_dict(flat=True)

    # Require preview to have populated these
    drona_job_id = (params.get("drona_job_id") or "").strip()
    if not drona_job_id:
        return jsonify({
            "error": "Missing drona_job_id. Please preview the job before submitting."
        }), 400

    location = (params.get("location") or "").strip()
    if not location:
        return jsonify({
            "error": "Missing location. Please preview the job before submitting."
        }), 400

    # Do NOT modify location here (preview is the single source of truth)
    params["location"] = location

    # Optional: keep this fallback (does NOT affect location)
    if not (params.get("name") or "").strip():
        params["name"] = drona_job_id

    # Filesystem side effects use the preview-computed location
    create_folder_if_not_exist(location)

    extra_files = files.getlist("files[]")
    for f in extra_files:
        save_file(f, location)

    engine = Engine()
    engine.set_environment(params.get("runtime"), params.get("env_dir"))
    bash_script_path = engine.generate_script(params)
    driver_script_path = engine.generate_driver_script(params)

    bash_cmd = f"bash {driver_script_path}"

    history_manager = JobHistoryManager()
    job_record = history_manager.save_job(
        params,
        files,
        {
            "bash_script": bash_script_path,
            "driver_script": driver_script_path
        },
        job_id=drona_job_id
    ) or {"job_id": drona_job_id}

    return jsonify({
        "bash_cmd": bash_cmd,
        "drona_job_id": job_record["job_id"],
        "location": location,
        "env_name": params.get("env_name"),
        "env_dir": params.get("env_dir")
    })



# def preview_job_route():
#     """Preview a job script without submitting it"""
#     params = dict(request.form)
#     PLACEHOLDER = "$DRONA_WF_ID"

#     def gen_drona_id():
#         return str(int(uuid.uuid4().int & 0xFFFFFFFFF))
    
#     def parse_deprecated_id(raw: str):
#         raw = (raw or "").strip()
#         if raw.endswith("*"):
#             cleaned = raw[:-1].strip()
#             return cleaned, True
#         return raw, False
    
#     # def strip_trailing_job_id(path: str, job_id: str):
#     #     """If path ends with /<job_id> (or /<job_id>*), remove that final component."""
#     #     if not path or not job_id:
#     #         return path
#     #     norm = os.path.normpath(path)
#     #     base = os.path.basename(norm)
#     #     if base == job_id or base == f"{job_id}*":
#     #         return os.path.dirname(norm)
#     #     return path
    
#     def ensure_placeholder_appended(base: str):
#         """Return a template path that ends with /$DRONA_WF_ID (unless it already contains it)."""
#         base = (base or "").strip()
#         if not base:
#             base = os.path.join(get_drona_dir(), "runs")

#         norm = os.path.normpath(base)

#         # If it already has placeholder somewhere, keep it.
#         if PLACEHOLDER in norm:
#             return norm

#         # If it already ends with placeholder, keep it.
#         if os.path.basename(norm) == PLACEHOLDER:
#             return norm

#         # Otherwise append placeholder once.
#         return os.path.join(norm, PLACEHOLDER)

#     def parse_bool(v):
#         # Accept: "true", "1", "yes", "on" => True
#         return str(v).strip().lower() in ("1", "true", "t", "yes", "y", "on")
    
#     # ---------------------------
#     # 1) Read flags / inputs
#     # ---------------------------
#     user_picked_location = parse_bool(params.get("user_picked_location", False))

#     old_id, is_deprecated = parse_deprecated_id(params.get("drona_job_id", ""))

#     name_in = (params.get("name") or "").strip()
#     location_in = (params.get("location") or "").strip()

#     if not location_in:
#         location_in = os.path.join(get_drona_dir(), "runs")

#     # ---------------------------
#     # 2) Decide drona_job_id
#     # ---------------------------
#     if old_id and not is_deprecated:
#         drona_job_id = old_id
#     else:
#         drona_job_id = gen_drona_id()

#     params["drona_job_id"] = drona_job_id

#     # # ---------------------------
#     # # 3) Clean location if deprecated id was embedded
#     # # ---------------------------
#     # location_base = location_in
#     # if is_deprecated and old_id:
#     #     location_base = strip_trailing_job_id(location_in, old_id)

#     # ---------------------------
#     # 4) Determine whether name is user-provided
#     # ---------------------------
#     # "User provided name" means: it's not blank AND not just the old auto-id
#     # and not the current id (in case the form already got injected).
#     user_provided_name = (
#         name_in != "" and
#         name_in != old_id and
#         name_in != drona_job_id
#     )

#     # If user didn't provide a real name, we treat it as auto-named
#     auto_named = not user_provided_name

#     # For auto-named jobs, we set name = drona_job_id
#     if auto_named:
#         params["name"] = drona_job_id
#     else:
#         params["name"] = name_in

#     # ---------------------------
#     # 5) Decide whether to append drona_job_id to location
#     # ---------------------------
#     # Rule:
#     # - If user_picked_location == True OR user provided name => DO NOT append
#     # - Else (auto-named AND not user picked) => append (robustly)
#     should_append = auto_named and (not user_picked_location)

#     location_effective = location_in
#     # Also avoid duplicates / placeholders
#     if should_append:
#         location_effective = ensure_placeholder_appended(location_in)

#     params["location"] = location_effective

#     # ---------------------------
#     # 6) Preview script and return injection fields
#     # ---------------------------
#     engine = Engine()
#     engine.set_environment(params.get("runtime"), params.get("env_dir"))
#     preview_job = engine.preview_script(params)

#     preview_job["drona_job_id"] = drona_job_id
#     preview_job["name"] = params["name"]
#     preview_job["location"] = params["location"]

#     # # Reuse existing drona_job_id if provided, otherwise generate a new one
#     # existing_id = (params.get('drona_job_id') or "").strip()
#     # if existing_id:
#     #     drona_job_id = existing_id
#     # else:
#     #     drona_job_id = str(int(uuid.uuid4().int & 0xFFFFFFFFF))

#     # # Ensure we always have a base location (same as submit_job_route)
#     # location = (params.get('location') or "").strip()
#     # if not location:
#     #     location = os.path.join(get_drona_dir(), 'runs')

#     # unnamed = (not params.get('name') or params.get('name').strip() == '')

#     # # For unnamed jobs, always use drona_job_id as the name
#     # if unnamed:
#     #     params['name'] = drona_job_id
#     #     # For the location, append drona_job_id only if it's not already
#     #     # the last path component to avoid repeated nesting on multiple previews
#     #     if os.path.basename(location) != drona_job_id:
#     #         location = os.path.join(location, drona_job_id)

#     # params['location'] = location
    
#     # engine = Engine()
#     # engine.set_environment(params.get('runtime'), params.get('env_dir'))
#     # preview_job = engine.preview_script(params)

#     # # Attach drona_job_id and effective location so the client
#     # # can reuse them on submit without recomputing
#     # preview_job['drona_job_id'] = drona_job_id
#     # preview_job['location'] = params.get('location')

#     # print("[PREVIEW_JOB]", preview_job)
#     return jsonify(preview_job)

def preview_job_route():
    """Preview a job script without submitting it"""
    params = request.form.to_dict(flat=True)

    def gen_drona_id():
        return str(int(uuid.uuid4().int & 0xFFFFFFFFF))

    def parse_deprecated_id(raw: str):
        raw = (raw or "").strip()
        if raw.endswith("*"):
            return raw[:-1].strip(), True
        return raw, False
    
 
    def parse_bool(v):
        return str(v).strip().lower() in ("1", "true", "t", "yes", "y", "on")

    def strip_trailing_component(path: str, comp: str):
        """If path ends with /comp (or /comp*), remove it."""
        if not path or not comp:
            return path
        norm = os.path.normpath(path)
        base = os.path.basename(norm)
        if base == comp or base == f"{comp}*":
            return os.path.dirname(norm)
        return path

    def ensure_id_appended(base: str, job_id: str):
        """Append /job_id once (avoid repeated nesting)."""
        base = os.path.normpath((base or "").strip())
        if os.path.basename(base) == job_id:
            return base
        return os.path.join(base, job_id)

    # 1) Inputs / flags
    user_picked_location = parse_bool(params.get("user_picked_location", False))
    old_id, is_deprecated = parse_deprecated_id(params.get("drona_job_id", ""))

    name_in = (params.get("name") or "").strip()
    location_in = (params.get("location") or "").strip()
    if not location_in:
        location_in = os.path.join(get_drona_dir(), "runs")

    # 2) Decide drona_job_id
    if old_id and not is_deprecated:
        drona_job_id = old_id
    else:
        drona_job_id = gen_drona_id()
    params["drona_job_id"] = drona_job_id

    # 3) Determine if user provided name
    user_provided_name = (name_in != "" and name_in != old_id and name_in != drona_job_id)
    auto_named = not user_provided_name

    # 4) Set name
    params["name"] = drona_job_id if auto_named else name_in

    # 5) Decide whether to append id into location
    # Rule: if user picked location OR user provided name => don't append id
    should_append = auto_named and (not user_picked_location)

    location_effective = location_in

    if should_append:
        # If deprecated reset, location might end with old_id from older previews → strip it once
        if is_deprecated and old_id:
            location_effective = strip_trailing_component(location_effective, old_id)

        # Now ensure current id appended (once)
        location_effective = ensure_id_appended(location_effective, drona_job_id)

    params["location"] = location_effective

    # 6) Preview
    engine = Engine()
    engine.set_environment(params.get("runtime"), params.get("env_dir"))
    preview_job = engine.preview_script(params)

    # Return fields client injects back into form
    preview_job["drona_job_id"] = drona_job_id
    preview_job["name"] = params["name"]
    preview_job["location"] = params["location"]
    preview_job["env_name"] = params["env_name"]
    preview_job["env_dir"] = params["env_dir"]

    return jsonify(preview_job)



def get_history_route():
    """Get job history for the current user"""
    history_manager = JobHistoryManager()
    return jsonify(history_manager.get_user_history())

def get_job_from_history_route(job_id):
    """Get details for a specific job from history"""
    history_manager = JobHistoryManager()

    job_data = history_manager.get_job(job_id)

    if not job_data:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(job_data)

def register_job_routes(blueprint, socketio_instance=None):
    """Register all job-related routes to the blueprint and initialize socketio"""
    global socketio
    socketio = socketio_instance
    
    # Register HTTP routes
    blueprint.route('/submit', methods=['POST'])(submit_job_route)
    blueprint.route('/preview', methods=['POST'])(preview_job_route)
    blueprint.route('/history', methods=['GET'])(get_history_route)
    blueprint.route('/history/<int:job_id>', methods=['GET'])(get_job_from_history_route)
