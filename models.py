from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "user_data"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    avatar = db.Column(db.String(200), nullable=False, default="profimg.png")
    role = db.Column(db.String(20), nullable=False, default="customer")
    favorite_category = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    cart_items = db.relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders = db.relationship("Order", back_populates="user", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    favorites = db.relationship("FavoriteDish", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_staff(self) -> bool:
        return self.role in {"staff", "admin"}


class Restaurant(db.Model):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    dishes = db.relationship("Dish", back_populates="restaurant", cascade="all, delete-orphan")
    pickup_slots = db.relationship("PickupSlot", back_populates="restaurant", cascade="all, delete-orphan")
    orders = db.relationship("Order", back_populates="restaurant")


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)


class Dish(db.Model):
    __tablename__ = "dishes"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    weight_grams = db.Column(db.Integer, nullable=False, default=250)
    description = db.Column(db.String(255), nullable=False)
    ingredients = db.Column(db.String(255), nullable=False, default="")
    image_url = db.Column(db.String(255), nullable=False, default="maintenance.png")
    is_published = db.Column(db.Boolean, nullable=False, default=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)

    restaurant = db.relationship("Restaurant", back_populates="dishes")
    cart_items = db.relationship("CartItem", back_populates="dish", cascade="all, delete-orphan")
    order_items = db.relationship("OrderItem", back_populates="dish")
    favorites = db.relationship("FavoriteDish", back_populates="dish", cascade="all, delete-orphan")


class CartItem(db.Model):
    __tablename__ = "cart"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user_data.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("dishes.id"), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    user = db.relationship("User", back_populates="cart_items")
    dish = db.relationship("Dish", back_populates="cart_items")
    restaurant = db.relationship("Restaurant")


class PickupSlot(db.Model):
    __tablename__ = "pickup_slots"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    label = db.Column(db.String(50), nullable=False)
    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=15)

    restaurant = db.relationship("Restaurant", back_populates="pickup_slots")
    orders = db.relationship("Order", back_populates="pickup_slot")

    @property
    def available_capacity(self) -> int:
        approved_orders = sum(1 for order in self.orders if order.status != "cancelled")
        return max(self.capacity - approved_orders, 0)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(36), nullable=False, unique=True)
    qr_payload = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="accepted")
    total_amount = db.Column(db.Integer, nullable=False, default=0)
    payment_status = db.Column(db.String(30), nullable=False, default="paid")
    payment_provider = db.Column(db.String(50), nullable=False, default="demo-gateway")
    pickup_slot_id = db.Column(db.Integer, db.ForeignKey("pickup_slots.id"), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user_data.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="orders")
    restaurant = db.relationship("Restaurant", back_populates="orders")
    pickup_slot = db.relationship("PickupSlot", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = db.relationship("PaymentTransaction", back_populates="order", cascade="all, delete-orphan")


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey("dishes.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    dish_name = db.Column(db.String(100), nullable=False)
    dish_price = db.Column(db.Integer, nullable=False)
    weight_grams = db.Column(db.Integer, nullable=False, default=250)

    order = db.relationship("Order", back_populates="items")
    dish = db.relationship("Dish", back_populates="order_items")


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user_data.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    channel = db.Column(db.String(20), nullable=False, default="site")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="notifications")


class FavoriteDish(db.Model):
    __tablename__ = "favorite_dishes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user_data.id"), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey("dishes.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="favorites")
    dish = db.relationship("Dish", back_populates="favorites")


class PaymentTransaction(db.Model):
    __tablename__ = "payment_transactions"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    provider = db.Column(db.String(50), nullable=False, default="demo-gateway")
    status = db.Column(db.String(30), nullable=False, default="paid")
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    order = db.relationship("Order", back_populates="payments")
