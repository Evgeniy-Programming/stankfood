document.addEventListener("DOMContentLoaded", () => {
    const profileForm = document.getElementById("profileForm");
    if (profileForm) {
        profileForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            try {
                const payload = Object.fromEntries(new FormData(profileForm).entries());
                const response = await fetch("/profile", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.message || "Ошибка сохранения");
                }
                alert(data.message);
                window.location.reload();
            } catch (error) {
                alert(error.message);
            }
        });
    }

    document.querySelectorAll(".reorder-button").forEach((button) => {
        button.addEventListener("click", async () => {
            try {
                const response = await fetch(`/reorder/${Number(button.dataset.orderId)}`, { method: "POST" });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.message || "Не удалось повторить заказ");
                }
                window.location.href = data.redirect || "/cart";
            } catch (error) {
                alert(error.message);
            }
        });
    });

    const markReadButton = document.getElementById("markNotificationsRead");
    if (markReadButton) {
        markReadButton.addEventListener("click", async () => {
            try {
                const response = await fetch("/mark_notifications_read", { method: "POST" });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.message || "Не удалось обновить уведомления");
                }
                alert(data.message);
                window.location.reload();
            } catch (error) {
                alert(error.message);
            }
        });
    }
});
