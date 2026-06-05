// frontend/js/auth.js

document.addEventListener('DOMContentLoaded', () => {
    // Если мы уже на dashboard.html — не проверяем токен здесь
    if (window.location.pathname.includes('dashboard.html')) {
        return;
    }

    // Если мы на index.html и токен есть — редирект на dashboard
    if (window.location.pathname.includes('index.html') || window.location.pathname === '/' || window.location.pathname.endsWith('/frontend/')) {
        if (localStorage.getItem('accessToken')) {
            window.location.href = 'dashboard.html';
        }
    }

    // Если пользователь уже залогинен, сразу кидаем его на дашборд
    if (localStorage.getItem('accessToken')) {
        window.location.href = 'dashboard.html';
    }

    // Элементы DOM
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const alertContainer = document.getElementById('alertContainer');

    // Функция показа ошибок/успеха (Bootstrap Alert)
    function showAlert(message, type = 'danger') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        alertContainer.innerHTML = alertHtml;
    }

    // Обработка входа
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault(); // Остановить стандартную отправку формы

            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const submitBtn = loginForm.querySelector('button[type="submit"]');

            // Блокируем кнопку, чтобы не нажали дважды
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Вход...';

            try {
                const data = await authAPI.login(email, password);
                
                // Сохраняем токен
                localStorage.setItem('accessToken', data.access_token);
                
                // Переход на дашборд
                window.location.href = 'dashboard.html';
            } catch (error) {
                showAlert(error.message || 'Ошибка входа');
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Войти';
            }
        });
    }

    // Обработка регистрации
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('regUsername').value;
            const email = document.getElementById('regEmail').value;
            const password = document.getElementById('regPassword').value;
            const submitBtn = registerForm.querySelector('button[type="submit"]');

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Регистрация...';

            try {
                await authAPI.register(username, email, password);
                
                showAlert('Регистрация успешна! Теперь войдите.', 'success');
                
                // Очищаем форму и переключаем на вкладку входа
                registerForm.reset();
                
                // Переключаем таб на Login (используем Bootstrap API)
                const loginTab = document.getElementById('login-tab');
                const tab = new bootstrap.Tab(loginTab);
                tab.show();
                
            } catch (error) {
                showAlert(error.message || 'Ошибка регистрации');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Зарегистрироваться';
            }
        });
    }
});