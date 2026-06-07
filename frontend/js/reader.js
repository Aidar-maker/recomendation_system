document.addEventListener('DOMContentLoaded', async () => {
    // Проверка авторизации
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    // Получаем параметры из URL: ?book=1&chapter=3
    const urlParams = new URLSearchParams(window.location.search);
    const bookId = parseInt(urlParams.get('book'));
    const chapterId = parseInt(urlParams.get('chapter'));

    if (!bookId || !chapterId) {
        showToast('Не указаны книга или глава', 'error')
        window.location.href = 'catalog.html';
        return;
    }

    // Элементы DOM
    const bookTitleEl = document.getElementById('bookTitle');
    const chapterTitleEl = document.getElementById('chapterTitle');
    const chapterContentEl = document.getElementById('chapterContent');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const progressFill = document.getElementById('progressFill');
    const progressPercent = document.getElementById('progressPercent');

    let currentBook = null;
    let currentChapter = null;
    let chaptersList = [];

    // === ФУНКЦИИ ===

    // Загрузка книги и главы
    async function loadChapter() {
        try {
            // Сначала загружаем информацию о книге
            currentBook = await apiRequest(`/books/${bookId}`);
            bookTitleEl.textContent = currentBook.title;

            // Загружаем список глав для навигации
            chaptersList = currentBook.chapters || [];

            // Загружаем контент текущей главы
            currentChapter = await apiRequest(`/books/${bookId}/chapters/${chapterId}`);
            
            // Отображаем
            chapterTitleEl.textContent = currentChapter.title;
            chapterContentEl.innerHTML = currentChapter.content_html;

            // Настраиваем кнопки навигации
            updateNavButtons();

            // Загружаем сохранённый прогресс
            await loadProgress();

            // Начинаем отслеживать скролл для прогресса
            setupScrollTracking();

            console.log(`✅ Глава загружена: ${currentChapter.title}`);

        } catch (e) {
            console.error('Ошибка загрузки:', e);
            chapterContentEl.innerHTML = `
                <div class="alert alert-danger">
                    ❌ Ошибка: ${e.message}<br>
                    <a href="catalog.html" class="btn btn-outline-danger mt-2">← Вернуться в каталог</a>
                </div>
            `;
        }
    }

    // Обновление кнопок навигации
    function updateNavButtons() {
        const currentIndex = chaptersList.findIndex(c => c.chapter_id === chapterId);
        
        // Кнопка "Назад"
        if (currentIndex > 0) {
            const prevChapter = chaptersList[currentIndex - 1];
            prevBtn.disabled = false;
            prevBtn.onclick = () => navigateToChapter(prevChapter.chapter_id);
        } else {
            prevBtn.disabled = true;
        }

        // Кнопка "Вперёд"
        if (currentIndex < chaptersList.length - 1) {
            const nextChapter = chaptersList[currentIndex + 1];
            nextBtn.disabled = false;
            nextBtn.onclick = () => navigateToChapter(nextChapter.chapter_id);
        } else {
            nextBtn.disabled = true;
        }
    }

    // Переход к другой главе
    function navigateToChapter(newChapterId) {
        // Сохраняем прогресс перед переходом
        saveProgress();
        
        // Переход
        window.location.href = `reader.html?book=${bookId}&chapter=${newChapterId}`;
    }

    // Загрузка прогресса чтения
    async function loadProgress() {
        try {
            const progress = await apiRequest(`/reading-progress/${bookId}`);
            
            if (progress.chapter_id === chapterId && progress.position_percent > 0) {
                // Восстанавливаем позицию скролла
                const contentHeight = chapterContentEl.scrollHeight;
                const scrollPos = (progress.position_percent / 100) * contentHeight;
                window.scrollTo(0, scrollPos - 100); // -100 для отступа от верха
                updateProgressBar(progress.position_percent);
                console.log(`📍 Прогресс восстановлен: ${progress.position_percent}%`);
            }
        } catch (e) {
            console.warn('Не удалось загрузить прогресс:', e);
        }
    }

    // Отслеживание скролла для прогресса
    let scrollTimeout;
    function setupScrollTracking() {
        window.addEventListener('scroll', () => {
            // Обновляем визуальный прогресс
            const scrollTop = window.scrollY;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const percent = Math.round((scrollTop / docHeight) * 100);
            updateProgressBar(percent);

            // Автосохранение прогресса (с задержкой 2 секунды)
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                saveProgress(percent);
            }, 2000);
        });
    }

    // Обновление визуального прогресс-бара
    function updateProgressBar(percent) {
        progressFill.style.width = `${percent}%`;
        progressPercent.textContent = `${percent}%`;
    }

    // Сохранение прогресса на сервер
    async function saveProgress(percent = null) {
        if (percent === null) {
            // Вычисляем процент
            const scrollTop = window.scrollY;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            percent = Math.round((scrollTop / docHeight) * 100);
        }

        try {
            await apiRequest('/reading-progress', {
                method: 'POST',
                body: {
                    chapter_id: chapterId,
                    position_percent: percent
                }
            });
            console.log(`💾 Прогресс сохранён: ${percent}%`);
        } catch (e) {
            console.warn('Не удалось сохранить прогресс:', e);
        }
    }

    // === НАСТРОЙКИ ЧТЕНИЯ ===

    // Переключение темы
    function toggleTheme() {
        const body = document.body;
        const current = body.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        
        body.setAttribute('data-theme', next);
        localStorage.setItem('readerTheme', next);
        console.log(`🌓 Тема: ${next}`);
    }

    // Загрузка сохранённой темы
    function loadTheme() {
        const saved = localStorage.getItem('readerTheme');
        if (saved) {
            document.body.setAttribute('data-theme', saved);
        }
    }

    // Настройка размера шрифта
    function setFontSize(size) {
        const content = document.getElementById('chapterContent');
        content.classList.remove('font-small', 'font-medium', 'font-large');
        
        if (size !== 'medium') {
            content.classList.add(`font-${size}`);
        }
        
        localStorage.setItem('readerFontSize', size);
        console.log(`🔤 Размер шрифта: ${size}`);
    }

    // Загрузка сохранённого размера шрифта
    function loadFontSize() {
        const saved = localStorage.getItem('readerFontSize');
        if (saved) {
            setFontSize(saved);
        }
    }

    // === ИНИЦИАЛИЗАЦИЯ ===

    // Загружаем настройки
    loadTheme();
    loadFontSize();

    // Делаем функции доступными глобально (для onclick в HTML)
    window.toggleTheme = toggleTheme;
    window.setFontSize = setFontSize;

    // Загружаем главу
    await loadChapter();

    // Сохраняем прогресс при уходе со страницы
    window.addEventListener('beforeunload', () => {
        saveProgress();
    });
});