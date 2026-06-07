document.addEventListener('DOMContentLoaded', async () => {
    // Проверка авторизации
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    // Получаем ID книги из URL: ?book=1
    const urlParams = new URLSearchParams(window.location.search);
    const bookId = parseInt(urlParams.get('book'));

    if (!bookId) {
        showToast('Не указана книга', 'error');
        window.location.href = 'catalog.html';
        return;
    }

    // Элементы DOM
    const bookTitle = document.getElementById('bookTitle');
    const bookAuthor = document.getElementById('bookAuthor');
    const bookYear = document.getElementById('bookYear');
    const bookPublisher = document.getElementById('bookPublisher');
    const bookDescription = document.getElementById('bookDescription');
    const bookCover = document.getElementById('bookCover');
    const chaptersContainer = document.getElementById('chaptersContainer');
    const startReadingBtn = document.getElementById('startReadingBtn');
    const addToFavoritesBtn = document.getElementById('addToFavoritesBtn');
    const setStatusBtn = document.getElementById('setStatusBtn');
    const ratingStars = document.querySelectorAll('#ratingStars .star');
    const ratingText = document.getElementById('ratingText');
    const logoutBtn = document.getElementById('logout-btn');

    let currentBook = null;
    let currentRating = 0;
    let chaptersList = [];

    // === ЗАГРУЗКА ДАННЫХ ===

    async function loadBookDetails() {
        try {
            currentBook = await apiRequest(`/books/${bookId}`);
            
            // Заполняем информацию
            bookTitle.textContent = currentBook.title;
            bookAuthor.textContent = currentBook.author;
            bookYear.textContent = currentBook.year_publication || '—';
            bookPublisher.textContent = currentBook.publisher || '—';
            bookDescription.textContent = currentBook.description || 'Описание отсутствует';
            
            // Обложка - проверяем на валидность
            const defaultCover = 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="300" height="400" viewBox="0 0 300 400">
                    <rect fill="#e9ecef" width="300" height="400"/>
                    <text fill="#6c757d" font-family="Arial, sans-serif" font-size="16" x="50%" y="50%" text-anchor="middle" dy=".3em">
                        Нет обложки
                    </text>
                </svg>
            `);
            
            if (currentBook.image_url && 
                currentBook.image_url.trim() !== '' && 
                currentBook.image_url.toLowerCase() !== 'none' &&
                currentBook.image_url.toLowerCase() !== 'null') {
                bookCover.src = currentBook.image_url;
            } else {
                bookCover.src = defaultCover;
            }

            // Загружаем главы
            chaptersList = currentBook.chapters || [];
            loadChapters(chaptersList);

            // Загружаем статус избранного
            await checkFavoriteStatus();

            // Загружаем текущую оценку
            await loadCurrentRating();

            console.log('✅ Книга загружена:', currentBook.title);

        } catch (e) {
            console.error('Ошибка загрузки:', e);
            bookTitle.textContent = 'Ошибка загрузки';
            bookDescription.textContent = e.message;
        }
    }

    // Отображение списка глав
    function loadChapters(chapters) {
        if (chapters.length === 0) {
            chaptersContainer.innerHTML = `
                <div class="text-center text-muted py-3">
                    📚 В этой книге ещё нет глав
                </div>
            `;
            startReadingBtn.disabled = true;
            return;
        }

        // Сортируем по order_number
        const sortedChapters = chapters.sort((a, b) => a.order_number - b.order_number);

        chaptersContainer.innerHTML = sortedChapters.map(chapter => `
            <div class="chapter-item" data-chapter-id="${chapter.chapter_id}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>Глава ${chapter.order_number + 1}:</strong> ${escapeHtml(chapter.title)}
                    </div>
                    <span class="badge bg-primary">Читать →</span>
                </div>
            </div>
        `).join('');

        // Добавляем обработчики кликов на главы
        document.querySelectorAll('.chapter-item').forEach(item => {
            item.addEventListener('click', function() {
                const chapterId = parseInt(this.dataset.chapterId);
                openChapter(chapterId);
            });
        });

        // Кнопка "Начать чтение" ведёт на первую главу
        const firstChapter = sortedChapters[0];
        startReadingBtn.onclick = () => openChapter(firstChapter.chapter_id);
    }

    // Открытие главы (сделаем глобальной)
    window.openChapter = function(chapterId) {
        window.location.href = `reader.html?book=${bookId}&chapter=${chapterId}`;
    };

    // Проверка, добавлена ли книга в избранное
    async function checkFavoriteStatus() {
        try {
            const favorites = await booksAPI.getFavorites();
            const isFavorite = favorites.books.some(book => book.book_id === bookId);
            
            if (isFavorite) {
                addToFavoritesBtn.textContent = '💔 Удалить из избранного';
                addToFavoritesBtn.classList.remove('btn-outline-danger');
                addToFavoritesBtn.classList.add('btn-danger');
            }
        } catch (e) {
            console.warn('Не удалось проверить избранное:', e);
        }
    }

    // Загрузка текущей оценки
    async function loadCurrentRating() {
        try {
            const ratings = await ratingsAPI.getMyRatings();
            const myRating = ratings.books.find(book => book.book_id === bookId);
            
            if (myRating) {
                currentRating = myRating.rating;
                updateRatingDisplay(currentRating);
            }
        } catch (e) {
            console.warn('Не удалось загрузить оценку:', e);
        }
    }

    // Обновление отображения рейтинга
    function updateRatingDisplay(rating) {
        ratingStars.forEach(star => {
            const starRating = parseInt(star.dataset.rating);
            if (starRating <= rating) {
                star.classList.add('active');
            } else {
                star.classList.remove('active');
            }
        });
        ratingText.textContent = rating > 0 ? `${rating} из 10` : 'Не оценено';
    }

    // Обработчики звёзд рейтинга
    ratingStars.forEach(star => {
        star.addEventListener('click', async () => {
            const rating = parseInt(star.dataset.rating);
            try {
                await ratingsAPI.setRating(bookId, rating);
                currentRating = rating;
                updateRatingDisplay(rating);
                console.log(`⭐ Оценка сохранена: ${rating}`);
            } catch (e) {
                console.error('Ошибка сохранения оценки:', e);
                showToast(`Ошибка: ${e.message}`, 'error')
            }
        });
    });

    // Кнопка "В избранное"
    addToFavoritesBtn.addEventListener('click', async () => {
        try {
            const isFavorite = addToFavoritesBtn.textContent.includes('Удалить');
            
            if (isFavorite) {
                await booksAPI.removeFavorite(bookId);
                addToFavoritesBtn.textContent = '❤️ В избранное';
                addToFavoritesBtn.classList.remove('btn-danger');
                addToFavoritesBtn.classList.add('btn-outline-danger');
                console.log('💔 Удалено из избранного');
            } else {
                await booksAPI.addFavorite(bookId);
                addToFavoritesBtn.textContent = '💔 Удалить из избранного';
                addToFavoritesBtn.classList.remove('btn-outline-danger');
                addToFavoritesBtn.classList.add('btn-danger');
                console.log('❤️ Добавлено в избранное');
            }
        } catch (e) {
            console.error('Ошибка:', e);
            showToast(`Ошибка: ${e.message}`, 'error')
        }
    });

    // Кнопка "В планы"
    setStatusBtn.addEventListener('click', async () => {
        try {
            await booksAPI.setStatus(bookId, 1); // 1 = В планах
            setStatusBtn.textContent = '✅ Статус установлен';
            setStatusBtn.disabled = true;
            console.log('📖 Статус "В планах" установлен');
        } catch (e) {
            console.error('Ошибка:', e);
            showToast(`Ошибка: ${e.message}`, 'error');
        }
    });

    // Выход
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('accessToken');
            window.location.href = 'index.html';
        });
    }

    // Экранирование HTML
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Инициализация
    await loadBookDetails();
});