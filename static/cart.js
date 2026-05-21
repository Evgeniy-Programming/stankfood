async function fetchCartItems(userId) {
    try {
        const response = await fetch(`/cart/${userId}`);
        if (!response.ok) {
            throw new Error('Ошибка при получении данных о товарах в корзине');
        }
        const cartItems = await response.json();
        displayCartItems(cartItems);
    } catch (error) {
        console.error(error);
    }
}
function displayCartItems(cartItems) {
    const cartContainer = document.getElementById('cart-container');
    cartContainer.innerHTML = ''; // Очистить контейнер перед добавлением новых элементов
    if (cartItems.length === 0) {
        // Если корзина пуста, отображаем соответствующее сообщение
        cartContainer.innerHTML = '<div class="empty-cart">Корзина пуста</div>';
        const cartTotal = document.getElementById('cart-total');
        cartTotal.innerHTML = ''; // Очистить предыдущую сумму
        return; // Выходим из функции
    }
    // Создаем массив для хранения HTML-кода элементов корзины
    const itemsHtml = cartItems.map(item => `
        <div class="cart-item">
            <img src="/static/images/${item.image_url}" alt="${item.name}">
            <div class="cart-item-name">${item.name}</div>
            <div class="cart-item-price">${item.price} ₽</div>
            <div class="cart-item-quantity">Количество: ${item.quantity}</div>
        </div>
    `).join(''); // Объединяем массив в одну строку
    cartContainer.innerHTML = itemsHtml; // Добавляем все элементы сразу
    const cartTotal = document.getElementById('cart-total');
    cartTotal.innerHTML = ''; // Очистить предыдущую сумму
    let sumPrice = 0;
    // Считаем общую стоимость
    cartItems.forEach(item => {
        sumPrice += item.price * item.quantity;
    });
    const totalHtml = `Итого: ${sumPrice} ₽`;
    cartTotal.innerHTML = totalHtml; // Добавляем итоговую сумму
}
fetchCartItems(userId);