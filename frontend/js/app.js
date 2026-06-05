// frontend/js/app.js

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Проверка авторизации
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    // Элементы DOM
    const recommendationsContainer = document.getElementById('recommendations-list');
    const favoritesContainer = document.getElementById('favorites-list');
    const readingListContainer = document.getElementById('reading-list');
    const ratingsContainer = document.getElementById('ratings-list');
    
    // Кнопки обновления
    const refreshRecBtn = document.getElementById('refresh-rec');
    const refreshFavBtn = document.getElementById('refresh-fav');

    // Функции отрисовки

    // Создание HTML-карточки книги
    function createBookCard(book, type = 'recommendation') {
        const statusBadge = book.status ? getStatusBadge(book.status) : '';
        const ratingBadge = book.rating ? `<span class="badge bg-warning text-dark">★ ${book.rating}</span>` : '';
        
        let actionButtons = '';
        
        if (type === 'recommendation') {
            actionButtons = `
                <button class="btn btn-sm btn-outline-primary mt-2" onclick="addToFavorites(${book.book_id})">❤️ В избранное</button>
                <button class="btn btn-sm btn-outline-success mt-2" onclick="setStatus(${book.book_id}, 2)">📖 Читаю</button>
            `;
        } else if (type === 'favorites') {
            actionButtons = `
                <button class="btn btn-sm btn-outline-danger mt-2" onclick="removeFromFavorites(${book.book_id})">🗑 Удалить</button>
            `;
        } else if (type === 'reading') {
            actionButtons = `
                <select class="form-select form-select-sm mt-2" onchange="changeStatus(${book.book_id}, this.value)">
                    <option value="1" ${book.status == 1 ? 'selected' : ''}>📅 В планах</option>
                    <option value="2" ${book.status == 2 ? 'selected' : ''}>📖 Читаю</option>
                    <option value="3" ${book.status == 3 ? 'selected' : ''}>✅ Прочитано</option>
                    <option value="4" ${book.status == 4 ? 'selected' : ''}>❌ Брошено</option>
                </select>
            `;
        }

        return `
            <div class="col-md-4 mb-4">
                <div class="card h-100 shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title">${book.title}</h5>
                        <h6 class="card-subtitle mb-2 text-muted">${book.author}</h6>
                        <div class="d-flex gap-2 mb-2">
                            ${statusBadge}
                            ${ratingBadge}
                        </div>
                        <p class="card-text small text-truncate">${book.description || 'Нет описания'}</p>
                        ${actionButtons}
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
        const html = books.map(book => createBookCard(book, type)).join('');
        container.innerHTML = html;
    }

    // Загрузка данных

    async function loadRecommendations() {
        if (!recommendationsContainer) return;
        console.log('Загрузка рекомендаций');
        recommendationsContainer.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';
        try {
            const startTime = performance.now();
            const data = await recommendAPI.getRecommendations(10);
            const endTime = performance.now();
            
            console.log(`Получено ${data.length} книг за ${(endTime - startTime).toFixed(2)}ms`);
            console.log('Данные:', data);
            
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

    // Глобальные функции

    window.addToFavorites = async (bookId) => {
        try {
            await booksAPI.addFavorite(bookId);
            alert('Добавлено в избранное!');
            loadFavorites(); // Обновить список
        } catch (e) {
            alert(e.message);
        }
    };

    window.removeFromFavorites = async (bookId) => {
        if(!confirm('Удалить из избранного?')) return;
        try {
            await booksAPI.removeFavorite(bookId);
            loadFavorites();
        } catch (e) {
            alert(e.message);
        }
    };

    window.setStatus = async (bookId, status) => {
        try {
            await booksAPI.setStatus(bookId, status);
            loadReadingStatuses();
            loadFavorites(); // Обновить и там, если книга там есть
        } catch (e) {
            alert(e.message);
        }
    };

    window.changeStatus = async (bookId, status) => {
        try {
            await booksAPI.setStatus(bookId, status);
            loadReadingStatuses();
        } catch (e) {
            alert(e.message);
        }
    };

    // Инициализирование

    // Привязываем кнопки обновления
    if (refreshRecBtn) refreshRecBtn.addEventListener('click', loadRecommendations);
    if (refreshFavBtn) refreshFavBtn.addEventListener('click', loadFavorites);

    // Загружаем данные при открытии
    async function initDashboard(){
        loadRecommendations();
        loadFavorites();
        loadReadingStatuses();
    }

    initDashboard();
    
    // Выход из системы
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('accessToken');
            window.location.href = 'index.html';
        });
    }
});