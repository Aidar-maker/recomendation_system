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

    // Заглушка обложки
    const DEFAULT_COVER = 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
        <svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450">
            <rect fill="#2a2a2a" width="300" height="450"/>
            <text fill="#707070" font-family="Arial, sans-serif" font-size="16" x="50%" y="50%" text-anchor="middle" dy=".3em">
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

    // === ЗАГРУЗКА КНИГ ===
    async function loadBooks() {
        try {
            booksGrid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Загрузка...</span>
                    </div>
                </div>
            `;

            const response = await apiRequest('/books');
            allBooks = response.books;
            totalBooks = response.total;

            renderBooks(allBooks);
            renderPagination();
            
        } catch (e) {
            console.error('Ошибка загрузки книг:', e);
            booksGrid.innerHTML = `
                <div class="col-12">
                    <div class="empty-state">
                        <div class="empty-state-title">Ошибка загрузки</div>
                        <div class="empty-state-text">${e.message}</div>
                    </div>
                </div>
            `;
        }
    }

    // === ФИЛЬТРАЦИЯ ===
    async function filterBooks(page = 1) {
        currentPage = page;
        
        const searchTerm = searchInput.value.trim();
        const selectedGenre = genreFilter.value;
        const sortValue = document.getElementById('sortFilter').value;

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
            totalBooks = response.total;

            renderBooks(filtered);
            renderPagination();
            
        } catch (e) {
            console.error('Ошибка фильтрации:', e);
            booksGrid.innerHTML = `
                <div class="col-12">
                    <div class="empty-state">
                        <div class="empty-state-title">Ошибка фильтрации</div>
                        <div class="empty-state-text">${e.message}</div>
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
                <div class="col-12">
                    <div class="empty-state">
                        <div class="empty-state-title">Книги не найдены</div>
                        <div class="empty-state-text">Попробуйте изменить параметры поиска</div>
                    </div>
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
            
            // Жанры
            const genresHtml = book.genres && book.genres.length > 0
                ? `<div class="book-genres">
                    ${book.genres.slice(0, 3).map(g => `<span class="genre-badge">${escapeHtml(g.genre_name)}</span>`).join('')}
                    ${book.genres.length > 3 ? `<span class="genre-badge">+${book.genres.length - 3}</span>` : ''}
                   </div>`
                : '';
            
            // Рейтинг
            const ratingHtml = book.avg_rating 
                ? `<span class="book-rating">★ ${book.avg_rating}</span>`
                : '<span></span>';
            
            const card = document.createElement('div');
            card.className = 'book-card';
            card.onclick = () => openBook(book.book_id);
            
            card.innerHTML = `
                <img src="${imageUrl}" 
                     class="book-cover" 
                     alt="${escapeHtml(book.title)}"
                     onerror="this.onerror=null; this.src='${DEFAULT_COVER}'">
                <div class="book-info">
                    <h5 class="book-title">${escapeHtml(book.title)}</h5>
                    <p class="book-author">${escapeHtml(book.author)}</p>
                    ${genresHtml}
                    <div class="book-meta">
                        ${ratingHtml}
                        <button class="book-btn" onclick="event.stopPropagation(); openBook(${book.book_id})">
                            Читать
                        </button>
                    </div>
                </div>
            `;
            
            col.appendChild(card);
            booksGrid.appendChild(col);
        });

        booksCount.textContent = `${totalBooks} ${getBookCountWord(totalBooks)}`;
    }

    // === ПАГИНАЦИЯ ===
    function renderPagination() {
        const pagination = document.getElementById('pagination');
        if (!pagination) return;

        const totalPages = Math.ceil(totalBooks / perPage);
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let html = '';

        // Кнопка "Назад"
        html += `<button class="page-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="changePage(${currentPage - 1})">Назад</button>`;

        // Номера страниц (показываем максимум 7 кнопок)
        let startPage = Math.max(1, currentPage - 3);
        let endPage = Math.min(totalPages, startPage + 6);
        
        if (endPage - startPage < 6) {
            startPage = Math.max(1, endPage - 6);
        }

        if (startPage > 1) {
            html += `<button class="page-btn" onclick="changePage(1)">1</button>`;
            if (startPage > 2) {
                html += `<span class="page-btn" style="cursor: default; border: none;">...</span>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                html += `<span class="page-btn" style="cursor: default; border: none;">...</span>`;
            }
            html += `<button class="page-btn" onclick="changePage(${totalPages})">${totalPages}</button>`;
        }

        // Кнопка "Вперёд"
        html += `<button class="page-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="changePage(${currentPage + 1})">Вперёд</button>`;

        pagination.innerHTML = html;
    }

    // Глобальная функция для смены страницы
    window.changePage = function(page) {
        filterBooks(page);
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