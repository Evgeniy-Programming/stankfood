from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from models import (
    CartItem,
    Category,
    Dish,
    FavoriteDish,
    Notification,
    Order,
    OrderItem,
    PaymentTransaction,
    PickupSlot,
    Restaurant,
    User,
    db,
)

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
DB_PATH = INSTANCE_DIR / "database.db"
IMAGE_DIR = BASE_DIR / "static" / "images"

VALID_STATUSES = ["accepted", "cooking", "ready", "issued", "cancelled"]
STATUS_LABELS = {
    "accepted": "Принят",
    "cooking": "Готовится",
    "ready": "Готов к выдаче",
    "issued": "Выдан",
    "cancelled": "Отменен",
}
MEAL_CATEGORIES = ["Завтрак", "Обед", "Ужин"]


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "stankfood-dev-secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "main"
    login_manager.login_message = "Сначала войдите в аккаунт."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional[User]:
        return db.session.get(User, int(user_id))

    register_routes(app)
    return app


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="pbkdf2:sha256")


def create_notification(user_id: int, message: str, channel: str = "site") -> None:
    db.session.add(Notification(user_id=user_id, message=message, channel=channel))


def generate_slots_for_restaurant(restaurant: Restaurant) -> None:
    if restaurant.pickup_slots:
        return

    now = datetime.now().replace(second=0, microsecond=0)
    base_start = now.replace(hour=9, minute=0)
    if now.hour >= 16:
        base_start = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    elif now.hour >= 9:
        minutes_to_next = (30 - (now.minute % 30)) % 30
        candidate = now + timedelta(minutes=minutes_to_next)
        base_start = candidate if candidate.hour < 16 else (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

    slots = []
    current = base_start
    for _ in range(14):
        slot_end = current + timedelta(minutes=30)
        slots.append(
            PickupSlot(
                restaurant_id=restaurant.id,
                label=f"{current:%d.%m %H:%M}–{slot_end:%H:%M}",
                starts_at=current,
                ends_at=slot_end,
                capacity=15,
            )
        )
        current = slot_end
    db.session.add_all(slots)
    db.session.commit()


def seed_data() -> None:
    if Category.query.count() == 0:
        db.session.add_all([Category(name=name) for name in ["Завтрак", "Обед", "Ужин", "Напитки"]])
        db.session.commit()

    if Restaurant.query.count() == 0:
        restaurants = [
            Restaurant(
                name="Столовая в 1-ом корпусе",
                description="Быстрые завтраки, обеды и напитки рядом с главным входом.",
                image_url="Stol1.png",
            ),
            Restaurant(
                name="Столовая во 2-ом корпусе",
                description="Полноценные обеды и ужины с горячими блюдами и десертами.",
                image_url="Stol2.png",
            ),
        ]
        db.session.add_all(restaurants)
        db.session.commit()

    restaurant_ids = {item.name: item.id for item in Restaurant.query.order_by(Restaurant.id).all()}

    if Dish.query.count() == 0:
        dishes = [
            Dish(
                name="Омлет с сыром",
                category="Завтрак",
                description="Нежный омлет с тостами и зеленью.",
                ingredients="Яйцо, сыр, молоко, зелень, тосты",
                weight_grams=260,
                price=190,
                image_url="omelet-with-cheese.jpg",
                restaurant_id=restaurant_ids["Столовая в 1-ом корпусе"],
                is_published=True,
            ),
            Dish(
                name="Сырники",
                category="Завтрак",
                description="Сырники со сметаной и ягодным соусом.",
                ingredients="Творог, мука, яйцо, сметана, ягодный соус",
                weight_grams=220,
                price=210,
                image_url="cheesecakes.jpg",
                restaurant_id=restaurant_ids["Столовая в 1-ом корпусе"],
                is_published=True,
            ),
            Dish(
                name="Куриный бургер",
                category="Обед",
                description="Бургер с куриной котлетой и свежими овощами.",
                ingredients="Булочка, курица, салат, помидор, соус",
                weight_grams=310,
                price=280,
                image_url="chicken-burger.jpg",
                restaurant_id=restaurant_ids["Столовая в 1-ом корпусе"],
                is_published=True,
            ),
            Dish(
                name="Капучино",
                category="Напитки",
                description="Классический кофейный напиток с молочной пенкой.",
                ingredients="Кофе, молоко",
                weight_grams=300,
                price=150,
                image_url="cappuccino.jpg",
                restaurant_id=restaurant_ids["Столовая в 1-ом корпусе"],
                is_published=True,
            ),
            Dish(
                name="Борщ со сметаной",
                category="Обед",
                description="Горячий борщ с чесночной булочкой.",
                ingredients="Свекла, мясо, картофель, сметана, булочка",
                weight_grams=350,
                price=210,
                image_url="borscht-with-sour.jpg",
                restaurant_id=restaurant_ids["Столовая во 2-ом корпусе"],
                is_published=True,
            ),
            Dish(
                name="Курица с рисом",
                category="Ужин",
                description="Куриное филе с рисом и овощами.",
                ingredients="Курица, рис, морковь, перец, соус",
                weight_grams=340,
                price=260,
                image_url="chicken-with-rice.jpg",
                restaurant_id=restaurant_ids["Столовая во 2-ом корпусе"],
                is_published=True,
            ),
            Dish(
                name="Паста карбонара",
                category="Ужин",
                description="Паста в сливочном соусе с беконом и пармезаном.",
                ingredients="Паста, сливки, бекон, пармезан",
                weight_grams=320,
                price=320,
                image_url="pasta-carbonara.jpg",
                restaurant_id=restaurant_ids["Столовая во 2-ом корпусе"],
                is_published=True,
            ),
            Dish(
                name="Компот",
                category="Напитки",
                description="Домашний ягодный компот.",
                ingredients="Ягоды, вода, сахар",
                weight_grams=250,
                price=80,
                image_url="compot.jpg",
                restaurant_id=restaurant_ids["Столовая во 2-ом корпусе"],
                is_published=True,
            ),
        ]
        db.session.add_all(dishes)
        db.session.commit()

    if User.query.filter_by(phone_number="+70000000001").first() is None:
        db.session.add(
            User(
                username="Администратор",
                phone_number="+70000000001",
                email="admin@stankfood.local",
                password=hash_password("admin123"),
                role="admin",
            )
        )
    if User.query.filter_by(phone_number="+70000000002").first() is None:
        db.session.add(
            User(
                username="Сотрудник",
                phone_number="+70000000002",
                email="staff@stankfood.local",
                password=hash_password("staff123"),
                role="staff",
            )
        )
    if User.query.filter_by(phone_number="+70000000003").first() is None:
        db.session.add(
            User(
                username="Студент",
                phone_number="+70000000003",
                email="student@stankfood.local",
                password=hash_password("student123"),
                role="customer",
                favorite_category="Обед",
            )
        )
    db.session.commit()

    for restaurant in Restaurant.query.order_by(Restaurant.id).all():
        generate_slots_for_restaurant(restaurant)


def get_visible_restaurants():
    return Restaurant.query.filter_by(is_active=True).order_by(Restaurant.id).limit(2).all()


def get_available_slots(restaurant_id: int):
    cutoff = datetime.now() + timedelta(minutes=30)
    slots = (
        PickupSlot.query.filter_by(restaurant_id=restaurant_id)
        .filter(PickupSlot.starts_at >= cutoff)
        .order_by(PickupSlot.starts_at.asc())
        .all()
    )
    return [slot for slot in slots if slot.available_capacity > 0]


def get_cart_summary(user_id: int):
    items = (
        CartItem.query.filter_by(user_id=user_id)
        .join(Dish, CartItem.product_id == Dish.id)
        .order_by(CartItem.id.desc())
        .all()
    )
    total = sum(item.quantity * item.dish.price for item in items)
    restaurants = sorted({item.restaurant_id for item in items})
    return items, total, restaurants


def build_analytics():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    revenue = sum(order.total_amount for order in orders if order.payment_status == "paid")
    status_counts = Counter(order.status for order in orders)
    dish_counter = Counter()
    weekday_counter = Counter()
    meal_counter = Counter()

    for order in orders:
        weekday_counter[order.created_at.strftime("%A")] += order.total_amount
        hour = order.pickup_slot.starts_at.hour
        if hour < 11:
            meal_counter["Завтрак"] += order.total_amount
        elif hour < 16:
            meal_counter["Обед"] += order.total_amount
        else:
            meal_counter["Ужин"] += order.total_amount
        for item in order.items:
            dish_counter[item.dish_name] += item.quantity

    return {
        "revenue": revenue,
        "orders_total": len(orders),
        "status_counts": status_counts,
        "top_dishes": dish_counter.most_common(5),
        "weekday_sales": weekday_counter,
        "meal_sales": meal_counter,
    }


def register_routes(app: Flask) -> None:
    @app.context_processor
    def inject_layout_data():
        cart_count = 0
        unread_notifications = []
        if current_user.is_authenticated:
            cart_count = sum(item.quantity for item in current_user.cart_items)
            unread_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
        return {
            "nav_restaurants": get_visible_restaurants(),
            "cart_count": cart_count,
            "status_labels": STATUS_LABELS,
            "unread_notifications": unread_notifications,
        }

    @app.route("/")
    @app.route("/main", methods=["GET", "POST"])
    def main():
        if request.method == "POST":
            payload = request.get_json(silent=True) or request.form
            action = (payload.get("action") or "").strip().lower()
            if action == "register":
                return handle_register(payload)
            if action == "login":
                return handle_login(payload)
            return jsonify({"message": "Неизвестное действие."}), 400

        restaurants = get_visible_restaurants()
        popular_dishes = Dish.query.filter_by(is_published=True).order_by(Dish.id.desc()).limit(6).all()
        analytics = build_analytics()
        return render_template("mainsheet.html", restaurants=restaurants, popular_dishes=popular_dishes, analytics=analytics)

    def handle_register(payload):
        username = (payload.get("name") or "").strip()
        phone = (payload.get("phone") or "").strip()
        password = (payload.get("password") or "").strip()
        email = (payload.get("email") or "").strip() or None

        if not username or not phone or not password:
            return jsonify({"message": "Заполните имя, телефон и пароль."}), 400
        if len(password) < 6:
            return jsonify({"message": "Пароль должен быть не короче 6 символов."}), 400
        if User.query.filter_by(phone_number=phone).first():
            return jsonify({"message": "Пользователь с таким телефоном уже существует."}), 409
        if email and User.query.filter_by(email=email).first():
            return jsonify({"message": "Пользователь с таким email уже существует."}), 409

        user = User(
            username=username,
            phone_number=phone,
            email=email,
            password=hash_password(password),
            role="customer",
        )
        db.session.add(user)
        db.session.commit()
        create_notification(user.id, "Аккаунт создан. Добро пожаловать в Stank FOOD.")
        db.session.commit()
        login_user(user)
        return jsonify({"redirect": url_for("main"), "message": "Регистрация прошла успешно."})

    def handle_login(payload):
        phone = (payload.get("phone") or "").strip()
        password = (payload.get("password") or "").strip()
        if not phone or not password:
            return jsonify({"message": "Введите телефон и пароль."}), 400

        user = User.query.filter_by(phone_number=phone).first()
        if user is None or not check_password_hash(user.password, password):
            return jsonify({"message": "Неверный телефон или пароль."}), 401

        login_user(user)
        return jsonify({"redirect": url_for("main"), "message": "Успешный вход."})

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Вы вышли из аккаунта.", "success")
        return redirect(url_for("main"))

    @app.route("/menu/<int:restaurant_id>")
    def menu(restaurant_id: int):
        restaurant = db.session.get(Restaurant, restaurant_id)
        if restaurant is None or not restaurant.is_active:
            return redirect(url_for("main"))

        selected_category = (request.args.get("category") or "").strip()
        query = Dish.query.filter_by(restaurant_id=restaurant.id, is_published=True)
        if selected_category:
            query = query.filter_by(category=selected_category)

        dishes = query.order_by(Dish.category.asc(), Dish.name.asc()).all()
        categories = Category.query.order_by(Category.id.asc()).all()
        favorite_ids = set()
        if current_user.is_authenticated:
            favorite_ids = {fav.dish_id for fav in FavoriteDish.query.filter_by(user_id=current_user.id).all()}
        return render_template(
            "menu.html",
            restaurant=restaurant,
            dishes=dishes,
            categories=categories,
            selected_category=selected_category,
            favorite_ids=favorite_ids,
        )

    @app.route("/cart")
    @login_required
    def cart():
        items, total, restaurants = get_cart_summary(current_user.id)
        slots = []
        warning = None
        if restaurants:
            if len(restaurants) > 1:
                warning = "Корзина должна содержать блюда только из одной столовой для оформления заказа."
            else:
                slots = get_available_slots(restaurants[0])
        return render_template("cart.html", items=items, total=total, slots=slots, mixed_restaurants=warning)

    @app.route("/update_cart", methods=["POST"])
    @login_required
    def update_cart():
        data = request.get_json(silent=True) or request.form
        try:
            dish_id = int(data.get("dish_id", 0))
            quantity = int(data.get("quantity", 0))
        except (TypeError, ValueError):
            return jsonify({"message": "Некорректные данные корзины."}), 400

        dish = db.session.get(Dish, dish_id)
        if dish is None or not dish.is_published:
            return jsonify({"message": "Блюдо не найдено."}), 404

        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=dish_id).first()
        existing_restaurant_ids = {item.restaurant_id for item in current_user.cart_items if item.product_id != dish_id}
        if quantity > 0 and existing_restaurant_ids and dish.restaurant_id not in existing_restaurant_ids:
            return jsonify({"message": "Оформление возможно только для одной столовой за раз."}), 409

        if quantity <= 0:
            if cart_item:
                db.session.delete(cart_item)
                db.session.commit()
            return jsonify({"message": "Товар удален из корзины."})

        if cart_item is None:
            cart_item = CartItem(
                user_id=current_user.id,
                product_id=dish_id,
                restaurant_id=dish.restaurant_id,
                quantity=quantity,
            )
            db.session.add(cart_item)
        else:
            cart_item.quantity = quantity
        db.session.commit()
        return jsonify({"message": "Корзина обновлена.", "cart_count": sum(item.quantity for item in current_user.cart_items)})

    @app.route("/checkout", methods=["POST"])
    @login_required
    def checkout():
        slot_id = request.form.get("pickup_slot_id", type=int) or (request.get_json(silent=True) or {}).get("pickup_slot_id")
        items, total, restaurants = get_cart_summary(current_user.id)
        if not items:
            flash("Корзина уже пуста.", "warning")
            return redirect(url_for("cart"))
        if len(restaurants) != 1:
            flash("Для оформления заказа выберите блюда только из одной столовой.", "danger")
            return redirect(url_for("cart"))
        if not slot_id:
            flash("Выберите слот выдачи.", "danger")
            return redirect(url_for("cart"))

        slot = db.session.get(PickupSlot, int(slot_id))
        if slot is None or slot.restaurant_id != restaurants[0]:
            flash("Слот выдачи недоступен.", "danger")
            return redirect(url_for("cart"))
        if slot.starts_at < datetime.now() + timedelta(minutes=30):
            flash("Предзаказ возможен не позднее чем за 30 минут до выдачи.", "danger")
            return redirect(url_for("cart"))
        if slot.available_capacity <= 0:
            flash("Этот слот уже заполнен. Выберите другой.", "danger")
            return redirect(url_for("cart"))

        order = Order(
            order_number=str(uuid.uuid4())[:8].upper(),
            qr_payload=f"STANKFOOD:{uuid.uuid4()}",
            status="accepted",
            total_amount=total,
            payment_status="paid",
            pickup_slot_id=slot.id,
            restaurant_id=restaurants[0],
            user_id=current_user.id,
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    dish_id=item.dish.id,
                    quantity=item.quantity,
                    dish_name=item.dish.name,
                    dish_price=item.dish.price,
                    weight_grams=item.dish.weight_grams,
                )
            )
            db.session.delete(item)

        db.session.add(PaymentTransaction(order_id=order.id, amount=total, status="paid"))
        create_notification(current_user.id, f"Заказ {order.order_number} принят. Слот: {slot.label}.")
        db.session.commit()
        flash("Заказ оформлен и оплачен через demo-gateway.", "success")
        return redirect(url_for("profile"))

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        if request.method == "POST":
            payload = request.get_json(silent=True) or request.form
            username = (payload.get("name") or "").strip()
            phone = (payload.get("phone") or "").strip()
            email = (payload.get("email") or "").strip() or None
            password = (payload.get("password") or "").strip()
            favorite_category = (payload.get("favorite_category") or "").strip() or None

            if not username or not phone:
                return jsonify({"message": "Имя и телефон обязательны."}), 400

            if User.query.filter(User.phone_number == phone, User.id != current_user.id).first():
                return jsonify({"message": "Такой телефон уже занят."}), 409
            if email and User.query.filter(User.email == email, User.id != current_user.id).first():
                return jsonify({"message": "Такой email уже занят."}), 409

            current_user.username = username
            current_user.phone_number = phone
            current_user.email = email
            current_user.favorite_category = favorite_category
            if password:
                if len(password) < 6:
                    return jsonify({"message": "Пароль должен быть не короче 6 символов."}), 400
                current_user.password = hash_password(password)
            db.session.commit()
            return jsonify({"message": "Профиль сохранен."})

        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        favorites = FavoriteDish.query.filter_by(user_id=current_user.id).order_by(FavoriteDish.created_at.desc()).all()
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()
        return render_template("profile.html", orders=orders, favorites=favorites, notifications=notifications, categories=MEAL_CATEGORIES)

    @app.route("/favorite/<int:dish_id>", methods=["POST"])
    @login_required
    def toggle_favorite(dish_id: int):
        dish = db.session.get(Dish, dish_id)
        if dish is None:
            return jsonify({"message": "Блюдо не найдено."}), 404
        favorite = FavoriteDish.query.filter_by(user_id=current_user.id, dish_id=dish_id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return jsonify({"message": "Удалено из любимых.", "favorite": False})
        db.session.add(FavoriteDish(user_id=current_user.id, dish_id=dish_id))
        db.session.commit()
        return jsonify({"message": "Добавлено в любимые.", "favorite": True})

    @app.route("/reorder/<int:order_id>", methods=["POST"])
    @login_required
    def reorder(order_id: int):
        order = db.session.get(Order, order_id)
        if order is None or order.user_id != current_user.id:
            abort(404)

        current_restaurants = {item.restaurant_id for item in current_user.cart_items}
        if current_restaurants and order.restaurant_id not in current_restaurants:
            return jsonify({"message": "Сначала очистите корзину другой столовой."}), 409

        for order_item in order.items:
            cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=order_item.dish_id).first()
            if cart_item:
                cart_item.quantity += order_item.quantity
            else:
                db.session.add(
                    CartItem(
                        user_id=current_user.id,
                        product_id=order_item.dish_id,
                        restaurant_id=order.restaurant_id,
                        quantity=order_item.quantity,
                    )
                )
        db.session.commit()
        return jsonify({"message": "Заказ повторно добавлен в корзину.", "redirect": url_for("cart")})

    @app.route("/staff/orders", methods=["GET", "POST"])
    @login_required
    def staff_orders():
        if not current_user.is_staff:
            flash("Доступ только для персонала столовой.", "warning")
            return redirect(url_for("main"))

        if request.method == "POST":
            order_id = request.form.get("order_id", type=int)
            status = request.form.get("status", "").strip()
            order = db.session.get(Order, order_id)
            if order is None or status not in VALID_STATUSES:
                flash("Некорректное обновление заказа.", "danger")
                return redirect(url_for("staff_orders"))
            order.status = status
            create_notification(order.user_id, f"Заказ {order.order_number}: статус «{STATUS_LABELS[status]}».")
            db.session.commit()
            flash("Статус заказа обновлен.", "success")
            return redirect(url_for("staff_orders"))

        orders = Order.query.order_by(Order.created_at.desc()).all()
        return render_template("staff_orders.html", orders=orders, valid_statuses=VALID_STATUSES)

    @app.route("/admin/analytics")
    @login_required
    def analytics():
        if not current_user.is_staff:
            flash("Доступ только для персонала столовой.", "warning")
            return redirect(url_for("main"))
        return render_template("analytics.html", analytics=build_analytics())

    @app.route("/add_dish", methods=["GET", "POST"])
    @login_required
    def add_dish():
        if not current_user.is_staff:
            flash("Раздел доступен только персоналу.", "warning")
            return redirect(url_for("main"))

        if request.method == "POST":
            dish_id = request.form.get("dish_id", type=int)
            name = request.form.get("name", "").strip()
            category = request.form.get("category", "").strip()
            description = request.form.get("description", "").strip()
            ingredients = request.form.get("ingredients", "").strip()
            restaurant_id = request.form.get("restaurant_id", type=int)
            weight_grams = request.form.get("weight_grams", type=int)
            price = request.form.get("price", type=int)
            is_published = request.form.get("is_published") == "on"

            if not all([name, category, description, ingredients, restaurant_id, weight_grams, price]):
                flash("Заполните все поля блюда.", "danger")
                return redirect(url_for("add_dish"))

            dish = db.session.get(Dish, dish_id) if dish_id else Dish(image_url="compot.png")
            if dish is None:
                flash("Блюдо не найдено.", "danger")
                return redirect(url_for("add_dish"))
            if not dish_id:
                db.session.add(dish)

            dish.name = name
            dish.category = category
            dish.description = description
            dish.ingredients = ingredients
            dish.restaurant_id = restaurant_id
            dish.weight_grams = weight_grams
            dish.price = price
            dish.is_published = is_published

            image = request.files.get("image")
            if image and image.filename:
                safe_name = Path(image.filename).name
                image.save(IMAGE_DIR / safe_name)
                dish.image_url = safe_name

            db.session.commit()
            flash("Блюдо сохранено.", "success")
            return redirect(url_for("add_dish"))

        restaurants = get_visible_restaurants()
        categories = Category.query.order_by(Category.id.asc()).all()
        dishes = Dish.query.order_by(Dish.id.desc()).all()
        return render_template("dishes.html", restaurants=restaurants, categories=categories, dishes=dishes)

    @app.route("/delete_dish/<int:dish_id>", methods=["POST"])
    @login_required
    def delete_dish(dish_id: int):
        if not current_user.is_staff:
            flash("Удаление доступно только персоналу.", "warning")
            return redirect(url_for("main"))
        dish = db.session.get(Dish, dish_id)
        if dish:
            db.session.delete(dish)
            db.session.commit()
            flash("Блюдо удалено.", "success")
        return redirect(url_for("add_dish"))

    @app.route("/mark_notifications_read", methods=["POST"])
    @login_required
    def mark_notifications_read():
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
        db.session.commit()
        return jsonify({"message": "Уведомления отмечены прочитанными."})

    @app.route("/restaurant/<int:restaurant_id>")
    def restaurant_redirect(restaurant_id: int):
        return redirect(url_for("menu", restaurant_id=restaurant_id))

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("not_found.html"), 404


app = create_app()

if __name__ == "__main__":
    INSTANCE_DIR.mkdir(exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_data()
    app.run(debug=True)
