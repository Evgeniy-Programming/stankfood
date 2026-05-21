function toggleLanguage() {
    const ruButton = document.querySelector('.language-button.ru');
    const enButton = document.querySelector('.language-button.en');
    const isRussian = enButton.style.transform === 'translateX(100%)';
    if (isRussian) {
        enButton.style.transform = 'translateX(0)';
        ruButton.style.transform = 'translateX(0)';
    } else {
        enButton.style.transform = 'translateX(100%)';
        ruButton.style.transform = 'translateX(0)';
    }
}
function toggleDropdown() {
    const dropdown = document.getElementById('dropdownMenu');
    dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
}
function showLogin() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
}
function showRegister() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}
function togglePasswordVisibility(fieldId) {
    const passwordField = document.getElementById(fieldId);
    const type = passwordField.type === "password" ? "text" : "password";
    passwordField.type = type;
}
function generatePassword() {
    const randomPassword = Math.random().toString(36).slice(-8); // Генерация случайного пароля
    document.getElementById('registerPassword').value = randomPassword; // Заполнение поля пароля
}
function login() {
    const phone = document.getElementById('phone').value;
    const password = document.getElementById('password').value;
    const data = {
        action: 'login',
        phone: phone,
        password: password
    };
    fetch('/main', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Ошибка авторизации');
        }
    })
    .then(data => {
        document.getElementById('authContainer').style.display = 'none'; // Скрываем форму авторизации
        document.getElementById('profileIcon').style.display = 'block'; // Показываем иконку профиля
        if (data.redirect) {
            window.location.href = data.redirect; // Перенаправляем на главную страницу
        }
    })
    .catch(error => {
        showMessage(error.message);
    });
}
function register() {
    const name = document.getElementById('name').value;
    const phone = document.getElementById('RegisterPhone').value;
    const password = document.getElementById('registerPassword').value;
    const data = {
        action: 'register',
        name: name,
        phone: phone,
        password: password
    };
    fetch('/main', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Ошибка регистрации');
        }
    })
    .then(data => {
        document.getElementById('authContainer').style.display = 'none'; // Скрываем форму авторизации
        document.getElementById('profileIcon').style.display = 'block'; // Показываем иконку профиля
        if (data.redirect) {
            window.location.href = data.redirect; // Перенаправляем на главную страницу
        }
    })
    .catch(error => {
        showMessage(error.message);
    });
}
// Закрыть выпадающее меню, если кликнули вне его
window.onclick = function(event) {
    if (!event.target.matches('.menu-icon') && !event.target.matches('.profile-icon')) {
        const dropdown = document.getElementById('dropdownMenu');
        const authContainer = document.getElementById('authContainer');
        if (dropdown.style.display === 'block') {
            dropdown.style.display = 'none';
        }
        // Убираем условие для скрытия authContainer, чтобы оно не скрывалось
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const profileIcon = document.getElementById('profileIcon');
    const authContainer = document.getElementById('authContainer');
    if (isAuthenticated) {
        profileIcon.style.display = 'block'; // Показываем иконку профиля
        authContainer.style.display = 'none'; // Скрываем окно авторизации
    } else {
        profileIcon.style.display = 'none'; // Скрываем иконку профиля
        authContainer.style.display = 'block'; // Показываем окно авторизации
    }
});
function toggleProfile() {
    // Если пользователь авторизован, не выполняем переключение
    if (isAuthenticated) {
        window.location.href = profileUrl; 
        return; // Прерываем выполнение функции
    }
    const authContainer = document.getElementById('authContainer');
    authContainer.style.display = authContainer.style.display === 'block' ? 'none' : 'block';
}

function showMessage(message) {
    const messageContainer = document.getElementById('messageContainer'); // Предполагается, что у вас есть контейнер для сообщений
    messageContainer.innerText = message; // Устанавливаем текст сообщения
    messageContainer.style.display = 'block'; // Показываем контейнер с сообщением
    setTimeout(() => {
        messageContainer.style.display = 'none'; // Скрываем сообщение через 3 секунды
    }, 3000);
}