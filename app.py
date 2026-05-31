import csv
import os
import re
from datetime import datetime
from flask import Flask, Blueprint, send_from_directory, request, jsonify

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LANDING_DIR = os.path.join(BASE_DIR, 'kutuzovskiy-kvartal-landing')
TESTING_DIR = os.path.join(BASE_DIR, 'testing')

app = Flask(__name__, static_folder=LANDING_DIR, static_url_path='')

# ── Testing Blueprint ─────────────────────────────────────────────────────────
testing_bp = Blueprint(
    'testing',
    __name__,
    static_folder=TESTING_DIR,
    static_url_path='/',
)


@testing_bp.route('/')
def testing_index():
    return send_from_directory(TESTING_DIR, 'index.html')


@testing_bp.route('/consent')
def testing_consent():
    return send_from_directory(TESTING_DIR, 'consent.html')


@testing_bp.route('/cookies')
def testing_cookies():
    return send_from_directory(TESTING_DIR, 'cookies.html')


@testing_bp.route('/privacy')
def testing_privacy():
    return send_from_directory(TESTING_DIR, 'privacy.html')


@testing_bp.route('/<path:page>.html')
def testing_page(page):
    """Serve any .html file placed in the testing/ directory (e.g. queue1.html)."""
    return send_from_directory(TESTING_DIR, f'{page}.html')


app.register_blueprint(testing_bp, url_prefix='/testing')


# ── CORS ─────────────────────────────────────────────────────────────────────

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


# ── Pages ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(LANDING_DIR, 'index.html')


@app.route('/consent')
def consent():
    return send_from_directory(LANDING_DIR, 'consent.html')


@app.route('/cookies')
def cookies():
    return send_from_directory(LANDING_DIR, 'cookies.html')


@app.route('/privacy')
def privacy():
    return send_from_directory(LANDING_DIR, 'privacy.html')


# ── Form API ─────────────────────────────────────────────────────────────────

@app.route('/api/send', methods=['POST', 'OPTIONS'])
def api_send():
    """Handle callback form submissions and save to CSV."""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()

    # Basic validation
    if not name or len(name) < 2:
        return jsonify({'error': 'Имя должно содержать минимум 2 символа'}), 400

    digits = re.sub(r'\D', '', phone)
    if len(digits) < 11:
        return jsonify({'error': 'Введите корректный номер телефона'}), 400

    # Save to CSV
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'submissions.csv')
    file_exists = os.path.isfile(csv_path)

    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'name', 'phone', 'email'])
        writer.writerow([
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            name,
            phone,
            email,
        ])

    app.logger.info('New submission saved — name: %s, phone: %s', name, phone)

    return jsonify({'status': 'ok', 'message': 'Заявка принята'}), 200


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000)
