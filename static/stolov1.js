// Функция для открытия модального окна редактирования
function openEditModal(dishName, dishPrice) {
    document.getElementById("dish-name").value = dishName;
    document.getElementById("dish-price").value = dishPrice;
    document.getElementById("edit-modal").style.display = "block";
}
document.getElementById("close-modal").onclick = function() {
    document.getElementById("edit-modal").style.display = "none";
}
window.onclick = function(event) {
    if (event.target == document.getElementById("edit-modal")) {
        document.getElementById("edit-modal").style.display = "none";
    }
}
document.getElementById("save-button").onclick = function() {
    alert("Изменения сохранены!");
    document.getElementById("edit-modal").style.display = "none";
}
// JavaScript для автоматической прокрутки изображений в ленте
let currentIndex = 0;
const images = document.querySelectorAll('.image-slider img');
const totalImages = images.length;
function showNextImage() {
    images[currentIndex].style.display = 'none';
    currentIndex = (currentIndex + 1) % totalImages;
    images[currentIndex].style.display = 'block';
}
setInterval(showNextImage, 3000); // смена изображения каждые 3 секунды
// Функция для переключения иконки сердечка
function toggleHeart(event, element) {
    event.stopPropagation(); // Остановить всплытие события
    const firsheart = `<svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12.01 6.001C6.5 1 1 8 5.782 13.001L12.011 20l6.23-7C23 8 17.5 1 12.01 6.002Z"/>
</svg>`;
    const nextheart = `<svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
<path d="m12.75 20.66 6.184-7.098c2.677-2.884 2.559-6.506.754-8.705-.898-1.095-2.206-1.816-3.72-1.855-1.293-.034-2.652.43-3.963 1.442-1.315-1.012-2.678-1.476-3.973-1.442-1.515.04-2.825.76-3.724 1.855-1.806 2.201-1.915 5.823.772 8.706l6.183 7.097c.19.216.46.34.743.34a.985.985 0 0 0 .743-.34Z"/>
</svg>`;
    if (element.innerHTML === firsheart) {
        element.innerHTML = nextheart; // красное сердце
    } else {
        element.innerHTML = firsheart; // тусклое сердце
        element.style.color = "black";
    }
}
function showLoginModal() {
    const modal = document.getElementById("loginModal");
    modal.style.display = "block"; // Показываем модальное окно
    // Закрытие модального окна при нажатии на "x"
    const closeButton = modal.querySelector(".close");
    closeButton.onclick = function() {
        modal.style.display = "none"; // Скрываем модальное окно
    }
    // Закрытие модального окна при нажатии вне его
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none"; // Скрываем модальное окно
        }
    }
    // Обработка отправки формы
    const loginForm = document.getElementById("loginForm");
    loginForm.onsubmit = function(event) {
        event.preventDefault(); // Предотвращаем отправку формы по умолчанию
        const phone= document.getElementById("phone").value;
        const password = document.getElementById("password").value;
        // Отправка данных на сервер
        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                phone: phone,
                password: password
            })
        })
        .then(response => {
            if (response.ok) {
                modal.style.display = "none"; // Закрываем модальное окно
                // Дополнительная логика после успешной авторизации
                location.reload(); // Перезагрузить страницу или выполнить другие действия
            } else {
                alert("Ошибка авторизации. Проверьте логин и пароль.");
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
        });
    }
}
// Функция для переключения иконки плюсика на новую иконку
function togglePlus(event, element) {
    event.stopPropagation(); // Предотвращаем всплытие события
    const menuItem = element.closest('.menu-item');
    const quantityElement = menuItem.querySelector('.quantity');
    const dishId = menuItem.getAttribute('data-id'); // Получаем ID блюда
    let quantity = parseInt(quantityElement.textContent) || 0; // Получаем текущее количество
    quantity += 1; // Увеличиваем количество
    quantityElement.textContent = quantity; // Обновляем отображаемое количество
    // Отображаем элемент количества, если он еще не виден
    quantityElement.style.display = 'inline'; // Показываем количество
    const minusButton = menuItem.querySelector('.minus-icon');
    minusButton.style.display = 'inline'; // Отображаем кнопку "-"
    // Отправляем данные на сервер
    const totalPrice = parseFloat(menuItem.querySelector('.price').textContent.replace('Цена: ', '').replace(' ₽', ''));
    fetch('/update_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            dish_id: dishId,
            quantity: quantity,
            restaurant_id: restaurantId,
            total_price: totalPrice * quantity
        })
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else if (response.status === 401) {
            // Если пользователь не авторизован, показываем модальное окно
            showLoginModal();
            throw new Error('Пользователь не авторизован');
        } else {
            throw new Error('Ошибка при добавлении товара в корзину');
        }
    })
    .then(data => {
        console.log(data.message); // Выводим сообщение о результате
    })
    .catch(error => {
        console.error('Ошибка при добавлении товара в корзину:', error);
    });
}
// Функция для уменьшения количества
function decreaseQuantity(event, element) {
    event.stopPropagation(); // Предотвращаем всплытие события
    const menuItem = element.closest('.menu-item');
    const quantityElement = menuItem.querySelector('.quantity');
    let quantity = parseInt(quantityElement.textContent) || 0; // Получаем текущее количество
    if (quantity > 0) {
        quantity -= 1; // Уменьшаем количество
        quantityElement.textContent = quantity; // Обновляем отображаемое количество
        // Скрываем элемент количества и кнопку "-" если количество стало 0
        if (quantity === 0) {
            quantityElement.style.display = 'none'; // Скрываем количество
            const minusButton = menuItem.querySelector('.minus-icon');
            minusButton.style.display = 'none'; // Скрываем кнопку "-"
        }
        // Отправляем данные на сервер
        const dishId = menuItem.getAttribute('data-id'); // Получаем ID блюда
        const totalPrice = parseFloat(menuItem.querySelector('.price').textContent.replace('Цена: ', '').replace(' ₽', ''));
        fetch('/update_cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dish_id: dishId,
                quantity: quantity,
                restaurant_id: restaurantId,
                total_price: totalPrice * quantity // Учитываем новое количество
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message); // Выводим сообщение о результате
        })
        .catch(error => {
            console.error('Ошибка при обновлении товара в корзине:', error);
        });
    }
}
// Функция для загрузки количеств из базы данных
function loadQuantities() {
    fetch('/get_cart_quantities')
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка при загрузке количеств');
            }
            return response.json();
        })
        .then(quantities => {
            const menuItemsDiv = document.getElementById('menu-list');
            const menuItems = menuItemsDiv.getElementsByClassName('menu-item');
            for (const menuItem of menuItems) {
                const dishId = menuItem.getAttribute('data-id');
                const savedQuantity = quantities[dishId] || 0; // Получаем количество из базы данных или 0
                const quantityElement = menuItem.querySelector('.quantity');
                quantityElement.textContent = savedQuantity;
                quantityElement.style.display = savedQuantity > 0 ? 'inline' : 'none';
                const minusButton = menuItem.querySelector('.minus-icon');
                minusButton.style.display = savedQuantity > 0 ? 'inline' : 'none';
            }
        })
        .catch(error => {
            console.error('Ошибка при загрузке количеств:', error);
        });
}
// Получаем ID ресторана из переменной, переданной из Flask
let dishes = []; // Переменная для хранения всех блюд
// Вызов функции showMenu с ID ресторана
document.addEventListener('DOMContentLoaded', () => {
    showMenu(restaurantId);
    loadQuantities();
});
function showMenu(restaurantId) {
    const menuItemsDiv = document.getElementById('menu-list');
    menuItemsDiv.innerHTML = ''; // Очищаем предыдущие элементы меню
    if (!restaurantId) {
        return; // Если ресторан не выбран, ничего не делать
    }
    fetch(`/api/dishes/${restaurantId}`) // Используем ID ресторана в запросе
        .then(response => {
            if (!response.ok) {
                throw new Error('Сеть не отвечает');
            }
            return response.json();
        })
        .then(data => {
            dishes = data; // Сохраняем все блюда в переменной
            displayAllDishes(dishes); // Отображаем все блюда
        })
        .catch(error => {
            console.error('Ошибка при получении блюд:', error);
            menuItemsDiv.innerHTML = '<p>Не удалось загрузить блюда. Попробуйте позже.</p>';
        });
}
// Функция для отображения всех блюд
function displayAllDishes(dishes) {
    const menuItemsDiv = document.getElementById('menu-list');
    menuItemsDiv.innerHTML = ''; // Очищаем предыдущие элементы меню
    dishes.forEach(dish => {
        createDishCard(dish);
    });
}
// Функция для создания карточки блюда
function createDishCard(dish) {
    const menuList = document.getElementById('menu-list');
    const menuItem = document.createElement('div');
    menuItem.className = 'menu-item';
    menuItem.setAttribute('data-id', dish.id);
    menuItem.setAttribute('data-name', dish.name);
    menuItem.setAttribute('onclick', `openEditModal('${dish.name}', ${dish.price}, ${dish.id})`);
    menuItem.innerHTML = `
        <div class="menu-header">
            <span class="heart-icon" onclick="toggleHeart(event, this)">❤️</span>
            <img src="/static/images/${dish.image_url}" style="width: 160px; height:120px; margin: 10px 0;" alt="${dish.name}">
        </div>
        <h3 class="menu-item-name">${dish.name}</h3>
        <div class="menu-footer">
            <span class="price">Цена: ${dish.price} ₽</span>
            <span class="minus-icon" onclick="decreaseQuantity(event, this)" style="display: none;">
                <svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <circle xmlns="http://www.w3.org/2000/svg" cx="12" cy="12" r="10" stroke="#1C274C" stroke-width="1.5"/>
                    <path xmlns="http://www.w3.org/2000/svg" d="M15 12H9" stroke="#1C274C" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
            </span>
            <span class="quantity" style="display: none;">0</span> <!-- Начальное количество -->
            <span class="plus-icon" onclick="togglePlus(event, this)">
                <svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="24" height="24" viewBox="0 0 48 48">
                    <path d="M 24 4 C 12.972066 4 4 12.972074 4 24 C 4 35.027926 12.972066 44 24 44 C 35.027934 44 44 35.027926 44 24 C 44 12.972074 35.027934 4 24 4 z M 24 7 C 33.406615 7 41 14.593391 41 24 C 41 33.406609 33.406615 41 24 41 C 14.593385 41 7 33.406609 7 24 C 7 14.593391 14.593385 7 24 7 z M 23.976562 13.978516 A 1.50015 1.50015 0 0 0 22.5 15.5 L 22.5 22.5 L 15.5 22.5 A 1.50015 1.50015 0 1 0 15.5 25.5 L 22.5 25.5 L 22.5 32.5 A 1.50015 1.50015 0 1 0 25.5 32.5 L 25.5 25.5 L 32.5 25.5 A 1.50015 1.50015 0 1 0 32.5 22.5 L 25.5 22.5 L 25.5 15.5 A 1.50015 1.50015 0 0 0 23.976562 13.978516 z"></path>
                </svg>
            </span>
        </div>
    `;
    menuList.appendChild(menuItem);
}
// Функция для фильтрации блюд по категории
function filterDishes(category) {
    const menuItemsDiv = document.getElementById('menu-list');
    menuItemsDiv.innerHTML = ''; // Очищаем предыдущие элементы меню
    const filteredDishes = category === 'Все' ? dishes : dishes.filter(dish => dish.category === category);
    displayAllDishes(filteredDishes);
}

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-container input');
    searchInput.addEventListener('input', function() {
        const searchTerm = searchInput.value.toLowerCase();
        const menuItems = document.querySelectorAll('.menu-item');
        menuItems.forEach(item => {
            const dishName = item.getAttribute('data-name').toLowerCase();
            if (dishName.includes(searchTerm)) {
                item.style.display = ''; // Показываем элемент
            } else {
                item.style.display = 'none'; // Скрываем элемент
            }
        });
    });
});