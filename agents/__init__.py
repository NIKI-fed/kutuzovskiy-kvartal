import json
from functools import wraps

from flask import (
    Blueprint,
    abort,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from agents.db import close_db, get_db, init_db

agents_bp = Blueprint(
    "agents",
    __name__,
    url_prefix="/agents",
    static_folder="static",
    template_folder=None,  # use the app-level templates/ folder
)


@agents_bp.record_once
def _register_setup(state):
    state.app.teardown_appcontext(close_db)
    state.app.jinja_env.filters["format_price"] = format_price
    state.app.jinja_env.globals["status_label"] = status_label


# ── Template helpers ──────────────────────────────────────────────────────────

def format_price(value):
    try:
        return f"{int(value):,}".replace(",", " ")
    except (TypeError, ValueError):
        return value


def status_label(status):
    return {
        "available": "Свободна",
        "reserved": "Бронь",
        "sold": "Продана",
    }.get(status, status)


# ── Auth ──────────────────────────────────────────────────────────────────────

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("agent_id"):
            return redirect(url_for("agents.login"))
        return view(*args, **kwargs)

    return wrapped


# ── Routes ────────────────────────────────────────────────────────────────────

@agents_bp.route("/")
def index():
    if session.get("agent_id"):
        return redirect(url_for("agents.houses"))
    return redirect(url_for("agents.login"))


@agents_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("agent_id"):
        return redirect(url_for("agents.houses"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        agent = get_db().execute(
            "SELECT * FROM agents WHERE username = ?", (username,)
        ).fetchone()
        if agent and check_password_hash(agent["password_hash"], password):
            session.clear()
            session["agent_id"] = agent["id"]
            session["agent_name"] = agent["name"] or agent["username"]
            return redirect(url_for("agents.houses"))
        error = "Неверный логин или пароль"

    return render_template("agents/login.html", error=error)


@agents_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("agents.login"))


@agents_bp.route("/houses")
@login_required
def houses():
    rows = get_db().execute("SELECT * FROM houses ORDER BY id").fetchall()
    return render_template("agents/houses.html", houses=rows)


@agents_bp.route("/houses/<int:house_id>")
@login_required
def house(house_id):
    db = get_db()
    house = db.execute("SELECT * FROM houses WHERE id = ?", (house_id,)).fetchone()
    if house is None:
        abort(404)
    flats = db.execute(
        "SELECT * FROM flats WHERE house_id = ? ORDER BY floor, flat_number",
        (house_id,),
    ).fetchall()
    return render_template("agents/house.html", house=house, flats=flats)


@agents_bp.route("/houses/<int:house_id>/flats/<int:flat_id>")
@login_required
def flat(house_id, flat_id):
    db = get_db()
    flat = db.execute(
        "SELECT * FROM flats WHERE id = ? AND house_id = ?", (flat_id, house_id)
    ).fetchone()
    house = db.execute("SELECT * FROM houses WHERE id = ?", (house_id,)).fetchone()
    if flat is None or house is None:
        abort(404)
    try:
        images = json.loads(flat["plan_images"]) if flat["plan_images"] else []
    except (TypeError, ValueError):
        images = []
    return render_template("agents/flat.html", flat=flat, house=house, images=images)
