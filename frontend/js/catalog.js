document.addEventListener('DOMContentLoaded', async () => {
    // Проверка авторизации
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    // Элементы DOM
    const booksGrid = document.getElementById('booksGrid');
    const searchInput = document.getElementById('searchInput');
    const genreFilter = document.getElementById('genreFilter');
    const booksCount = document.getElementById('booksCount');
    const logoutBtn = document.getElementById('logout-btn');

    let allBooks = [];
    let genres = [];

    // Пагинация
    let currentPage = 1;
    const perPage = 12;
    let totalBooks = 0;

    // Надёжная заглушка обложки
    const DEFAULT_COVER = 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
        <svg xmlns="http://www.w3.org/2000/svg" width="300" height="400" viewBox="0 0 300 400">
            <rect fill="#e9ecef" width="300" height="400"/>
            <text fill="#6c757d" font-family="Arial, sans-serif" font-size="16" x="50%" y="50%" text-anchor="middle" dy=".3em">
                Нет обложки
            </text>
        </svg>
    `);

    // === ЗАГРУЗКА ЖАНРОВ ===
    async function loadGenres() {
        try {
            genres = await recommendAPI.getGenres();
            
            genres.forEach(genre => {
                const option = document.createElement('option');
                option.value = genre.genre_id;
                option.textContent = genre.genre_name;
                genreFilter.appendChild(option);
            });
        } catch (e) {
            console.error('Ошибка загрузки жанров:', e);
        }
    }

    // === ЗАГРУЗКА КНИГ (через новый эндпоинт) ===
    async function loadBooks() {
        try {
            booksGrid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Загрузка...</span>
                    </div>
                </div>
            `;

            // Получаем все книги через новый эндпоинт
            const response = await apiRequest('/books');
            allBooks = response.books;

            renderBooks(allBooks);
            
        } catch (e) {
            console.error('Ошибка загрузки книг:', e);
            booksGrid.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        ❌ Ошибка: ${e.message}
                    </div>
                </div>
            `;
        }
    }

    // === ФИЛЬТРАЦИЯ ===
    async function filterBooks(page = 1) {
        currentPage = page; // Сохраняем текущую страницу
        
        const searchTerm = searchInput.value.trim();
        const selectedGenre = genreFilter.value;
        const sortValue = document.getElementById('sortFilter').value;

        // Показываем спиннер
        booksGrid.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Загрузка...</span>
                </div>
            </div>
        `;

        try {
            const [sortField, sortOrder] = sortValue.split('-');

            const params = new URLSearchParams();
            if (searchTerm) params.append('search', searchTerm);
            if (selectedGenre) params.append('genre_id', selectedGenre);
            params.append('sort', sortField);
            params.append('order', sortOrder);
            params.append('page', page);
            params.append('per_page', perPage);

            const response = await apiRequest(`/books?${params.toString()}`);
            const filtered = response.books;
            totalBooks = response.total; // Сохраняем общее количество

            renderBooks(filtered);
            renderPagination(); // Рисуем пагинацию
            
        } catch (e) {
            console.error('Ошибка фильтрации:', e);
            booksGrid.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        ❌ Ошибка: ${e.message}
                    </div>
                </div>
            `;
        }
    }

    // === ПРОВЕРКА ВАЛИДНОСТИ URL ===
    function isValidImageUrl(url) {
        if (!url || typeof url !== 'string') return false;
        const trimmed = url.trim().toLowerCase();
        if (trimmed === '' || trimmed === 'none' || trimmed === 'null' || trimmed === 'undefined') {
            return false;
        }
        return trimmed.startsWith('http://') || trimmed.startsWith('https://');
    }

    // === ОТОБРАЖЕНИЕ КНИГ ===
    function renderBooks(books) {
        booksGrid.innerHTML = '';
        
        if (books.length === 0) {
            booksGrid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <h4>📚 Книги не найдены</h4>
                    <p class="text-muted">Попробуйте изменить параметры поиска</p>
                </div>
            `;
            booksCount.textContent = '0 книг';
            return;
        }

        books.forEach(book => {
            const col = document.createElement('div');
            col.className = 'col-md-4 col-lg-3 mb-4';
            
            const imageUrl = isValidImageUrl(book.image_url) 
                ? book.image_url 
                : DEFAULT_COVER;
            
            // Формируем бейджи жанров
            const genresHtml = book.genres && book.genres.length > 0
                ? book.genres.map(g => `<span class="badge bg-secondary genre-badge">${escapeHtml(g.genre_name)}</span>`).join(' ')
                : '';
            
            // Рейтинг
            const ratingHtml = book.avg_rating 
                ? `<span class="badge bg-success">★ ${book.avg_rating}</span>`
                : '';
            
            const card = document.createElement('div');
            card.className = 'card book-card h-100';
            card.onclick = () => openBook(book.book_id);
            
            card.innerHTML = `
                <img src="${imageUrl}" 
                     class="card-img-top book-cover" 
                     alt="${escapeHtml(book.title)}"
                     onerror="this.onerror=null; this.src='${DEFAULT_COVER}'">
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title">${escapeHtml(book.title)}</h5>
                    <h6 class="card-subtitle mb-2 text-muted">${escapeHtml(book.author)}</h6>
                    <div class="mb-2">${genresHtml}</div>
                    <div class="mt-auto">
                        <div class="d-flex justify-content-between align-items-center">
                            ${ratingHtml}
                            <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); openBook(${book.book_id})">
                                📖 Читать
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            col.appendChild(card);
            booksGrid.appendChild(col);
        });

        booksCount.textContent = `${books.length} ${getBookCountWord(books.length)}`;
    }

    // === ПАГИНАЦИЯ ===
    function renderPagination() {
        const pagination = document.getElementById('pagination');
        if (!pagination) return;

        const totalPages = Math.ceil(totalBooks / perPage);
        
        // Если страниц 1 или меньше — не показываем пагинацию
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let html = '';

        // Кнопка "Назад"
        if (currentPage > 1) {
            html += `
                <li class="page-item">
                    <button class="page-link" onclick="changePage(${currentPage - 1})">← Назад</button>
                </li>
            `;
        } else {
            html += `<li class="page-item disabled"><span class="page-link">← Назад</span></li>`;
        }

        // Номера страниц
        for (let i = 1; i <= totalPages; i++) {
            if (i === currentPage) {
                html += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
            } else {
                html += `<li class="page-item"><button class="page-link" onclick="changePage(${i})">${i}</button></li>`;
            }
        }

        // Кнопка "Вперёд"
        if (currentPage < totalPages) {
            html += `
                <li class="page-item">
                    <button class="page-link" onclick="changePage(${currentPage + 1})">Вперёд →</button>
                </li>
            `;
        } else {
            html += `<li class="page-item disabled"><span class="page-link">Вперёд →</span></li>`;
        }

        pagination.innerHTML = html;
    }

    // Глобальная функция для смены страницы
    window.changePage = function(page) {
        filterBooks(page);
        // Прокручиваем к началу каталога
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // === ЭКРАНИРОВАНИЕ HTML ===
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // === ОТКРЫТИЕ КНИГИ ===
    async function openBook(bookId) {
        window.location.href = `book_detail.html?book=${bookId}`;
    }

    // === СКЛОНЕНИЕ "КНИГА" ===
    function getBookCountWord(count) {
        if (count % 10 === 1 && count % 100 !== 11) return 'книга';
        if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return 'книги';
        return 'книг';
    }

    // === ВЫХОД ===
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('userEmail');
            window.location.href = 'index.html';
        });
    }

    // === ОБРАБОТЧИКИ ===
    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => filterBooks(1), 300);
    });
    
    genreFilter.addEventListener('change', () => filterBooks(1));
    document.getElementById('sortFilter').addEventListener('change', () => filterBooks(1));

    // === ИНИЦИАЛИЗАЦИЯ ===
    (async () => {
        await loadGenres();
        await loadBooks();
    })();
});