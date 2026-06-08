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
    const chaptersCount = document.getElementById('chaptersCount');
    const startReadingBtn = document.getElementById('startReadingBtn');
    const addToFavoritesBtn = document.getElementById('addToFavoritesBtn');
    const setStatusBtn = document.getElementById('setStatusBtn');
    const ratingStars = document.querySelectorAll('#ratingStars .star');
    const ratingText = document.getElementById('ratingText');
    const logoutBtn = document.getElementById('logout-btn');

    let currentBook = null;
    let currentRating = 0;
    let chaptersList = [];

    // Заглушка обложки (темная)
    const defaultCover = 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
        <svg xmlns="http://www.w3.org/2000/svg" width="350" height="525" viewBox="0 0 350 525">
            <rect fill="#2a2a2a" width="350" height="525"/>
            <text fill="#707070" font-family="Arial, sans-serif" font-size="16" x="50%" y="50%" text-anchor="middle" dy=".3em">
                Нет обложки
            </text>
        </svg>
    `);

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
            
            // Отображаем жанры
            const genresContainer = document.getElementById('bookGenres');
            if (genresContainer && currentBook.genres && currentBook.genres.length > 0) {
                genresContainer.innerHTML = currentBook.genres.map(g => 
                    `<span class="genre-badge">${escapeHtml(g.genre_name)}</span>`
                ).join('');
            }

            // Обложка
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
                <div class="empty-chapters">
                    В этой книге ещё нет глав
                </div>
            `;
            chaptersCount.textContent = '0 глав';
            startReadingBtn.disabled = true;
            return;
        }

        // Сортируем по order_number
        const sortedChapters = chapters.sort((a, b) => parseFloat(a.order_number) - parseFloat(b.order_number));

        chaptersCount.textContent = `${sortedChapters.length} ${getChapterWord(sortedChapters.length)}`;

        chaptersContainer.innerHTML = sortedChapters.map(chapter => {
            const orderNum = parseFloat(chapter.order_number);
            const displayNum = orderNum == Math.floor(orderNum) ? Math.floor(orderNum) + 1 : orderNum;
            
            return `
                <div class="chapter-item" data-chapter-id="${chapter.chapter_id}">
                    <div class="chapter-info">
                        <div class="chapter-number">Глава ${displayNum}</div>
                        <h3 class="chapter-title">${escapeHtml(chapter.title)}</h3>
                    </div>
                    <div class="chapter-action">Читать →</div>
                </div>
            `;
        }).join('');

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

    // Открытие главы
    window.openChapter = function(chapterId) {
        window.location.href = `reader.html?book=${bookId}&chapter=${chapterId}`;
    };

    // Проверка избранного
    async function checkFavoriteStatus() {
        try {
            const favorites = await booksAPI.getFavorites();
            const isFavorite = favorites.books.some(book => book.book_id === bookId);
            
            if (isFavorite) {
                addToFavoritesBtn.textContent = 'Удалить из избранного';
                addToFavoritesBtn.classList.remove('btn-action-outline');
                addToFavoritesBtn.classList.add('btn-action-danger');
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
                showToast('Оценка сохранена', 'success');
            } catch (e) {
                console.error('Ошибка сохранения оценки:', e);
                showToast(`Ошибка: ${e.message}`, 'error');
            }
        });
    });

    // Кнопка "В избранное"
    addToFavoritesBtn.addEventListener('click', async () => {
        try {
            const isFavorite = addToFavoritesBtn.textContent.includes('Удалить');
            
            if (isFavorite) {
                await booksAPI.removeFavorite(bookId);
                addToFavoritesBtn.textContent = 'В избранное';
                addToFavoritesBtn.classList.remove('btn-action-danger');
                addToFavoritesBtn.classList.add('btn-action-outline');
                showToast('Удалено из избранного', 'success');
            } else {
                await booksAPI.addFavorite(bookId);
                addToFavoritesBtn.textContent = 'Удалить из избранного';
                addToFavoritesBtn.classList.remove('btn-action-outline');
                addToFavoritesBtn.classList.add('btn-action-danger');
                showToast('Добавлено в избранное', 'success');
            }
        } catch (e) {
            console.error('Ошибка:', e);
            showToast(`Ошибка: ${e.message}`, 'error');
        }
    });

    // Кнопка "В планы"
    setStatusBtn.addEventListener('click', async () => {
        try {
            await booksAPI.setStatus(bookId, 1);
            setStatusBtn.textContent = 'Статус установлен';
            setStatusBtn.disabled = true;
            showToast('Статус "В планах" установлен', 'success');
        } catch (e) {
            console.error('Ошибка:', e);
            showToast(`Ошибка: ${e.message}`, 'error');
        }
    });

    // Выход
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('userEmail');
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

    // Склонение "глава"
    function getChapterWord(count) {
        if (count % 10 === 1 && count % 100 !== 11) return 'глава';
        if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return 'главы';
        return 'глав';
    }

    // Инициализация
    await loadBookDetails();
});