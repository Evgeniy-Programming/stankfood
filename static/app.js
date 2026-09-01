async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const isJson = response.headers.get("content-type")?.includes("application/json");
    const data = isJson ? await response.json() : {};
    if (!response.ok) {
        throw new Error(data.message || "Ошибка запроса");
    }
    return data;
}

async function postJson(url, payload) {
    return requestJson(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
}

function bindNavToggle() {
    const button = document.querySelector(".nav-toggle");
    const nav = document.querySelector(".site-nav");
    if (!button || !nav) return;
    button.addEventListener("click", () => nav.classList.toggle("open"));
}

function bindAuthForms() {
    ["loginForm", "registerForm"].forEach((formId) => {
        const form = document.getElementById(formId);
        if (!form) return;
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            try {
                const payload = Object.fromEntries(new FormData(form).entries());
                const data = await postJson("/main", payload);
                if (data.redirect) {
                    window.location.href = data.redirect;
                    return;
                }
                window.location.reload();
            } catch (error) {
                alert(error.message);
            }
        });
    });
}

function bindAddToCartButtons() {
    document.querySelectorAll(".add-to-cart").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                await postJson("/update_cart", {
                    dish_id: Number(button.dataset.dishId),
                    quantity: Number(button.dataset.quantity || 1),
                });
                alert("Блюдо добавлено в корзину");
                window.location.href = "/cart";
            } catch (error) {
                alert(error.message);
            }
        });
    });
}

function bindUpdateCartButtons() {
    document.querySelectorAll(".update-cart").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                await postJson("/update_cart", {
                    dish_id: Number(button.dataset.dishId),
                    quantity: Number(button.dataset.quantity),
                });
                window.location.reload();
            } catch (error) {
                alert(error.message);
            }
        });
    });
}

function bindFavoriteButtons() {
    document.querySelectorAll(".toggle-favorite").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                const data = await postJson(`/favorite/${Number(button.dataset.dishId)}`, {});
                button.textContent = data.favorite ? "В любимых" : "В любимое";
                alert(data.message);
            } catch (error) {
                alert(error.message);
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    bindNavToggle();
    bindAuthForms();
    bindAddToCartButtons();
    bindUpdateCartButtons();
    bindFavoriteButtons();
});
