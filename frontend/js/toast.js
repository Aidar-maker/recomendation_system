/**
 * Toast-уведомления — замена alert()
 * Показывает красивые уведомления в правом верхнем углу
 */

// Создаём контейнер для toast-ов (один раз при загрузке)
function getToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }
    return container;
}

/**
 * Показать toast-уведомление
 * @param {string} message - Текст уведомления
 * @param {string} type - Тип: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Время показа в мс (по умолчанию 3000)
 */
function showToast(message, type = 'info', duration = 3000) {
    const container = getToastContainer();
    
    // Иконки для разных типов
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    // Цвета для разных типов
    const colors = {
        success: '#198754',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#0dcaf0'
    };
    
    // Создаём элемент toast
    const toast = document.createElement('div');
    toast.style.cssText = `
        background: white;
        border-left: 4px solid ${colors[type]};
        border-radius: 8px;
        padding: 15px 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        gap: 12px;
        animation: slideIn 0.3s ease-out;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    
    toast.innerHTML = `
        <span style="font-size: 1.5rem;">${icons[type]}</span>
        <div style="flex-grow: 1; color: #333; font-size: 0.95rem;">${message}</div>
        <button style="background: none; border: none; cursor: pointer; font-size: 1.2rem; color: #999; padding: 0 5px;" onclick="this.parentElement.remove()">×</button>
    `;
    
    container.appendChild(toast);
    
    // Автоматическое удаление через duration мс
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Добавляем CSS-анимации
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Делаем функцию глобальной
window.showToast = showToast;