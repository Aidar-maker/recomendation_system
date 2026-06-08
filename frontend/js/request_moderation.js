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
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Отправка...';

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
                submitBtn.innerHTML = '📤 Отправить запрос';
            }
        });
    }

    // Загрузка моих запросов
    async function loadMyRequests() {
        try {
            const requests = await apiRequest('/moderation/my-requests');
            
            if (requests.length === 0) {
                myRequestsContainer.innerHTML = '<p class="text-muted">У вас пока нет запросов</p>';
                return;
            }

            const statusColors = {
                'pending': 'warning',
                'approved': 'success',
                'rejected': 'danger'
            };

            const statusTexts = {
                'pending': ' На рассмотрении',
                'approved': '✅ Одобрено',
                'rejected': ' Отклонено'
            };

            myRequestsContainer.innerHTML = requests.map(req => `
                <div class="border-bottom pb-2 mb-2">
                    <h6 class="mb-1">${req.title}</h6>
                    <span class="badge bg-${statusColors[req.status]}">${statusTexts[req.status]}</span>
                    ${req.admin_note ? `<p class="small text-muted mt-1">Комментарий: ${req.admin_note}</p>` : ''}
                </div>
            `).join('');

        } catch (e) {
            console.error('Ошибка загрузки запросов:', e);
            myRequestsContainer.innerHTML = '<p class="text-danger">Ошибка загрузки</p>';
        }
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