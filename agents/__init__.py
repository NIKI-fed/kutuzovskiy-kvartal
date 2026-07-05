import json
import os
import re
import uuid
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
from werkzeug.utils import secure_filename

from agents.db import (
    PLANS_DIR,
    PLANS_URL_PREFIX,
    close_db,
    get_db,
    init_db,
    register_agent,
)

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


# ── Admin: flats management ───────────────────────────────────────────────────

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _allowed_image(filename: str) -> bool:
    ext = os.path.splitext(filename or "")[1].lower().lstrip(".")
    return ext in ALLOWED_IMAGE_EXTENSIONS


def _save_plan_images(files) -> list:
    """Persist uploaded plan images and return their public URLs."""
    saved = []
    os.makedirs(PLANS_DIR, exist_ok=True)
    for f in files:
        if not f or not f.filename or not _allowed_image(f.filename):
            continue
        ext = os.path.splitext(f.filename)[1].lower()
        name = f"{uuid.uuid4().hex}{ext}"
        f.save(os.path.join(PLANS_DIR, secure_filename(name)))
        saved.append(f"{PLANS_URL_PREFIX}/{name}")
    return saved


def _delete_plan_file(url: str) -> None:
    """Remove an uploaded plan file from disk (only inside the plans folder)."""
    if not url or not url.startswith(PLANS_URL_PREFIX + "/"):
        return
    rel = url[len(PLANS_URL_PREFIX) + 1:].replace("\\", "/").lstrip("/")
    if not rel or "/" in rel or ".." in rel:
        return
    target = os.path.join(PLANS_DIR, rel)
    try:
        if os.path.isfile(target):
            os.remove(target)
    except OSError:
        pass


def _flat_form_values(flat=None, form=None) -> dict:
    if form is not None:
        return {
            "house_id": form.get("house_id", ""),
            "floor": form.get("floor", ""),
            "flat_number": form.get("flat_number", ""),
            "rooms": form.get("rooms", ""),
            "area_m2": form.get("area_m2", ""),
            "price_per_m2": form.get("price_per_m2", ""),
            "price": form.get("price", ""),
            "status": form.get("status", "available"),
        }
    if flat is not None:
        ppm = flat["price_per_m2"] if flat["price_per_m2"] else 0
        return {
            "house_id": flat["house_id"],
            "floor": flat["floor"],
            "flat_number": flat["flat_number"],
            "rooms": flat["rooms"],
            "area_m2": f'{flat["area_m2"]:g}',
            "price_per_m2": f"{ppm:g}" if ppm else "",
            "price": flat["price"],
            "status": flat["status"],
        }
    return {
        "house_id": "",
        "floor": "",
        "flat_number": "",
        "rooms": "1",
        "area_m2": "",
        "price_per_m2": "",
        "price": "",
        "status": "available",
    }


def _validate_flat(db, form):
    """Validate submitted flat fields. Returns (data_dict, errors_list)."""
    errors = []
    house_id = form.get("house_id", "").strip()
    flat_number = form.get("flat_number", "").strip()
    floor = form.get("floor", "").strip()
    rooms = form.get("rooms", "").strip()
    area_m2 = form.get("area_m2", "").strip()
    price_per_m2 = form.get("price_per_m2", "").strip()
    price = form.get("price", "").strip()
    status = form.get("status", "available")

    house_id_i = None
    if house_id and house_id.lstrip("-").isdigit():
        if db.execute("SELECT 1 FROM houses WHERE id = ?", (house_id,)).fetchone():
            house_id_i = int(house_id)
    if house_id_i is None:
        errors.append("Выберите дом")

    if not flat_number:
        errors.append("Укажите номер квартиры")
    try:
        floor_i = int(floor)
        if floor_i < 0:
            raise ValueError
    except ValueError:
        errors.append("Этаж должен быть неотрицательным целым числом")
        floor_i = 0
    try:
        rooms_i = int(rooms) if rooms else 1
        if rooms_i < 0:
            raise ValueError
    except ValueError:
        errors.append("Количество комнат должно быть целым числом")
        rooms_i = 1
    try:
        area_f = float(area_m2.replace(",", "."))
        if area_f <= 0:
            raise ValueError
    except ValueError:
        errors.append("Общая площадь должна быть положительным числом")
        area_f = 0.0
    try:
        ppm_f = float(price_per_m2.replace(",", ".")) if price_per_m2 else 0.0
        if ppm_f < 0:
            raise ValueError
    except ValueError:
        errors.append("Цена за м² должна быть числом")
        ppm_f = 0.0
    try:
        price_i = int(float(price.replace(",", "."))) if price else 0
        if price_i < 0:
            raise ValueError
    except ValueError:
        errors.append("Общая стоимость должна быть числом")
        price_i = 0
    if status not in ("available", "reserved", "sold"):
        status = "available"
    # Auto-compute total price when only area and price per m² were provided.
    if not price and area_f > 0 and ppm_f > 0:
        price_i = int(round(area_f * ppm_f))

    data = {
        "house_id": house_id_i,
        "flat_number": flat_number,
        "floor": floor_i,
        "rooms": rooms_i,
        "area_m2": area_f,
        "price_per_m2": ppm_f,
        "price": price_i,
        "status": status,
    }
    return data, errors


def _decode_images(raw) -> list:
    try:
        images = json.loads(raw) if raw else []
    except (TypeError, ValueError):
        images = []
    return [img for img in images if isinstance(img, str)]


@agents_bp.route("/admin/flats")
@admin_required
def admin_flats():
    db = get_db()
    flats = db.execute(
        "SELECT f.id, f.flat_number, f.floor, f.rooms, f.area_m2, f.price, f.price_per_m2, "
        "f.status, h.name AS house_name, h.id AS house_id "
        "FROM flats f JOIN houses h ON h.id = f.house_id "
        "ORDER BY h.id, f.floor, f.flat_number"
    ).fetchall()
    return render_template("agents/admin_flats.html", flats=flats)


@agents_bp.route("/admin/flats/new", methods=["GET", "POST"])
@admin_required
def admin_flat_new():
    db = get_db()
    houses = db.execute("SELECT id, name FROM houses ORDER BY id").fetchall()

    if request.method == "POST":
        data, errors = _validate_flat(db, request.form)
        if errors:
            return render_template(
                "agents/admin_flat_form.html",
                houses=houses,
                values=_flat_form_values(form=request.form),
                images=[],
                is_edit=False,
                error="; ".join(errors),
            )
        new_urls = _save_plan_images(request.files.getlist("plan"))
        cur = db.execute(
            "INSERT INTO flats "
            "(house_id, flat_number, floor, rooms, area_m2, price_per_m2, price, status, plan_images) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                data["house_id"], data["flat_number"], data["floor"], data["rooms"],
                data["area_m2"], data["price_per_m2"], data["price"], data["status"],
                json.dumps(new_urls),
            ),
        )
        db.commit()
        flash("Квартира добавлена", "success")
        return redirect(url_for("agents.admin_flat_edit", flat_id=cur.lastrowid))

    return render_template(
        "agents/admin_flat_form.html",
        houses=houses,
        values=_flat_form_values(),
        images=[],
        is_edit=False,
        error=None,
    )


@agents_bp.route("/admin/flats/<int:flat_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_flat_edit(flat_id):
    db = get_db()
    flat = db.execute("SELECT * FROM flats WHERE id = ?", (flat_id,)).fetchone()
    if flat is None:
        abort(404)
    houses = db.execute("SELECT id, name FROM houses ORDER BY id").fetchall()
    images = _decode_images(flat["plan_images"])

    if request.method == "POST":
        data, errors = _validate_flat(db, request.form)
        if errors:
            return render_template(
                "agents/admin_flat_form.html",
                houses=houses,
                values=_flat_form_values(form=request.form),
                images=images,
                is_edit=True,
                flat_id=flat_id,
                error="; ".join(errors),
            )
        images = images + _save_plan_images(request.files.getlist("plan"))
        db.execute(
            "UPDATE flats SET house_id = ?, flat_number = ?, floor = ?, rooms = ?, "
            "area_m2 = ?, price_per_m2 = ?, price = ?, status = ?, plan_images = ? "
            "WHERE id = ?",
            (
                data["house_id"], data["flat_number"], data["floor"], data["rooms"],
                data["area_m2"], data["price_per_m2"], data["price"], data["status"],
                json.dumps(images), flat_id,
            ),
        )
        db.commit()
        flash("Квартира обновлена", "success")
        return redirect(url_for("agents.admin_flat_edit", flat_id=flat_id))

    return render_template(
        "agents/admin_flat_form.html",
        houses=houses,
        values=_flat_form_values(flat=flat),
        images=images,
        is_edit=True,
        flat_id=flat_id,
        error=None,
    )


@agents_bp.route("/admin/flats/<int:flat_id>/images/delete", methods=["POST"])
@admin_required
def admin_flat_image_delete(flat_id):
    db = get_db()
    flat = db.execute("SELECT * FROM flats WHERE id = ?", (flat_id,)).fetchone()
    if flat is None:
        abort(404)
    target = request.form.get("image", "")
    images = _decode_images(flat["plan_images"])
    if target in images:
        _delete_plan_file(target)
        images = [u for u in images if u != target]
        db.execute(
            "UPDATE flats SET plan_images = ? WHERE id = ?",
            (json.dumps(images), flat_id),
        )
        db.commit()
        flash("План удалён", "success")
    return redirect(url_for("agents.admin_flat_edit", flat_id=flat_id))


@agents_bp.route("/admin/flats/<int:flat_id>/delete", methods=["POST"])
@admin_required
def admin_flat_delete(flat_id):
    db = get_db()
    flat = db.execute("SELECT * FROM flats WHERE id = ?", (flat_id,)).fetchone()
    if flat is None:
        abort(404)
    for url in _decode_images(flat["plan_images"]):
        _delete_plan_file(url)
    db.execute("DELETE FROM reservations WHERE flat_id = ?", (flat_id,))
    db.execute("DELETE FROM flats WHERE id = ?", (flat_id,))
    db.commit()
    flash("Квартира удалена", "success")
    return redirect(url_for("agents.admin_flats"))
