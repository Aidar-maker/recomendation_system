/**
 * Управление информацией о пользователе
 */

// Показать email пользователя в navbar
function displayUserEmail() {
    const userEmailEl = document.getElementById('user-email');
    if (userEmailEl) {
        const email = localStorage.getItem('userEmail');
        if (email) {
            userEmailEl.textContent = email;
        } else {
            userEmailEl.textContent = 'Загрузка...';
        }
    }
}

// Очистить данные пользователя при выходе
function clearUserData() {
    localStorage.removeItem('userEmail');
    localStorage.removeItem('accessToken');
}

// Инициализация (если на странице есть элемент #user-email)
document.addEventListener('DOMContentLoaded', () => {
    const userEmailEl = document.getElementById('user-email');
    if (userEmailEl) {
        displayUserEmail();
    }
});