from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, send_from_directory, send_file, render_template
from flask_cors import CORS
from utils import *
from mirrorr_be import load_settings, save_settings, load_jobs, validate_job, load_jobs, save, ensure_defaults, stop, get_log, get_all_log_indices, delete, enable, disable, enable_dryruns, disable_dryruns, purge_job_logs
from scheduler import start_scheduler, get_job_execution
import yaml
from pathlib import Path


logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder='frontend', template_folder='frontend')
CORS(app)

DATA_DIR = '../../data'
MIRROR_VERSION = Path("../../install/.version").read_text().strip()


###############   ROUTES   ###############

@app.route('/')
def index():
    return render_template(
        "index.html", 
        settings = get_render_time_settings())


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')

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
    jobs = load_jobs()
    existing_job = next((j for j in jobs if j['name'] == job['name']), None)
    if existing_job:
        return 'A job with this name already exists', 400

    violations = validate_job(job, skip_path_existence_check=True)
    if violations:
       return ''.join(f"\n{key}: {value}" for v in violations for key, value in v.items()), 400

    try:
        save(job | {'enabled': False})
    except Exception as e:
        logger.error(e)
        return f"{e}", 500

    return 'OK'


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

    return 'OK'


@app.route('/css/theme.css')
def get_css_theme():
    color_theme = load_settings()['color_theme'] + ".css"
    return send_from_directory(app.static_folder, f"css/{color_theme}")


@app.route('/<path:path>')
def serve(path):
    if path.endswith('.html'):
        return render_template(
            path, 
            settings = get_render_time_settings())
    return send_from_directory(app.static_folder, path)


@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    jobs= load_jobs()

    #Decorate with execution info
    for job in jobs:
        job.update(get_job_execution(job['name']))

    return jsonify(jobs), 200


@app.route('/api/jobs/<name>', methods=['GET'])
def get_job(name):
    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(job), 201

@app.route('/api/jobs', methods=['POST'])
def create_job():
    job = request.json

    violations = validate_job(job, request.headers.get('Skip-Path-Existence-Check'))

    jobs = load_jobs()
    existing_job = next((j for j in jobs if j['name'] == job['name']), None)
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

    jobs = load_jobs()
    existing_job = next((j for j in jobs if j['name'] == name), None)
    if not existing_job:
        return jsonify({'error': 'Job not found'}), 404

    if 'last_run' in existing_job: 
        job['last_run'] = existing_job['last_run']

    try:
        save(job)
    except Exception as e:
        logger.error(e)
        return jsonify({'error': f"{e}"}), 500

    return jsonify(job), 201


@app.route('/api/jobs/<name>', methods=['DELETE'])
def delete_job(name):
    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    delete(name)
    return jsonify({'deleted': True}), 200


@app.route('/api/jobs/<name>/toggle', methods=['POST'])
def toggle_job(name):
    data = request.json
    do_enable = data['enable']

    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)
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

    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)
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
    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)
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
    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)
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
        "your_brand": settings.get('your_brand', '')
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


def start():
    Path(f"{DATA_DIR}/jobs").mkdir(parents=True, exist_ok=True)
    Path(f"{DATA_DIR}/logs").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)

    setup_logging()
    logger.info("Mirrorr web service initializing...")
    
    settings = load_settings() if Path(f"{DATA_DIR}/conf.yaml").exists() else {}
    save_settings(ensure_defaults(settings))

    start_scheduler()



##### START PROGRAM ######
start()

