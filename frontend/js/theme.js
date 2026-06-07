/**
 * Глобальная система тем для всего сайта
 * Три темы: light (белая), cream (кремовая), dark (тёмная)
 */

// Определения тем
const THEMES = {
    light: {
        name: 'light',
        label: '☀️ Светлая',
        bg: '#ffffff',
        text: '#212529',
        cardBg: '#f8f9fa',
        navbarBg: '#212529',
        navbarText: '#ffffff',
        border: '#dee2e6',
        muted: '#6c757d',
        inputBg: '#ffffff',
        inputBorder: '#ced4da'
    },
    cream: {
        name: 'cream',
        label: '📜 Кремовая',
        bg: '#f5f0e8',
        text: '#3d3529',
        cardBg: '#faf6ee',
        navbarBg: '#5c4f3d',
        navbarText: '#f5f0e8',
        border: '#d4c9b8',
        muted: '#8b7d6b',
        inputBg: '#faf6ee',
        inputBorder: '#d4c9b8'
    },
    dark: {
        name: 'dark',
        label: '🌙 Тёмная',
        bg: '#1a1a2e',
        text: '#e9ecef',
        cardBg: '#16213e',
        navbarBg: '#0f0f1e',
        navbarText: '#e9ecef',
        border: '#2a2a4a',
        muted: '#8b8ba7',
        inputBg: '#16213e',
        inputBorder: '#2a2a4a'
    }
};

// Применить тему к странице
function applyTheme(themeName) {
    const theme = THEMES[themeName];
    if (!theme) return;

    const root = document.documentElement;
    root.setAttribute('data-theme', themeName);

    // Сохраняем выбор
    localStorage.setItem('siteTheme', themeName);

    // Обновляем иконку переключателя если он есть
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.textContent = theme.label;
    }

    console.log(`🎨 Тема применена: ${theme.label}`);
}

// Переключить на следующую тему
function cycleTheme() {
    const current = localStorage.getItem('siteTheme') || 'light';
    const order = ['light', 'cream', 'dark'];
    const currentIndex = order.indexOf(current);
    const nextIndex = (currentIndex + 1) % order.length;
    applyTheme(order[nextIndex]);
}

// Загрузить сохранённую тему при старте
function loadSavedTheme() {
    const saved = localStorage.getItem('siteTheme') || 'light';
    applyTheme(saved);
}

// Делаем функции глобальными
window.applyTheme = applyTheme;
window.cycleTheme = cycleTheme;
window.loadSavedTheme = loadSavedTheme;

// === ВАЖНО: Применяем тему СРАЗУ, не ждём DOMContentLoaded ===
(function() {
    const saved = localStorage.getItem('siteTheme') || 'light';
    const root = document.documentElement;
    root.setAttribute('data-theme', saved);
    
    // Обновляем кнопку если она уже есть в DOM
    setTimeout(() => {
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            const theme = THEMES[saved];
            themeToggle.textContent = theme.label;
        }
    }, 100);
})();

// Дополнительно: применяем тему когда DOM готов (на случай если кнопка появилась позже)
document.addEventListener('DOMContentLoaded', () => {
    loadSavedTheme();
});