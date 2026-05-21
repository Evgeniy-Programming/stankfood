from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, Cart, Dish, Restaurant, Category
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'bezhentsi'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main'))

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    print(data)
    phone=data.get('phone')
    password=data.get('password')
    user = User.query.filter((User.phone_number == phone)).first()
    if user and check_password_hash(user.password, password):
        login_user(user)
        return jsonify({"message": "Успешная авторизация"}), 200
    return jsonify({"message": "Неверное имя пользователя или пароль."}), 401

@app.route('/main', methods=['GET','POST'])
def main():
    if request.method == 'GET':
        restaurants = Restaurant.query.all()
        return render_template('mainsheet.html', restaurants = restaurants)
    if request.method == 'POST':
        data = request.json
        action = data.get('action')  # 'register' или 'login'
        if action == 'register':
            name = data.get('name')
            phone = data.get('phone')
            password = data.get('password')
            # Проверка на существование пользователя
            existing_user = User.query.filter((User.phone_number == phone)).first()
            if existing_user:
                return jsonify({"message": "Пользователь с таким email или телефоном уже существует."}), 403
            # Создание нового пользователя
            new_user = User(
                username=name,
                phone_number=phone,
                password=generate_password_hash(password)
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return jsonify({"redirect": url_for('main')}), 200 

        elif action == 'login':
            phone = data.get('phone')
            password = data.get('password')
            user = User.query.filter_by(phone_number=phone).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                return jsonify({"redirect": url_for('main')}), 200 
            return jsonify({"message": "Неверный телефон или пароль."}), 401
        return jsonify({"message": "Неверное действие."}), 400


@app.route('/menu/<int:restaurant_id>', methods=['GET'])
def menu(restaurant_id):
    return render_template(f'stolov{restaurant_id}.html', restaurant_id=restaurant_id)

@app.route('/api/dishes/<int:restaurant_id>', methods=['GET'])
def get_dishes(restaurant_id):
    dishes = Dish.query.filter_by(restaurant_id=restaurant_id).all()
    return jsonify([{
        'id': dish.id,
        'name': dish.name,
        'description': dish.description,
        'image_url': dish.image_url,
        'category': dish.category,
        'price': dish.price
    } for dish in dishes])

@app.route('/cart')
@login_required
def cart():
    return render_template('cart.html')

@app.route('/add_dish', methods=['GET', 'POST'])
@login_required
def add_dish():
    if request.method == 'POST':
        # Проверяем, пришел ли запрос на редактирование или добавление нового блюда
        dish_id = request.form.get('dish_id')  # Получаем ID блюда, если он есть
        name = request.form['name']
        category = request.form['category']
        description = request.form['description']
        restaurant_id = request.form['restaurant_id']
        price = request.form['price']
        # Обработка загрузки файла
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                flash('Нет выбранного файла', 'danger')
                return redirect(request.url)
            # Сохранение файла
            filename = file.filename
            file.save(os.path.join("static/images", filename))
        else:
            filename = None  # Если файл не загружен, оставляем filename равным None
        if dish_id:  # Если dish_id существует, значит редактируем блюдо
            dish = Dish.query.get(dish_id)
            if dish:
                # Обновляем существующее блюдо
                dish.name = name
                dish.category = category
                dish.description = description
                dish.price = price
                if filename:  # Если новое изображение загружено, обновляем его
                    dish.image_url = filename
                db.session.commit()
                flash('Блюдо успешно обновлено', 'success')
        else:  # Если dish_id нет, значит добавляем новое блюдо
            if filename is None:
                flash('Необходимо загрузить изображение', 'danger')
                return redirect(request.url)
            # Создание нового блюда
            new_dish = Dish(name=name, category=category, description=description, image_url=filename, restaurant_id=restaurant_id, price=price)
            db.session.add(new_dish)
            db.session.commit()
            flash('Блюдо успешно добавлено', 'success')
        return redirect(url_for('add_dish'))
    restaurants = Restaurant.query.all()  # Получаем список ресторанов для выбора
    categories = Category.query.all()
    dishes = Dish.query.all()  # Получаем все блюда для отображения
    dishes_by_restaurant = {}
    for dish in dishes:
        if dish.restaurant_id not in dishes_by_restaurant:
            dishes_by_restaurant[dish.restaurant_id] = {
                'dishes': []
            }
        dishes_by_restaurant[dish.restaurant_id]['dishes'].append(dish)
    return render_template('dishes.html', restaurants=restaurants, dishes_by_restaurant=dishes_by_restaurant, categories=categories)

@app.route('/delete_dish/<int:dish_id>', methods=['DELETE'])
def delete_dish(dish_id):
    dish = Dish.query.get(dish_id)
    if dish:
        db.session.delete(dish)
        db.session.commit()
        return '', 204  # Успешно удалено
    return '', 404  # Не найдено


@app.route('/get_cart_quantities', methods=['GET'])
def get_cart_quantities():
    if current_user.is_authenticated:
        user_id = current_user.id
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        quantities = {}
        for item in cart_items:
            quantities[item.product_id] = item.quantity
        return jsonify(quantities), 200
    else:
        return jsonify({"message":"Пользователь не авторизован"}), 401

@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart_items(user_id):
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    results = []
    for item in cart_items:
        # Получаем продукт по product_id
        product = Dish.query.filter_by(id=item.id, restaurant_id=item.restaurant_id).first()
        if product:  # Проверяем, что продукт существует
            results.append({
                'user_id': item.user_id,
                'quantity': item.quantity,
                'name': product.name,
                'price': product.price,
                'image_url': product.image_url
            })
    return jsonify(results)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    if current_user.is_authenticated:
        data = request.json
        user_id = current_user.id
        dish_id = data.get('dish_id')
        quantity = data.get('quantity')
        restaurant_id = data.get('restaurant_id')
        # Проверка на существование товара
        dish = Dish.query.get(dish_id)
        if not dish:
            return jsonify({"message": "Товар не найден"}), 404
        # Поиск элемента корзины для данного пользователя и товара
        cart_item = Cart.query.filter_by(user_id=user_id, product_id=dish_id).first()
        if cart_item:
            # Если товар уже есть в корзине, обновляем его количество
            if quantity > 0:
                cart_item.quantity = quantity
                db.session.commit()
                return jsonify({"message": "Количество товара в корзине обновлено", "cart_item": {
                    "id": cart_item.id,
                    "dish_id": cart_item.product_id,
                    "quantity": cart_item.quantity,
                    "restaurant_id": cart_item.restaurant_id,
                }}), 200
            else:
                # Если количество равно 0, удаляем товар из корзины
                db.session.delete(cart_item)
                db.session.commit()
                return jsonify({"message": "Товар удален из корзины"}), 200
        else:
            # Если товара нет в корзине, создаем новый элемент корзины
            if quantity > 0:
                new_cart_item = Cart(user_id=user_id, product_id=dish_id, quantity=quantity, restaurant_id=restaurant_id)
                db.session.add(new_cart_item)
                db.session.commit()
                return jsonify({"message": "Товар добавлен в корзину", "cart_item": {
                    "id": new_cart_item.id,
                    "dish_id": new_cart_item.product_id,
                    "quantity": new_cart_item.quantity,
                    "restaurant_id": new_cart_item.restaurant_id,
                }}), 201
            else:
                return jsonify({"message": "Количество должно быть больше 0 для добавления товара в корзину"}), 400
    else:
        return jsonify({"message": "Пользователь не авторизован"}), 401

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if current_user.is_authenticated:
        if request.method == 'GET':
            # Получаем данные текущего пользователя
            return render_template('profile.html', username=current_user.username, email=current_user.email, phone=current_user.phone_number)
        if request.method == 'POST':
            data = request.json
            print(data)
            name = data.get('name')
            phone = data.get('phone')
            password = data.get('password')
            email = data.get('email')
            # Проверка на существование пользователя с тем же номером телефона, кроме текущего
            existing_user = User.query.filter((User.phone_number == phone) & (User.id != current_user.id)).first()
            if existing_user:
                return jsonify({"message": "Пользователь с таким номером телефона уже существует."}), 403
            # Обновление данных текущего пользователя
            current_user.username = name
            current_user.phone_number = phone
            current_user.email = email
            if password:  # Обновляем пароль только если он был предоставлен
                current_user.password = generate_password_hash(password)
            db.session.commit()  # Сохраняем изменения в базе данных
            return jsonify({"message": "Данные профиля успешно обновлены."}), 200
    else:
        return jsonify({"message": "Пользователь не авторизован"}), 401

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
