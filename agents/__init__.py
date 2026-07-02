import json
import re
from functools import wraps

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from agents.db import close_db, get_db, init_db, register_agent

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


# ── Validation helpers ────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _valid_phone(phone: str) -> bool:
    return len(re.sub(r"\D", "", phone or "")) >= 11


# ── Auth ──────────────────────────────────────────────────────────────────────

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("agent_id"):
            return redirect(url_for("agents.login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("agent_id"):
            return redirect(url_for("agents.login"))
        if not session.get("is_admin"):
            abort(403)
        return view(*args, **kwargs)

    return wrapped


# ── Routes ────────────────────────────────────────────────────────────────────

@agents_bp.route("/")
def index():
    if not session.get("agent_id"):
        return redirect(url_for("agents.login"))
    if session.get("is_admin"):
        return redirect(url_for("agents.admin_reservations"))
    return redirect(url_for("agents.houses"))


@agents_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("agent_id"):
        return redirect(
            url_for("agents.admin_reservations")
            if session.get("is_admin") else url_for("agents.houses")
        )

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
            session["is_admin"] = bool(agent["is_admin"])
            return redirect(
                url_for("agents.admin_reservations")
                if session["is_admin"] else url_for("agents.houses")
            )
        error = "Неверный логин или пароль"

    return render_template("agents/login.html", error=error)


@agents_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("agent_id"):
        return redirect(url_for("agents.houses"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        if len(name) < 2:
            return render_template(
                "agents/register.html", error="Имя должно содержать минимум 2 символа",
                name=name, username=username,
            )
        if len(username) < 3:
            return render_template(
                "agents/register.html", error="Логин должен содержать минимум 3 символа",
                name=name, username=username,
            )
        try:
            password = register_agent(get_db(), username, name)
        except ValueError as exc:
            return render_template(
                "agents/register.html", error=str(exc), name=name, username=username,
            )
        return render_template(
            "agents/register_done.html", username=username, password=password,
        )

    return render_template("agents/register.html", error=None)


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

    reservation = None
    is_owner = False
    is_admin = bool(session.get("is_admin"))
    if flat["status"] == "reserved":
        reservation = db.execute(
            "SELECT r.*, a.name AS agent_name, a.username AS agent_username "
            "FROM reservations r JOIN agents a ON a.id = r.agent_id "
            "WHERE r.flat_id = ?",
            (flat_id,),
        ).fetchone()
        is_owner = (
            not is_admin
            and reservation is not None
            and reservation["agent_id"] == session.get("agent_id")
        )

    return render_template(
        "agents/flat.html",
        flat=flat,
        house=house,
        images=images,
        reservation=reservation,
        is_owner=is_owner,
        is_admin=is_admin,
    )


@agents_bp.route("/houses/<int:house_id>/flats/<int:flat_id>/reserve", methods=["POST"])
@login_required
def reserve_flat(house_id, flat_id):
    if session.get("is_admin"):
        abort(403)
    db = get_db()
    flat = db.execute(
        "SELECT * FROM flats WHERE id = ? AND house_id = ?", (flat_id, house_id)
    ).fetchone()
    if flat is None:
        abort(404)

    client_name = request.form.get("client_name", "").strip()
    client_phone = request.form.get("client_phone", "").strip()
    client_email = request.form.get("client_email", "").strip()

    if len(client_name) < 2:
        flash("Укажите имя клиента (минимум 2 символа)", "error")
        return redirect(url_for("agents.flat", house_id=house_id, flat_id=flat_id))
    if not _valid_phone(client_phone):
        flash("Введите корректный номер телефона клиента", "error")
        return redirect(url_for("agents.flat", house_id=house_id, flat_id=flat_id))
    if client_email and not _EMAIL_RE.match(client_email):
        flash("Введите корректный email или оставьте поле пустым", "error")
        return redirect(url_for("agents.flat", house_id=house_id, flat_id=flat_id))

    if flat["status"] != "available":
        flash("Квартира уже забронирована", "error")
        return redirect(url_for("agents.flat", house_id=house_id, flat_id=flat_id))

    agent_id = session.get("agent_id")
    db.execute("BEGIN IMMEDIATE")
    try:
        cur = db.execute(
            "INSERT INTO reservations (flat_id, agent_id, client_name, client_phone, client_email) "
            "VALUES (?, ?, ?, ?, ?)",
            (flat_id, agent_id, client_name, client_phone, client_email),
        )
        db.execute(
            "UPDATE flats SET status = 'reserved' WHERE id = ? AND status = 'available'",
            (flat_id,),
        )
        db.commit()
    except Exception:
        db.rollback()
        flash("Не удалось забронировать квартиру — возможно, она только что занята", "error")
        return redirect(url_for("agents.flat", house_id=house_id, flat_id=flat_id))

    flash("Квартира забронирована", "success")
    return redirect(url_for("agents.flat", house_id=house_id, flat_id=flat_id))


@agents_bp.route("/houses/<int:house_id>/flats/<int:flat_id>/cancel", methods=["POST"])
@login_required
def cancel_reservation(house_id, flat_id):
    if session.get("is_admin"):
        abort(403)
    db = get_db()
    reservation = db.execute(
        "SELECT * FROM reservations WHERE flat_id = ?", (flat_id,)
    ).fetchone()
    if reservation is None:
        abort(404)
    if reservation["agent_id"] != session.get("agent_id"):
        flash("Снять бронь может только агент, который её оформил", "error")
        return redirect(url_for("agents.flat", house_id=house_id, flat_id=flat_id))

    db.execute("DELETE FROM reservations WHERE id = ?", (reservation["id"],))
    db.execute("UPDATE flats SET status = 'available' WHERE id = ?", (flat_id,))
    db.commit()
    flash("Бронь снята, квартира снова свободна", "success")
    return redirect(url_for("agents.flat", house_id=house_id, flat_id=flat_id))


@agents_bp.route("/admin/reservations")
@admin_required
def admin_reservations():
    db = get_db()
    reservations = db.execute(
        "SELECT r.id, r.client_name, r.client_phone, r.client_email, r.created_at, "
        "a.name AS agent_name, a.username AS agent_username, "
        "f.flat_number, f.floor, f.rooms, f.area_m2, f.price, f.status, "
        "h.name AS house_name, h.id AS house_id, f.id AS flat_id "
        "FROM reservations r "
        "JOIN agents a ON a.id = r.agent_id "
        "JOIN flats f ON f.id = r.flat_id "
        "JOIN houses h ON h.id = f.house_id "
        "ORDER BY r.created_at DESC, r.id DESC"
    ).fetchall()
    return render_template("agents/admin_reservations.html", reservations=reservations)
