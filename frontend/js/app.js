// frontend/js/app.js
document.addEventListener('DOMContentLoaded', async () => {
    // 1. Проверка авторизации
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    // 2. Загружаем последнюю читаемую книгу
    await loadContinueReading();

    // Элементы DOM
    const recommendationsContainer = document.getElementById('recommendations-list');
    const favoritesContainer = document.getElementById('favorites-list');
    const readingListContainer = document.getElementById('reading-list');
    const ratingsContainer = document.getElementById('ratings-list');
    
    // Кнопки обновления
    const refreshRecBtn = document.getElementById('refresh-rec');
    const refreshFavBtn = document.getElementById('refresh-fav');

    // === ОТКРЫТИЕ КНИГИ ===
    function openBook(bookId) {
        window.location.href = `book_detail.html?book=${bookId}`;
    }
    window.openBook = openBook;

    // Функции отрисовки

    // Создание HTML-карточки книги
    function createBookCard(book, type = 'recommendation') {
        const statusBadge = book.status ? getStatusBadge(book.status) : '';
        const ratingBadge = book.rating ? `<span class="badge bg-warning text-dark">★ ${book.rating}</span>` : '';
        
        let actionButtons = '';
        
        if (type === 'recommendation') {
            actionButtons = `
                <button class="btn btn-sm btn-outline-primary mt-2 me-1" onclick="event.stopPropagation(); addToFavorites(${book.book_id});">❤️ В избранное</button>
                <button class="btn btn-sm btn-outline-success mt-2" onclick="event.stopPropagation(); setStatus(${book.book_id}, 2);">📖 Читаю</button>
            `;
        } else if (type === 'favorites') {
            actionButtons = `
                <button class="btn btn-sm btn-outline-danger mt-2" onclick="event.stopPropagation(); removeFromFavorites(${book.book_id});">🗑 Удалить</button>
            `;
        } else if (type === 'reading') {
            actionButtons = `
                <select class="form-select form-select-sm mt-2" onchange="event.stopPropagation(); changeStatus(${book.book_id}, this.value);">
                    <option value="1" ${book.status == 1 ? 'selected' : ''}>📅 В планах</option>
                    <option value="2" ${book.status == 2 ? 'selected' : ''}>📖 Читаю</option>
                    <option value="3" ${book.status == 3 ? 'selected' : ''}>✅ Прочитано</option>
                    <option value="4" ${book.status == 4 ? 'selected' : ''}>❌ Брошено</option>
                </select>
            `;
        }

        return `
            <div class="col-md-4 mb-4">
                <div class="card h-100 shadow-sm book-card-clickable" style="cursor: pointer;" data-book-id="${book.book_id}">
                    <div class="card-body">
                        <h5 class="card-title">${book.title}</h5>
                        <h6 class="card-subtitle mb-2 text-muted">${book.author}</h6>
                        <div class="d-flex gap-2 mb-2">
                            ${statusBadge}
                            ${ratingBadge}
                        </div>
                        <p class="card-text small text-truncate">${book.description || 'Нет описания'}</p>
                        <div class="card-actions">
                            ${actionButtons}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    function getStatusBadge(status) {
        const map = {
            1: '<span class="badge bg-secondary">📅 В планах</span>',
            2: '<span class="badge bg-info text-dark">📖 Читаю</span>',
            3: '<span class="badge bg-success">✅ Прочитано</span>',
            4: '<span class="badge bg-danger">❌ Брошено</span>'
        };
        return map[status] || '';
    }

    function renderBooks(container, books, type) {
        if (!container) return;
        container.innerHTML = '';
        if (books.length === 0) {
            container.innerHTML = '<div class="col-12 text-center text-muted py-5">Список пуст</div>';
            return;
        }
        
        // Создаём HTML для всех карточек
        const html = books.map(book => createBookCard(book, type)).join('');
        container.innerHTML = html;
        
        // Добавляем обработчики кликов на карточки ПОСЛЕ вставки в DOM
        container.querySelectorAll('.book-card-clickable').forEach(card => {
            card.addEventListener('click', function(e) {
                // Проверяем что клик не по кнопкам
                if (!e.target.closest('button') && !e.target.closest('select')) {
                    const bookId = this.dataset.bookId;
                    openBook(bookId);
                }
            });
        });
    }

    // Загрузка данных
    async function loadContinueReading() {
        try {
            const continueBlock = document.getElementById('continueReadingBlock');
            if (!continueBlock) return;

            const statusesData = await booksAPI.getStatuses(2);
            
            if (statusesData.books.length === 0) {
                continueBlock.style.display = 'none';
                return;
            }

            const lastBook = statusesData.books[0];
            const progress = await apiRequest(`/reading-progress/${lastBook.book_id}`);
            
            if (progress.chapter_id) {
                document.getElementById('continueBookTitle').textContent = lastBook.title;
                document.getElementById('continueReadingBtn').onclick = () => {
                    window.location.href = `reader.html?book=${lastBook.book_id}&chapter=${progress.chapter_id}`;
                };
                continueBlock.style.display = 'block';
                
                console.log('✅ Найдена книга для продолжения:', lastBook.title);
            } else {
                continueBlock.style.display = 'none';
            }
            
        } catch (e) {
            console.warn('Не удалось загрузить последнюю книгу:', e);
        }
    }

    async function loadRecommendations() {
        if (!recommendationsContainer) return;
        console.log('Загрузка рекомендаций');
        recommendationsContainer.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';
        try {
            const startTime = performance.now();
            const data = await recommendAPI.getRecommendations(10);
            const endTime = performance.now();
            
            console.log(`Получено ${data.length} книг за ${(endTime - startTime).toFixed(2)}ms`);
            
            const books = Array.isArray(data) ? data : []; 
            renderBooks(recommendationsContainer, books, 'recommendation');
        } catch (e) {
            console.error(e);
        }
    }

    async function loadFavorites() {
        if (!favoritesContainer) return;
        favoritesContainer.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';
        try {
            const response = await booksAPI.getFavorites();
            renderBooks(favoritesContainer, response.books, 'favorites');
        } catch (e) {
            console.error(e);
        }
    }

    async function loadReadingStatuses() {
        if (!readingListContainer) return;
        readingListContainer.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';
        try {
            const response = await booksAPI.getStatuses();
            renderBooks(readingListContainer, response.books, 'reading');
        } catch (e) {
            console.error(e);
        }
    }

    async function loadStats() {
        const container = document.getElementById('statsContainer');
        if (!container) return;
        
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="spinner-border text-primary" role="status"></div>
            </div>
        `;
        
        try {
            const stats = await statsAPI.getReadingStats();
            
            const createStatCard = (title, value, icon, color) => `
                <div class="col-md-4 col-lg-2">
                    <div class="card h-100 text-center shadow-sm">
                        <div class="card-body">
                            <div class="display-4 mb-2">${icon}</div>
                            <h2 class="card-title text-${color} fw-bold">${value}</h2>
                            <p class="card-text text-muted small">${title}</p>
                        </div>
                    </div>
                </div>
            `;
            
            container.innerHTML = `
                ${createStatCard('Всего в библиотеке', stats.total_books, '📚', 'primary')}
                ${createStatCard('Прочитано', stats.books_read, '✅', 'success')}
                ${createStatCard('Читаю сейчас', stats.books_reading, '📖', 'info')}
                ${createStatCard('В планах', stats.books_planned, '📅', 'secondary')}
                ${createStatCard('Брошено', stats.books_dropped, '❌', 'danger')}
                ${createStatCard('Средняя оценка', stats.average_rating, '⭐', 'warning')}
            `;
            
        } catch (e) {
            console.error('Ошибка загрузки статистики:', e);
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">❌ Ошибка загрузки статистики</div>
                </div>
            `;
        }
    }

    // Глобальные функции

    window.addToFavorites = async (bookId) => {
        try {
            await booksAPI.addFavorite(bookId);
            showToast('Добавлено в избранное!', 'success');
            loadFavorites();
        } catch (e) {
            showToast(e.message, 'error');
        }
    };

    window.removeFromFavorites = async (bookId) => {
        if(!confirm('Удалить из избранного?')) return;
        try {
            await booksAPI.removeFavorite(bookId);
            showToast('Удалено из избранного', 'success');
            loadFavorites();
        } catch (e) {
            showToast(e.message, 'error');
        }
    };

    window.setStatus = async (bookId, status) => {
        try {
            await booksAPI.setStatus(bookId, status);
            showToast('Статус установлен', 'success');
            loadReadingStatuses();
            loadFavorites();
        } catch (e) {
            showToast(e.message, 'error');
        }
    };

    window.changeStatus = async (bookId, status) => {
        try {
            await booksAPI.setStatus(bookId, status);
            showToast('Статус изменён', 'success');
            loadReadingStatuses();
        } catch (e) {
            showToast(e.message, 'error');
        }
    };

    // Инициализирование

    if (refreshRecBtn) refreshRecBtn.addEventListener('click', loadRecommendations);
    if (refreshFavBtn) refreshFavBtn.addEventListener('click', loadFavorites);

    async function initDashboard(){
        await loadRecommendations();
        await loadFavorites();
        await loadReadingStatuses();
        await loadStats();
    }

    initDashboard();
    
    // Выход из системы
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('userEmail');
            window.location.href = 'index.html';
        });
    }

    // === ЭКСПОРТ БИБЛИОТЕКИ (только для админов) ===
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', async () => {
            try {
                const token = localStorage.getItem('accessToken');
                
                const response = await fetch(`${API_URL}/library/export`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.status === 403) {
                    showToast('Доступ запрещен: только для администраторов', 'error');
                    return;
                }

                if (!response.ok) {
                    throw new Error('Ошибка сервера при экспорте');
                }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `library_${new Date().toISOString().slice(0,10)}.csv`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);

                showToast('Библиотека экспортирована!', 'success');
                
            } catch (e) {
                console.error('Ошибка экспорта:', e);
                showToast(`Ошибка экспорта: ${e.message}`, 'error');
            }
        });
    }
});