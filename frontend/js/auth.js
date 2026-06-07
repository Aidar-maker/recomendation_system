// frontend/js/auth.js

document.addEventListener('DOMContentLoaded', () => {
    // Если мы на dashboard/catalog/admin — проверяем токен
    if (window.location.pathname.includes('dashboard.html') || 
        window.location.pathname.includes('catalog.html') ||
        window.location.pathname.includes('admin.html') ||
        window.location.pathname.includes('book_detail.html') ||
        window.location.pathname.includes('reader.html')) {
        
        if (!localStorage.getItem('accessToken')) {
            window.location.href = 'index.html';
            return;
        }
    }

    // Если мы на index.html и токен есть — редирект на dashboard
    if (window.location.pathname.includes('index.html') || window.location.pathname.endsWith('/frontend/')) {
        if (localStorage.getItem('accessToken')) {
            window.location.href = 'dashboard.html';
            return;
        }
    }

    // Элементы DOM
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const alertContainer = document.getElementById('alertContainer');

    // === ОБРАБОТКА ВХОДА ===
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault(); // ← ВАЖНО: первым делом!

            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const submitBtn = loginForm.querySelector('button[type="submit"]');

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Вход...';

            try {
                const data = await authAPI.login(email, password);
                
                localStorage.setItem('accessToken', data.access_token);
                localStorage.setItem('userEmail', email);
                
                window.location.href = 'dashboard.html';
            } catch (error) {
                // Показываем ошибку
                if (typeof showToast === 'function') {
                    showToast(error.message || 'Неверный email или пароль', 'error');
                } else {
                    // Fallback если toast.js не загружен
                    if (alertContainer) {
                        alertContainer.innerHTML = `
                            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                                ${error.message || 'Неверный email или пароль'}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        `;
                    }
                }
                
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Войти';
            }
        });
    }

    // === ОБРАБОТКА РЕГИСТРАЦИИ ===
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
                
                if (typeof showToast === 'function') {
                    showToast('Регистрация успешна! Теперь войдите.', 'success');
                }
                
                registerForm.reset();
                
                const loginTab = document.getElementById('login-tab');
                if (loginTab) {
                    const tab = new bootstrap.Tab(loginTab);
                    tab.show();
                }
                
            } catch (error) {
                if (typeof showToast === 'function') {
                    showToast(error.message || 'Ошибка регистрации', 'error');
                }
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Зарегистрироваться';
            }
        });
    }

    // === ОБРАБОТЧИК ВЫХОДА ===
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('userEmail');
            window.location.href = 'index.html';
        });
    }
});