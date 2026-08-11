from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, send_from_directory, send_file, render_template, redirect, session, url_for
from flask_cors import CORS
from utils import *
from mirrorr_be import load_settings, save_settings, load_jobs, load_job, validate_job, load_jobs, save, ensure_defaults, stop, get_log, get_all_log_indices, delete, enable, disable, enable_dryruns, disable_dryruns, purge_job_logs
from scheduler import start_scheduler, get_job_execution
import yaml
from pathlib import Path
from werkzeug.security import check_password_hash
import secrets


logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder='frontend', template_folder='frontend')
app.secret_key = secrets.token_hex(32)
CORS(app)

MIRRORR_ROOT_DIR = "../.."
DATA_DIR = f"{MIRRORR_ROOT_DIR}/data"
JOBS_LOGS_DIR = f"{DATA_DIR}/logs"

MIRROR_VERSION = Path(f"{MIRRORR_ROOT_DIR}/install/.version").read_text().strip()
CREDENTIALS = None



###############   ROUTES   ###############


PUBLIC_ROUTES = {
    "login",
    "logout",
    "css_theme",
    "favicon",
    "icons",
    "font"
}

@app.before_request
def require_login():
    if CREDENTIALS == None or request.endpoint in PUBLIC_ROUTES:
        return

    if not session.get("logged_in"):
        if request.full_path.startswith('/api/') \
            or request.full_path.startswith('/data/') \
            or request.headers.get('Accept', '') == 'application/json':
            return 'Unauthorized', 401

        session["dest"] = request.full_path
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if CREDENTIALS is not None and \
        request.method == "POST" and \
        request.form["username"] == CREDENTIALS['username'] and \
        check_password_hash(CREDENTIALS['password_hash'], request.form["password"]):

        session["logged_in"] = True
        dest = session.pop("dest", "/")

        return redirect(dest)

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route('/')
def index():
    return render_template(
        "index.html", 
        settings = get_render_time_settings())


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route('/css/theme.css')
def css_theme():
    color_theme = load_settings()['color_theme'] + ".css"
    return send_from_directory(app.static_folder, f"css/{color_theme}")


@app.route('/css/bootstrap-icons.css')
def icons():
    return send_from_directory(app.static_folder, "css/bootstrap-icons.css")


@app.route('/css/fonts/<path:font>')
def font(font):
    return send_from_directory(app.static_folder, f"css/fonts/{font}")


@app.route('/<path:path>')
def serve(path):
    if path.endswith('.html'):
        return render_template(
            path, 
            settings = get_render_time_settings())
    return send_from_directory(app.static_folder, path)


# Direct access to job log files
@app.route('/data/logs/<path:path>', methods=['GET'])
def download_log(path):
    return send_file(f"{DATA_DIR}/logs/" + path)


# Direct access to job conf files
@app.route('/data/jobs/<name>', methods=['GET'])
def export_job(name):
    return send_file(f"{DATA_DIR}/jobs/{name}.yaml")


# Direct import to job conf file
@app.route('/data/jobs', methods=['POST'])
def import_job():
    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    job = yaml.safe_load(file)
    violations = validate_job(job, skip_path_existence_check=True)
    if violations:
       return ''.join(f"\n{key}: {value}" for v in violations for key, value in v.items()), 400

    existing_job = load_job(job['name'])
    if existing_job:
        return 'A job with this name already exists', 400

    try:
        save(job | {'enabled': False})
    except Exception as e:
        logger.error(e)
        return f"{e}", 500

    return 'OK', 201


# Direct access to mirrorr conf file
@app.route('/data/settings', methods=['GET'])
def export_mirrorr_conf():
    return send_file(f"{DATA_DIR}/conf.yaml")


# Direct import to mirrorr conf file
@app.route('/data/settings', methods=['POST'])
def import_mirrorr_conf():
    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    save_settings(
        ensure_defaults(
            yaml.safe_load(file.stream)))

    return 'OK', 201


@app.route('/api/jobs', methods=['GET'])
def serve_jobs():
    #TODO Scheduler has a cache of this effectively, and this route is called often
    #Maybe this route is not about the jobs but about the job executions (no plain job listing endpoint then?)
    jobs= load_jobs()

    #Decorate with execution info and logs existence flag
    for job in jobs:
        job.update(get_job_execution(job['name']))
        job.update({'logfile': Path(f"{JOBS_LOGS_DIR}/{job['name']}.log").exists()})

    return jsonify(jobs), 200


@app.route('/api/jobs/<name>', methods=['GET'])
def serve_job(name):
    job = load_job(name)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    #Decorate with execution info
    job.update(get_job_execution(name))

    #Decorate with logs existence flag
    job.update({'logfile': Path(f"{JOBS_LOGS_DIR}/{name}.log").exists()})

    return jsonify(job), 200

@app.route('/api/jobs', methods=['POST'])
def create_job():
    job = request.json

    violations = validate_job(job, request.headers.get('Skip-Path-Existence-Check'))

    existing_job = load_job(job['name'])
    if existing_job:
        violations.append({'name': 'A job with this name already exists'})

    if violations:
        return jsonify({'validation': violations}), 400

    try:
        save(job)
    except Exception as e:
        logger.error(e)
        return jsonify({'error': f"{e}"}), 500

    return jsonify(job), 201


@app.route('/api/jobs/<name>', methods=['PUT'])
def update_job(name):
    job = request.json

    if name != job['name']:
        return jsonify({'validation': 'Job name not equal to path param name'}), 400

    violations = validate_job(job, request.headers.get('Skip-Path-Existence-Check'))
    if violations:
        return jsonify({'validation': violations}), 400

    existing_job = load_job(name)
    if not existing_job:
        return jsonify({'error': 'Job not found'}), 404

    if 'last_run' in existing_job: 
        job['last_run'] = existing_job['last_run']

    try:
        save(job)
    except Exception as e:
        logger.error(e)
        return jsonify({'error': f"{e}"}), 500

    return jsonify(job), 200


@app.route('/api/jobs/<name>', methods=['DELETE'])
def delete_job(name):
    job = load_job(name)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    delete(name)
    return jsonify({'deleted': True}), 200


@app.route('/api/jobs/<name>/toggle', methods=['POST'])
def toggle_job(name):
    data = request.json
    do_enable = data['enable']

    job = load_job(name)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    try:
        if do_enable:
            enable(job)
        else:
            disable(job)
    except Exception as e:
        logger.error(e)
        return jsonify({'error': f"{e}"}), 500

    return jsonify({'success': True})


@app.route('/api/jobs/<name>/dryruns', methods=['POST'])
def toggle_dryruns(name):
    data = request.json
    enable = data['enable']

    job = load_job(name)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    try:
        if enable:
            enable_dryruns(job)
        else:
            disable_dryruns(job)
    except Exception as e:
        logger.error( f"{e}")
        return jsonify({'error': f"{e}"}), 500

    return jsonify({'success': True})


@app.route('/api/jobs/<name>/stop', methods=['GET'])
def stop_job(name):
    job = load_job(name)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    try:
        stop(name)
    except Exception as e:
        logger.error(e)
        return jsonify({'error': f"{e}"}), 500

    return jsonify({'success': True})


@app.route('/api/jobs/<name>/logs', methods=['GET'])
def get_job_logs(name):
    index = request.args.get("index", default=0, type=int)

    # We combine the requested log with all logs for this job
    response = {
        "all-logs": get_all_log_indices(name)
    }

    log = get_log(name, index)
    if log:
        response |= log
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/api/jobs/<name>/logs', methods=['DELETE'])
def delete_job_logs(name):
    job = load_job(name)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    purge_job_logs(name)
    return jsonify({'purged': True}), 200


@app.route('/api/settings', methods=['GET'])
def get_settings():
    settings = load_settings();

    #Decorate with version information
    #TODO I dont like this but it's the only way to find (via the api) what version of mirrorr is running.
    #So, leaving it in for now - perhaps a get_version route is better
    settings['mirrorr_version'] = MIRROR_VERSION
    return jsonify(settings), 200


@app.route('/api/settings', methods=['POST'])
def set_settings():
    settings = request.json
    save_settings(settings)
    return jsonify({'success': True}), 200


def get_render_time_settings():
    settings = load_settings()
    return {
        "mirrorr_version": MIRROR_VERSION,
        "your_brand": settings.get('your_brand', ''),
        "debug_mode": logger.isEnabledFor(logging.DEBUG),
        "ui_refresher_s": settings.get('ui_refresher_s', 60),
        "reverse_cron": settings.get('reverse_cron', "true"),
        "default_ordering": settings.get('default_ordering', 'next-run / desc'),
    }


def setup_logging():
    logger.info("Setting up logging system....")
    log_level = os.getenv("MIRRORR_LOG_LEVEL", "WARNING")

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    handler = RotatingFileHandler(
        "logs/mirrorr-web-be.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=3)

    formatter = logging.Formatter(
        datefmt='%Y-%m-%d, %H:%M:%S',
        fmt='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s'
    )
    handler.setFormatter(formatter)

    # Add a StreamHandler so we can see errors directly in terminal/console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger.addHandler(handler)
    root_logger.addHandler(console_handler)


def setup_auth():
    global CREDENTIALS
    logger.info("Setting up auth")
    
    skip_auth = os.getenv("MIRRORR_USE_AUTH", "true").lower() == "false"

    if skip_auth:
        logger.info("Logins are disabled")
        CREDENTIALS = None
        return
    
    logger.info("Logins are enabled")
    creds_file: Path = Path(DATA_DIR) / ".creds"
    if not creds_file.exists():
        logger.error("❌ Credentials not found ❌")
        raise FileNotFoundError("❌ Credentials not found ❌")

    credentials_str = creds_file.read_text().strip()
    if credentials_str.count(" ") != 1:
        raise ValueError("❌ Credentials entry must contain exactly one space ❌")

    username, hashed_password = credentials_str.split()
    if not username or not hashed_password:
        raise ValueError("❌ Credentials entry is malformed, please recreate ❌")

    try:
        check_password_hash(hashed_password, "")
    except (ValueError, TypeError):
        raise ValueError("❌ Credentials entry is malformed, please recreate ❌")

    CREDENTIALS = {
        "username": username,
        "password_hash": hashed_password
    }        


def start():
    Path(f"{DATA_DIR}/jobs").mkdir(parents=True, exist_ok=True)
    Path(f"{DATA_DIR}/logs").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)

    setup_logging()
    setup_auth()

    logger.info("Mirrorr web service initializing...")      
    settings = load_settings() if Path(f"{DATA_DIR}/conf.yaml").exists() else {}
    save_settings(ensure_defaults(settings))

    start_scheduler()



##### START PROGRAM ######
start()

