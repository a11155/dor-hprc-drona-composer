from flask import Response, stream_with_context, Blueprint, send_file, render_template, request, jsonify, current_app as app
import json
import sqlite3
import re
import os
import pty
import time
import sys
from machine_driver_scripts.engine import Engine
import subprocess
import yaml
from functools import wraps
from .logger import Logger
from .error_handler import APIError, handle_api_error
from .history_manager import JobHistoryManager
from .env_repo_manager import EnvironmentRepoManager

job_composer = Blueprint("job_composer", __name__)
logger = Logger()


@job_composer.route("/")
def composer():
    environments = _get_environments() 
    return render_template("index_no_banner.html", environments=environments)

def get_directories(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

@job_composer.route('/download_file', methods=['POST'])
def download_file():
    # Todo make it use api errors
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    try:
        data = request.get_json()
    except Exception as json_error:
        return jsonify({'error': 'Invalid JSON'}), 400

    filepath = data.get('filepath')
    if not filepath:
        return jsonify({'error': 'No filepath provided'}), 400

    if not os.path.exists(filepath):
        return jsonify({'error': f'File not found: {filepath}'}), 404

    if not os.access(filepath, os.R_OK):
        return jsonify({'error': f'No read permissions for file: {filepath}'}), 403

    try:
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath)
        )
    except PermissionError as pe:
        return jsonify({'error': f'Permission denied: {pe}'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@job_composer.route('/modules', methods=['GET'])
def get_modules():
    query = request.args.get('query')
    toolchain = request.args.get('toolchain')
    modules_db_path = app.config['modules_db_path'] + f'{toolchain}.sqlite3'

    with sqlite3.connect(modules_db_path) as modules_db:
        cursor = modules_db.cursor()
        cursor.execute("SELECT name FROM modules WHERE name LIKE ?", (f'{query}%',))
        results = cursor.fetchall()
        module_names = [result[0] for result in results]

    response_data = {'data': module_names}
    return jsonify(response_data)

@job_composer.route('/environment/<environment>', methods=['GET'])
def get_environment(environment):
    env_dir = request.args.get("src")
    if env_dir is None:
        template_path = os.path.join('environments', environment, 'template.txt')
    else:
        template_path = os.path.join(env_dir, environment, 'template.txt')

    if os.path.exists(template_path):
        template_data = open(template_path, 'r').read()
    else:
        raise FileNotFoundError(f"{os.path.join(env_dir, environment, 'template.txt')} not found")
    
    return template_data

@job_composer.route('/evaluate_dynamic_select', methods=['GET'])
@handle_api_error
def evaluate_dynamic_select():
    retriever_path = request.args.get("retriever_path")
    
    retriever_dir = os.path.dirname(os.path.abspath(retriever_path))
    retriever_script = os.path.basename(retriever_path)
    bash_command = f"bash {retriever_script}"

    try:
        result = subprocess.run(
                bash_command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=retriever_dir
        )
        if result.returncode == 0:
            #TODO: We assume the result is the correct JSON format for a dynamic select
            #options = json.loads(result.stdout)
            options = result.stdout
        else:
            raise APIError(
                "The dynamic select script did not return exit code 0",
                status_code=400,
                details={'error': result.stderr}
                )
    except subprocess.CalledProcessError as e:
        raise APIError(
            "Failed to process dynamic select",
            status_code=500,
            details={'error': str(e)}
    )
    return options

@job_composer.route('/evaluate_autocomplete', methods=['GET'])
@handle_api_error
def evaluate_autocomplete():
    retriever_path = request.args.get("retriever_path")
    query = request.args.get("query")
    
    if not retriever_path:
        raise APIError("Retriever path is required", status_code=400)
    
    if not query:
        raise APIError("Search query is required", status_code=400)
    
    retriever_dir = os.path.dirname(os.path.abspath(retriever_path))
    retriever_script = os.path.basename(retriever_path)
    
    # Pass the query as an environment variable
    env = os.environ.copy()
    env["SEARCH_QUERY"] = query
    
    try:
        result = subprocess.run(
            f"bash {retriever_script}",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=retriever_dir,
            env=env
        )
        
        if result.returncode != 0:
            raise APIError(
                "The autocomplete script did not return exit code 0",
                status_code=400,
                details={'error': result.stderr}
            )
        
        try:
            options = json.loads(result.stdout)
            return jsonify(options)
        except json.JSONDecodeError as e:
            raise APIError(
                "The autocomplete script did not return valid JSON",
                status_code=400, 
                details={'error': str(e), 'output': result.stdout}
            )
            
    except subprocess.CalledProcessError as e:
        raise APIError(
            "Failed to process autocomplete search",
            status_code=500,
            details={'error': str(e), 'stderr': e.stderr}
        )

def iterate_schema(schema_dict):
    """Generator that yields all elements in the schema including nested ones"""
    for key, value in schema_dict.items():
        yield key, value

        if "Container" in value.get("type") and "elements" in value:
            yield from iterate_schema(value["elements"])


@job_composer.route('/schema/<environment>', methods=['GET'])
@handle_api_error
def get_schema(environment):
    env_dir = request.args.get("src")
    if env_dir is None:
        schema_path = os.path.join('environments', environment, 'schema.json')
    else:
        schema_path = os.path.join(env_dir, environment, 'schema.json')

    if os.path.exists(schema_path):
        schema_data = open(schema_path, 'r').read()
    else:
        raise APIError(f"Schema file not found: {schema_path}", status_code=404)
   
    try:
        schema_dict = json.loads(schema_data)
    except json.JSONDecodeError as e:
        raise APIError("Invalid schema JSON", status_code=400, details={'error': str(e)})

    for key, element in iterate_schema(schema_dict):
        if "retriever" in element:
            retriever_path = element["retriever"]
            if not os.path.isabs(retriever_path):
                retriever_path = os.path.join(env_dir, environment, retriever_path)
            element["retrieverPath"] = retriever_path

        if element["type"] == "dynamicSelect":
            element["isEvaluated"] = False
            element["isShown"] = False

    return json.dumps(schema_dict)


@job_composer.route('/map/<environment>', methods=['GET'])
def get_map(environment):
    env_dir = request.args.get("src")
    if env_dir is None:
        map_path = os.path.join('environments', environment, 'map.json')
    else:
        map_path = os.path.join(env_dir, environment, 'map.json')

    if os.path.exists(map_path):
        map_data = open(map_path, 'r').read()
    else:
        raise FileNotFoundError(f"{os.path.join(env_dir, environment, 'map.json')} not found")
    
    return map_data

def create_folder_if_not_exist(dir_path):
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)

def save_file(file, location):
    if not os.path.exists(location):
        os.makedirs(location)

    subpath, filename = os.path.split(file.filename)

    subpath_directory = os.path.join(location, subpath)
    file_path = os.path.join(subpath_directory, filename)

    # Ensure the subpath directory exists
    if not os.path.exists(subpath_directory):
        os.makedirs(subpath_directory)

    # Save the file
    with open(file_path, 'wb') as f:
        f.write(file.read())

    return file_path
    
@job_composer.route('/history', methods=['GET'])
def get_history():
    history_manager = JobHistoryManager()
    return jsonify(history_manager.get_user_history())


@job_composer.route('/history/<int:job_id>', methods=['GET'])
def get_job_from_history(job_id):
    history_manager = JobHistoryManager()
    
    job_data = history_manager.get_job(job_id)

    if not job_data:
        return "Job not found", 404

    return jsonify(job_data)  

def extract_job_id(submit_response):
    match = re.search(r'Submitted batch job (\d+)', submit_response)
    return match.group(1) if match else None


@job_composer.route('/submit', methods=['POST'])
@logger.log_route(
    extract_fields={
        'user': lambda: os.getenv('USER'), 
        'env_dir': lambda: request.form.get('env_dir', 'unknown'),
        'job_name': lambda: request.form.get('name','unknown'), 
        'env': lambda: request.form.get('runtime', 'unknown')
    },
    format_string="{timestamp} {user} {env_dir}/{env} {job_name}"
)
def submit_job():
    params = request.form
    files = request.files

    create_folder_if_not_exist(params.get('location'))

    engine = Engine()
    engine.set_environment(params.get('runtime'), params.get('env_dir'))

    # Saving Files
    # executable_script = save_file(files.get('executable_script'), params.get('location'))
    extra_files = files.getlist('files[]')
    for file in extra_files:
        save_file(file, params.get('location'))

    bash_script_path = engine.generate_script(params)
    driver_script_path = engine.generate_driver_script(params)

    # Use stdbuf to force line-buffered output from bash
    bash_cmd = ["stdbuf", "-oL", "-eL", "bash", driver_script_path]

    history_manager = JobHistoryManager()


    def generate():

        # Spawn the process (no PTY needed)
        proc = subprocess.Popen(
            bash_cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,    # merge stderr
            text=True,                   # str not bytes
            bufsize=1                    # line buffer
        )

        full_output = []
        job_id = None
        try:
            # 2-C: forward every line as soon as it arrives
            for line in proc.stdout:
                yield f"{line.rstrip()}\n\n"
                
                full_output.append(line)
                # Detect job_id once
                
                if ((job_id is None) and (extract := extract_job_id(line))):                    
                    job_id = extract
                    print(f"[DEBUG STREAM] job_id → {job_id}", flush=True)

        finally:
            proc.stdout.close()
            proc.wait()
            rc = proc.returncode

            # ---------- FINAL SSE ----------
            # if rc == 0:
            #     yield "event: done\ndata: {\"status\":\"ok\"}\n\n"
            # else:
            #     yield (
            #         "event: done\ndata: "
            #         f"{json.dumps({'status':'error','code':rc})}\n\n"
            #     )
            # ---------- SAVE TO HISTORY ----------
            if rc == 0 and job_id:
                history_manager.save_job(
                    job_id or extract_job_id("".join(full_output)),
                    params,
                    files,
                    {
                        "bash_script":   bash_script_path,
                        "driver_script": driver_script_path
                    }
                )
            # -------------------------------------

    # ---------- 3.  Flask response ----------
    resp = Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",       # critical for SSE!
        direct_passthrough=True,
    )
    resp.headers["Cache-Control"]     = "no-cache"
    resp.headers["Connection"]        = "keep-alive"
    resp.headers["X-Accel-Buffering"] = "no"       # nginx hint

    return resp

        




################## OLD SUBMIT JOB FUNCTION ################################
# def submit_job():
#     params = request.form
#     files = request.files

#     create_folder_if_not_exist(params.get('location'))

#     engine = Engine()
#     engine.set_environment(params.get('runtime'), params.get('env_dir'))

#     # Saving Files
#     # executable_script = save_file(files.get('executable_script'), params.get('location'))
#     extra_files = files.getlist('files[]')
#     for file in extra_files:
#         save_file(file, params.get('location'))

#     bash_script_path = engine.generate_script(params)
#     driver_script_path = engine.generate_driver_script(params)

#     bash_command = f"bash {driver_script_path}"

#     history_manager = JobHistoryManager()

#     try:
#         result = subprocess.run(bash_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
#         if result.returncode == 0:
#                 history_manager.save_job(
#                     extract_job_id(result.stdout),
#                     params,
#                     files,
#                     {
#                         'bash_script': bash_script_path,
#                         'driver_script': driver_script_path
#                      }
#                 )
#                 return result.stdout
                
#         else:
#             return result.stderr
#     except subprocess.CalledProcessError as e:
#         return e.stderr
    

@job_composer.route('/preview', methods=['POST'])
def preview_job():
    params = request.form
    engine = Engine()
    
    engine.set_environment(params.get('runtime'), params.get('env_dir'))
    preview_job = engine.preview_script(params)

    return jsonify(preview_job)


@job_composer.route('/mainpaths', methods=['GET'])
@handle_api_error
def get_main_paths():
     
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

def fetch_subdirectories(path):
    subdirectories = [os.path.basename(entry) for entry in os.listdir(path) if os.path.isdir(os.path.join(path, entry))]
    subfiles = [os.path.basename(entry) for entry in os.listdir(path) if os.path.isfile(os.path.join(path, entry))]
    return {"subdirectories": subdirectories, "subfiles": subfiles}

@job_composer.route('/subdirectories', methods=['GET'])
def get_subdirectories():
    fullpath = request.args.get('path')
    subdirectories = fetch_subdirectories(fullpath)
    return subdirectories

@job_composer.route('/environments', methods=['GET'])
def get_environments():
    environments = _get_environments()
    return jsonify(environments)


@job_composer.route('/add_environment', methods=['POST'])
@handle_api_error
def add_environment():
    env = request.form.get("env")
    src = request.form.get("src")
    
    if not env:
        raise APIError(
            "Missing environment name parameter",
            status_code=400,
            details={'error': 'The "env" parameter is required'}
        )
        
    cluster_name = app.config['cluster_name']
    repo_manager = EnvironmentRepoManager(
            repo_url=app.config['env_repo_github'],
            repo_dir="./environments-repo"
    )
    user_envs_path = f"/scratch/user/{os.getenv('USER')}/drona_composer/environments"
    
    try:
        repo_manager.copy_environment_to_user(env, user_envs_path)
        return jsonify({"status": "Success"})
    except ValueError as e:
        raise APIError(
            "Invalid input",
            status_code=400,
            details={'error': str(e)}
        )
    except FileNotFoundError as e:
        raise APIError(
            "Environment not found",
            status_code=404,
            details={'error': str(e)}
        )
    except PermissionError as e:
        raise APIError(
            "Permission denied",
            status_code=403,
            details={'error': str(e)}
        )
    except RuntimeError as e:
        raise APIError(
            "Git operation failed",
            status_code=500,
            details={'error': str(e)}
        )
    except Exception as e:
        raise APIError(
            "Unexpected error while adding environment",
            status_code=500,
            details={'error': str(e)}
        )



@job_composer.route('/evaluate_dynamic_text', methods=['GET'])
@handle_api_error
def evaluate_dynamic_text():
    retriever_path = request.args.get("retriever_path")
    
    if not retriever_path:
        raise APIError("Retriever path is required", status_code=400)
    
    retriever_dir = os.path.dirname(os.path.abspath(retriever_path))
    retriever_script = os.path.basename(retriever_path)
    
    env = os.environ.copy()
    
    path = os.path.join(retriever_dir, retriever_script)
    for key, value in request.args.items():
        if key != "retriever_path":
            env[key.upper()] = value
    
    try:
        result = subprocess.run(
            f"bash {path}",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=retriever_dir,
            env=env
        )
        
        if result.returncode != 0:
            raise APIError(
                "The dynamic text script did not return exit code 0",
                status_code=400,
                details={'error': result.stderr}
            )
        
        return result.stdout
            
    except subprocess.CalledProcessError as e:
        raise APIError(
            "Failed to process dynamic text",
            status_code=500,
            details={'error': str(e), 'stderr': e.stderr}
        )


@job_composer.route('/get_more_envs_info', methods=['GET'])
def get_more_envs_info():
    cluster_name = app.config['cluster_name']
    repo_manager = EnvironmentRepoManager(
        repo_url=app.config["env_repo_github"],
        repo_dir="./environments-repo"
    )
    
    environments_info = repo_manager.get_environments_info(cluster_name)
    return jsonify(environments_info)


def _get_environments():
    system_environments = []
    try:
        system_environments = get_directories("./environments")
        system_environments = [{"env": env, "src": "./environments", "is_user_env": False} for env in system_environments]
    except (PermissionError, FileNotFoundError, OSError):
        system_environments = []
    
    user_envs_path = request.args.get("user_envs_path")
    if user_envs_path is None:
        user_envs_path = f"/scratch/user/{os.getenv('USER')}/drona_composer/environments"
        try:
            create_folder_if_not_exist(user_envs_path)
        except (PermissionError, OSError):
            pass
    
    user_environments = []
    try:
        user_environments = get_directories(user_envs_path)
        user_environments = [{"env": env, "src": user_envs_path, "is_user_env": True} for env in user_environments]
    except (PermissionError, FileNotFoundError, OSError):
        user_environments = []
    
    environments = system_environments + user_environments
    return environments

