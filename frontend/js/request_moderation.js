document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    const requestForm = document.getElementById('requestForm');
    const myRequestsContainer = document.getElementById('myRequestsContainer');
    const logoutBtn = document.getElementById('logout-btn');

    // Подача запроса
    if (requestForm) {
        requestForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const title = document.getElementById('requestTitle').value;
            const description = document.getElementById('requestDescription').value;

            const submitBtn = requestForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Отправка...';

            try {
                await apiRequest('/moderation/request', {
                    method: 'POST',
                    body: { title, description }
                });

                showToast('Запрос отправлен на модерацию!', 'success');
                requestForm.reset();
                await loadMyRequests();

            } catch (error) {
                showToast(`Ошибка: ${error.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Отправить запрос';
            }
        });
    }

    // Загрузка моих запросов
    async function loadMyRequests() {
        try {
            const requests = await apiRequest('/moderation/my-requests');
            
            if (requests.length === 0) {
                myRequestsContainer.innerHTML = '<div class="empty-state">У вас пока нет запросов</div>';
                return;
            }

            myRequestsContainer.innerHTML = `<div class="requests-list">` + 
                requests.map(req => `
                    <div class="request-item">
                        <h6 class="request-item-title">${escapeHtml(req.title)}</h6>
                        <span class="status-badge status-${req.status}">${getStatusText(req.status)}</span>
                        ${req.admin_note ? `<div class="request-note"><b>Комментарий:</b> ${escapeHtml(req.admin_note)}</div>` : ''}
                        ${req.created_at ? `<span class="request-date">${new Date(req.created_at).toLocaleDateString('ru-RU')}</span>` : ''}
                    </div>
                `).join('') +
            `</div>`;

        } catch (e) {
            console.error('Ошибка загрузки запросов:', e);
            myRequestsContainer.innerHTML = '<div class="empty-state">Ошибка загрузки</div>';
        }
    }

    // Вспомогательная функция для статуса
    function getStatusText(status) {
        const map = {
            'pending': 'На рассмотрении',
            'approved': 'Одобрено',
            'rejected': 'Отклонено'
        };
        return map[status] || status;
    }

    // Экранирование HTML
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Выход
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('userEmail');
            window.location.href = 'index.html';
        });
    }

    await loadMyRequests();
});