/**
 * Проверка прав доступа
 * Скрывает элементы админа для обычных пользователей
 */

async function checkAdminAccess() {
    const token = localStorage.getItem('accessToken');
    if (!token) return false;

    try {
        const user = await userAPI.getMe();
        const isAdmin = user.role === 'admin';
        
        // Сохраняем роль в localStorage для быстрого доступа
        localStorage.setItem('userRole', user.role);
        
        return isAdmin;
    } catch (e) {
        console.error('Ошибка проверки прав:', e);
        return false;
    }
}

// Функция для скрытия админских элементов
function hideAdminElements() {
    // Скрываем все элементы с классом admin-only
    document.querySelectorAll('.admin-only').forEach(el => {
        el.style.display = 'none';
    });
}

// Функция для показа админских элементов
function showAdminElements() {
    document.querySelectorAll('.admin-only').forEach(el => {
        el.style.display = '';
    });
}

// Автоматическая проверка при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    const isAdmin = await checkAdminAccess();
    
    if (isAdmin) {
        showAdminElements();
    } else {
        hideAdminElements();
    }
});