import csv
import os
import re
from datetime import datetime
from flask import Flask, send_from_directory, request, jsonify

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(BASE_DIR, 'testing')

app = Flask(__name__, static_folder=SITE_DIR, static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-me')


# ── Agents cabinet ───────────────────────────────────────────────────────────
from agents import agents_bp, init_db  # noqa: E402

app.register_blueprint(agents_bp)
init_db()


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
    return send_from_directory(SITE_DIR, 'index.html')


@app.route('/consent')
def consent():
    return send_from_directory(SITE_DIR, 'consent.html')


@app.route('/cookies')
def cookies():
    return send_from_directory(SITE_DIR, 'cookies.html')


@app.route('/privacy')
def privacy():
    return send_from_directory(SITE_DIR, 'privacy.html')


@app.route('/<path:page>.html')
def site_page(page):
    """Serve any .html file placed in the site directory (e.g. kutuzov.html)."""
    return send_from_directory(SITE_DIR, f'{page}.html')


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
