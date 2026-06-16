from datetime import datetime, timedelta
from secrets import token_urlsafe
import os
import re

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)

app = Flask(__name__)

# Config via env:
#   SECRET_KEY   — clave de sesión (¡obligatoria en producción!) / session key (required in production!)
#   DATABASE_URL — URI de base de datos / Database URI
#   SCRIPT_NAME  — Prefijo de la ruta, por ejemplo "/travelpacker" / route prefix, e.g. "/travelpacker"
#   ADMIN_ALIAS  — Usuario administrador / Admin user
_secret = os.environ.get("SECRET_KEY")
if not _secret:
    import warnings
    warnings.warn(
        "SECRET_KEY no configurada. Se usará una clave aleatoria: "
        "las sesiones no sobrevivirán reinicios.",
        "SECRET_KEY not configured. A random key will be used: "
        "sessions will not survive reboots.",
        stacklevel=1,
    )
    _secret = token_urlsafe(32)

app.config["SECRET_KEY"] = _secret
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


_SCRIPT_NAME = os.environ.get("SCRIPT_NAME", "").rstrip("/")
if _SCRIPT_NAME:
    class _ReverseProxied:

        def __init__(self, wsgi_app, script_name):
            self.app = wsgi_app
            self.script_name = script_name

        def __call__(self, environ, start_response):
            environ["SCRIPT_NAME"] = self.script_name
            path = environ.get("PATH_INFO", "")
            if path.startswith(self.script_name):
                environ["PATH_INFO"] = path[len(self.script_name):]
            return self.app(environ, start_response)

    app.wsgi_app = _ReverseProxied(app.wsgi_app, _SCRIPT_NAME)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "index"

ADMIN_ALIAS = os.environ.get("ADMIN_ALIAS", "atlas-vault-7")
ALIAS_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,31}$")
MAX_NAME_LEN = 100
MAX_NOTES_LEN = 255
VALID_STATUSES = {"unchecked", "packed", "na", "standby"}

TRANSLATIONS = {
    "en": {
        "app_title": "Travel Packer",
        "login_title": "Login / Register",
        "alias_label": "Alias (Username)",
        "login_btn": "Enter",
        "guest_btn": "Continue as Guest",
        "logout": "Logout",
        "privacy_notice": "Notice: Do not enter confidential information. No passwords are required. Aliases are public.",
        "dashboard": "Dashboard",
        "admin_panel": "Admin Panel",
        "my_trips": "My Trips",
        "new_trip": "New Trip",
        "trip_name": "Trip Name",
        "select_categories": "Select Categories",
        "create_trip": "Create Trip",
        "delete": "Delete",
        "go_to_trip": "Open Checklist",
        "status_unchecked": "To Pack",
        "status_packed": "Packed",
        "status_na": "N/A",
        "status_standby": "Standby",
        "notes": "Notes",
        "custom_items": "My Custom Elements",
        "add_category": "Add Category",
        "add_item": "Add Item",
        "name_en": "Name (English)",
        "name_es": "Name (Spanish)",
        "category": "Category",
        "saved": "Saved!",
        "guest_notice": "Guest Mode: Data will be deleted in 24 hours.",
        "security_error": "Security check failed. Please try again.",
        "invalid_alias": "Please use a valid alias: 3-32 characters, letters/numbers/dots/underscores/hyphens.",
        "invalid_trip_name": "Please enter a valid trip name.",
        "invalid_category_name": "Please enter a valid category name.",
        "invalid_item_name": "Please enter a valid item name.",
        "invalid_selection": "Please select at least one valid category.",
        "no_trips": "No trips yet.",
        "no_items": "No custom items yet.",
        "dashboard_empty": "Create your first trip to start packing.",
        "save_failed": "Could not save changes.",
        "trip_deleted": "Trip deleted.",
        "delete_confirm": "Are you sure?",
        "language": "Language",
        "progress_complete": "complete",
        "global_summary": "Global Summary",
        "items_label": "items",
        "and": "and",
        "more": "more",
        "add_quick_item": "Add Quick Item",
        "item_name": "Item Name",
        "select_category": "Select Category",
        "add_to_trip": "Add to Trip",
        "error_adding_item": "Error adding item",
        "item_added": "Item added successfully!",
        "search_items": "Search items...",
        "all": "All",
        "or": "or",
    },
    "es": {
        "app_title": "Equipaje de Viaje",
        "login_title": "Entrar / Registrarse",
        "alias_label": "Alias (Nombre de usuario)",
        "login_btn": "Entrar",
        "guest_btn": "Continuar como Invitado",
        "logout": "Salir",
        "privacy_notice": "Aviso: No introduzcas información confidencial. No se requieren contraseñas. Los alias son visibles.",
        "dashboard": "Panel Principal",
        "admin_panel": "Panel de Admin",
        "my_trips": "Mis Viajes",
        "new_trip": "Nuevo Viaje",
        "trip_name": "Nombre del viaje",
        "select_categories": "Seleccionar Categorías",
        "create_trip": "Crear Viaje",
        "delete": "Borrar",
        "go_to_trip": "Abrir Lista",
        "status_unchecked": "Por empacar",
        "status_packed": "Empacado",
        "status_na": "No Aplica",
        "status_standby": "En Espera",
        "notes": "Notas",
        "custom_items": "Mis Elementos",
        "add_category": "Añadir Categoría",
        "add_item": "Añadir Elemento",
        "name_en": "Nombre (Inglés)",
        "name_es": "Nombre (Español)",
        "category": "Categoría",
        "saved": "¡Guardado!",
        "guest_notice": "Modo Invitado: Los datos se borrarán en 24 horas.",
        "security_error": "La comprobación de seguridad ha fallado. Inténtalo de nuevo.",
        "invalid_alias": "Usa un alias válido: 3-32 caracteres, letras/números/puntos/guiones bajos/guiones.",
        "invalid_trip_name": "Introduce un nombre de viaje válido.",
        "invalid_category_name": "Introduce un nombre de categoría válido.",
        "invalid_item_name": "Introduce un nombre de elemento válido.",
        "invalid_selection": "Selecciona al menos una categoría válida.",
        "no_trips": "Aún no hay viajes.",
        "no_items": "Aún no hay elementos personalizados.",
        "dashboard_empty": "Crea tu primer viaje para empezar a preparar el equipaje.",
        "save_failed": "No se han podido guardar los cambios.",
        "trip_deleted": "Viaje borrado.",
        "delete_confirm": "¿Seguro?",
        "language": "Idioma",
        "progress_complete": "completado",
        "global_summary": "Resumen Global",
        "items_label": "elementos",
        "and": "y",
        "more": "más",
        "add_quick_item": "Añadir Elemento Rápido",
        "item_name": "Nombre del Elemento",
        "select_category": "Seleccionar Categoría",
        "add_to_trip": "Añadir al Viaje",
        "error_adding_item": "Error al añadir el elemento",
        "item_added": "¡Elemento añadido con éxito!",
        "search_items": "Buscar elementos...",
        "all": "Todos",
        "or": "o",
    },
}

def t_key(key: str) -> str:
    lang = session.get("lang", "en")
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

@app.context_processor
def inject_globals():
    def t(key):
        return t_key(key)

    def csrf_token():
        token = session.get("_csrf_token")
        if not token:
            token = token_urlsafe(32)
            session["_csrf_token"] = token
        return token

    return dict(t=t, lang=session.get("lang", "en"), csrf_token=csrf_token)

@app.before_request
def protect_post_requests():
    if request.method != "POST":
        return

    submitted = request.form.get("csrf_token") or request.headers.get("X-CSRFToken") or request.headers.get("X-CSRF-Token")
    expected = session.get("_csrf_token")
    if not expected or not submitted or submitted != expected:
        if request.is_json:
            return jsonify({"error": t_key("security_error")}), 400
        flash(t_key("security_error"), "danger")
        return redirect(request.referrer or url_for("index"))

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(32), unique=True, nullable=False, index=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_guest = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(MAX_NAME_LEN), nullable=False)
    name_es = db.Column(db.String(MAX_NAME_LEN), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    items = db.relationship("Item", backref="category", lazy="selectin", cascade="all, delete-orphan")

class Item(db.Model):
    __tablename__ = "item"
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False, index=True)
    name_en = db.Column(db.String(MAX_NAME_LEN), nullable=False)
    name_es = db.Column(db.String(MAX_NAME_LEN), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    trip_items = db.relationship("TripItem", backref="item", lazy="selectin", cascade="all, delete-orphan")

class Trip(db.Model):
    __tablename__ = "trip"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(MAX_NAME_LEN), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    items = db.relationship("TripItem", backref="trip", lazy="selectin", cascade="all, delete-orphan")

class TripItem(db.Model):
    __tablename__ = "trip_item"
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False, index=True)
    status = db.Column(db.String(20), default="unchecked", nullable=False)
    notes = db.Column(db.String(MAX_NOTES_LEN), default="", nullable=False)

    __table_args__ = (
        db.Index("ix_trip_item_trip_item", "trip_id", "item_id"),
    )

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def validate_alias(alias: str) -> bool:
    if not alias or not ALIAS_RE.fullmatch(alias):
        return False
    return True

def clean_text(value: str, max_len: int = MAX_NAME_LEN) -> str:
    if value is None:
        return ""
    return value.strip()[:max_len]

def get_display_name(obj):
    return obj.name_en if session.get("lang", "en") == "en" else obj.name_es

def flash_errors(errors):
    for error in errors:
        flash(error, "danger")

@app.route("/", methods=["GET", "POST"])
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        alias = clean_text(request.form.get("alias", ""), max_len=32)
        if not validate_alias(alias):
            flash(t_key("invalid_alias"), "danger")
            return redirect(url_for("index"))

        user = User.query.filter_by(alias=alias).first()
        if not user:
            user = User(alias=alias, is_admin=(alias == ADMIN_ALIAS))
            db.session.add(user)
            db.session.commit()
        elif alias == ADMIN_ALIAS and not user.is_admin:
            user.is_admin = True
            db.session.commit()

        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template("index.html")

@app.route("/guest", methods=["POST"])
def guest():
    guest_alias = f"Guest_{token_urlsafe(6)}"
    user = User(alias=guest_alias, is_guest=True)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect(url_for("dashboard"))

@app.route("/lang/<lang>")
def set_lang(lang):
    if lang in ["en", "es"]:
        session["lang"] = lang
    return redirect(request.referrer or url_for("index"))

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        if "create_trip" in request.form:
            name = clean_text(request.form.get("trip_name", ""))
            selected_cat_ids = request.form.getlist("categories")
            visible_categories = Category.query.filter(
                Category.id.in_(selected_cat_ids),
                ((Category.user_id.is_(None)) & (Category.is_deleted == False)) | (Category.user_id == current_user.id),
            ).all()

            if not name:
                flash(t_key("invalid_trip_name"), "danger")
            elif not visible_categories:
                flash(t_key("invalid_selection"), "danger")
            else:
                new_trip = Trip(user_id=current_user.id, name=name)
                db.session.add(new_trip)
                db.session.flush()

                category_ids = [c.id for c in visible_categories]
                items = Item.query.filter(
                    Item.category_id.in_(category_ids),
                    (Item.user_id.is_(None)) | (Item.user_id == current_user.id),
                ).all()

                for item in items:
                    db.session.add(TripItem(trip_id=new_trip.id, item_id=item.id))

                db.session.commit()
                flash(t_key("saved"), "success")
                return redirect(url_for("trip", trip_id=new_trip.id))

        elif "add_category" in request.form:
            name = clean_text(request.form.get("cat_name", ""))
            if not name:
                flash(t_key("invalid_category_name"), "danger")
            else:
                db.session.add(Category(name_en=name, name_es=name, user_id=current_user.id))
                db.session.commit()
                flash(t_key("saved"), "success")

        elif "add_item" in request.form:
            cat_id = request.form.get("category_id")
            name = clean_text(request.form.get("item_name", ""))
            category = None
            if cat_id and cat_id.isdigit():
                category = Category.query.filter(
                    Category.id == int(cat_id),
                    (Category.user_id.is_(None)) | (Category.user_id == current_user.id),
                ).first()

            if not category:
                flash(t_key("invalid_selection"), "danger")
            elif not name:
                flash(t_key("invalid_item_name"), "danger")
            else:
                db.session.add(Item(category_id=category.id, name_en=name, name_es=name, user_id=current_user.id))
                db.session.commit()
                flash(t_key("saved"), "success")

    trips = Trip.query.filter_by(user_id=current_user.id).order_by(Trip.created_at.desc()).all()
    categories = Category.query.filter(((Category.user_id.is_(None)) & (Category.is_deleted == False)) | (Category.user_id == current_user.id)).order_by(Category.name_en.asc()).all()
    user_categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name_en.asc()).all()
    user_items = Item.query.filter_by(user_id=current_user.id).order_by(Item.name_en.asc()).all()

    return render_template(
        "dashboard.html",
        trips=trips,
        categories=categories,
        user_categories=user_categories,
        user_items=user_items,
        get_name=get_display_name,
    )

@app.route("/trip/<int:trip_id>")
@login_required
def trip(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=current_user.id).first_or_404()
    trip_items = TripItem.query.filter_by(trip_id=trip.id).all()

    status_order = {'unchecked': 0, 'standby': 1, 'packed': 2, 'na': 3}

    trip_items.sort(key=lambda ti: status_order.get(ti.status, 999))

    grouped = {}
    seen_names = set()

    for ti in trip_items:
        name_key = (ti.item.name_en.strip().lower(), ti.item.name_es.strip().lower())
        if name_key in seen_names:
            continue
        seen_names.add(name_key)

        cat = ti.item.category
        grouped.setdefault(cat, []).append(ti)

    categories = Category.query.filter(
        ((Category.user_id.is_(None)) & (Category.is_deleted == False)) | (Category.user_id == current_user.id)
    ).order_by(Category.name_en.asc()).all()

    return render_template("trip.html", trip=trip, grouped=grouped, categories=categories, get_name=get_display_name)

@app.route("/trip/<int:trip_id>/delete", methods=["POST"])
@login_required
def delete_trip(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=current_user.id).first_or_404()
    db.session.delete(trip)
    db.session.commit()
    flash(t_key("trip_deleted"), "success")
    return redirect(url_for("dashboard"))

@app.route("/api/update_item/<int:ti_id>", methods=["POST"])
@login_required
def update_item(ti_id):
    ti = db.session.get(TripItem, ti_id)
    if not ti or ti.trip.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(silent=True) or {}
    updates = {}

    if "status" in data:
        status = str(data.get("status", "")).strip()
        if status not in VALID_STATUSES:
            return jsonify({"error": "Invalid status"}), 400
        updates["status"] = status

    if "notes" in data:
        notes = clean_text(str(data.get("notes", "")), max_len=MAX_NOTES_LEN)
        updates["notes"] = notes

    if not updates:
        return jsonify({"error": "No valid fields supplied"}), 400

    for key, value in updates.items():
        setattr(ti, key, value)

    db.session.commit()
    return jsonify({"success": True})

@app.route("/api/add_trip_item", methods=["POST"])
@login_required
def add_trip_item():
    data = request.get_json()
    trip_id = data.get('trip_id')
    category_id = data.get('category_id')
    item_name = data.get('item_name')
    
    if not all([trip_id, category_id, item_name]):
        return jsonify({'success': False, 'error': 'Missing data'}), 400
    
    # Verificar que el trip pertenece al usuario
    trip = Trip.query.filter_by(id=trip_id, user_id=current_user.id).first()
    if not trip:
        return jsonify({'success': False, 'error': 'Trip not found'}), 404
    
    # Verificar que la categoría existe
    category = Category.query.filter_by(id=category_id).first()
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404
    
    # Crear el item personalizado
    new_item = Item(
        user_id=current_user.id,
        category_id=category_id,
        name_es=item_name,
        name_en=item_name
    )
    db.session.add(new_item)
    db.session.flush()  # Obtener el ID
    
    # Crear el TripItem asociado
    new_trip_item = TripItem(
        trip_id=trip_id,
        item_id=new_item.id,
        status='unchecked',
        notes=''
    )
    db.session.add(new_trip_item)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'item': {
            'id': new_item.id,
            'name_es': item_name,
            'name_en': item_name,
            'trip_item_id': new_trip_item.id,
            'status': 'unchecked'
        }
    })


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if not current_user.is_admin:
        flash(t_key("security_error"), "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        if "add_category" in request.form:
            name_en = clean_text(request.form.get("name_en", ""))
            name_es = clean_text(request.form.get("name_es", ""))
            if not name_en or not name_es:
                flash(t_key("invalid_category_name"), "danger")
            else:
                db.session.add(Category(name_en=name_en, name_es=name_es))
                db.session.commit()
                flash(t_key("saved"), "success")
                
        elif "add_item" in request.form:
            cat_id = request.form.get("category_id")
            name_en = clean_text(request.form.get("name_en", ""))
            name_es = clean_text(request.form.get("name_es", ""))
            category = None
            if cat_id and cat_id.isdigit():
                category = Category.query.filter_by(id=int(cat_id), user_id=None, is_deleted=False).first()

            if not category:
                flash(t_key("invalid_selection"), "danger")
            elif not name_en or not name_es:
                flash(t_key("invalid_item_name"), "danger")
            else:
                db.session.add(Item(category_id=category.id, name_en=name_en, name_es=name_es))
                db.session.commit()
                flash(t_key("saved"), "success")


        elif "delete_category" in request.form:
            cat_id = request.form.get("category_id")
            if cat_id and cat_id.isdigit():
                cat = Category.query.filter_by(id=int(cat_id), user_id=None).first()
                if cat:
                    cat.is_deleted = True
                    Item.query.filter_by(category_id=cat.id, user_id=None).update({"is_deleted": True})
                    db.session.commit()
                    flash(t_key("saved"), "success")

        elif "delete_item" in request.form:
            item_id = request.form.get("item_id")
            if item_id and item_id.isdigit():
                item = Item.query.filter_by(id=int(item_id), user_id=None).first()
                if item:
                    item.is_deleted = True
                    db.session.commit()
                    flash(t_key("saved"), "success")

    categories = Category.query.filter_by(user_id=None, is_deleted=False).order_by(Category.name_en.asc()).all()
    items = Item.query.filter_by(user_id=None, is_deleted=False).order_by(Item.name_en.asc()).all()
    return render_template("admin.html", categories=categories, items=items)

def clean_old_guests():
    yesterday = datetime.utcnow() - timedelta(days=1)
    old_guests = User.query.filter(
        User.is_guest.is_(True), User.created_at < yesterday
    ).all()
    for guest in old_guests:
        Trip.query.filter_by(user_id=guest.id).delete(synchronize_session="fetch")
        Item.query.filter_by(user_id=guest.id).delete(synchronize_session="fetch")
        Category.query.filter_by(user_id=guest.id).delete(synchronize_session="fetch")
        db.session.delete(guest)
    db.session.commit()

def seed_db():
    admin = User.query.filter_by(alias=ADMIN_ALIAS).first()
    if not admin:
        db.session.add(User(alias=ADMIN_ALIAS, is_admin=True))
        db.session.commit()


@app.route("/api/category/<int:cat_id>/preview")
@login_required
def category_preview(cat_id):
    category = Category.query.filter(
        Category.id == cat_id,
        (Category.user_id.is_(None)) | (Category.user_id == current_user.id),
    ).first()

    if not category:
        return jsonify({"error": "Category not found"}), 404

    items = Item.query.filter(
        Item.category_id == category.id,
        (Item.user_id.is_(None)) | (Item.user_id == current_user.id),
    ).order_by(Item.name_en.asc()).all()

    item_names = [get_display_name(item) for item in items]

    return jsonify({
        "category_name": get_display_name(category),
        "items": item_names,
        "total": len(item_names),
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_db()
        clean_old_guests()
    app.run(debug=True)
