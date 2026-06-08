/**
 * Система тем - 3 темы (light, cream, dark)
 */

const THEMES = {
    light: { name: 'light', label: '☀️ Светлая' },
    cream: { name: 'cream', label: '📜 Кремовая' },
    dark: { name: 'dark', label: '🌙 Тёмная' }
};

function applyTheme(themeName) {
    const theme = THEMES[themeName];
    if (!theme) return;

    document.documentElement.setAttribute('data-theme', themeName);
    localStorage.setItem('siteTheme', themeName);

    // Обновляем кнопки если они есть
    document.querySelectorAll('#themeToggle').forEach(btn => {
        btn.textContent = theme.label;
    });

    console.log(`🎨 Тема: ${theme.label}`);
}

function cycleTheme() {
    const current = localStorage.getItem('siteTheme') || 'light';
    const order = ['light', 'cream', 'dark'];
    const nextIndex = (order.indexOf(current) + 1) % 3;
    applyTheme(order[nextIndex]);
}

// Применяем тему сразу при загрузке
(function() {
    const saved = localStorage.getItem('siteTheme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
})();

// Глобальные функции
window.applyTheme = applyTheme;
window.cycleTheme = cycleTheme;