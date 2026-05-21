from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user_data'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=False, nullable=True)
    password = db.Column(db.String(120), nullable=False) # Храните пароли в хэшированном виде
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone_number = db.Column(db.String(15), nullable=True, unique=True)
    avatar = db.Column(db.String(200), nullable=True)

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_data.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('dishes.restaurant_id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

class Dish(db.Model):
    __tablename__ = 'dishes'  
    id = db.Column(db.Integer, primary_key=True)  
    category = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False) 
    price = db.Column(db.Integer, nullable = False) 
    description = db.Column(db.String(255), nullable=False) 
    image_url = db.Column(db.String(255), nullable=False)  
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)  
    
class Restaurant(db.Model):
    __tablename__ = 'restaurants'  
    id = db.Column(db.Integer, primary_key=True)  
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)  

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)  
    name = db.Column(db.String(100), nullable=False)