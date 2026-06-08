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
        showToast('Не указаны книга или глава', 'error');
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
            currentBook = await apiRequest(`/books/${bookId}`);
            bookTitleEl.textContent = currentBook.title;

            currentChapter = await apiRequest(`/books/${bookId}/chapters/${chapterId}`);
            
            chapterTitleEl.textContent = currentChapter.title;
            chapterContentEl.innerHTML = currentChapter.content_html;

            // Обновляем кнопки навигации с учётом всех глав
            updateNavButtons(currentChapter.all_chapters || []);

            await loadProgress();
            setupScrollTracking();

        } catch (e) {
            console.error('Ошибка загрузки:', e);
            chapterContentEl.innerHTML = `
                <div class="error-state">
                    <div class="error-title">Ошибка загрузки</div>
                    <p>${e.message}</p>
                    <a href="catalog.html" class="error-link">Вернуться в каталог</a>
                </div>
            `;
        }
    }

    // Обновление кнопок навигации
    function updateNavButtons(allChapters) {
        const currentIndex = allChapters.findIndex(c => c.chapter_id === chapterId);
        
        // Кнопка "Назад"
        if (currentIndex > 0) {
            const prevChapter = allChapters[currentIndex - 1];
            prevBtn.disabled = false;
            prevBtn.textContent = `← ${prevChapter.display_name}`;
            prevBtn.onclick = () => navigateToChapter(prevChapter.chapter_id);
        } else {
            prevBtn.disabled = true;
            prevBtn.textContent = '← Начало';
        }

        // Кнопка "Вперёд"
        if (currentIndex < allChapters.length - 1) {
            const nextChapter = allChapters[currentIndex + 1];
            nextBtn.disabled = false;
            nextBtn.textContent = `${nextChapter.display_name} →`;
            nextBtn.onclick = () => navigateToChapter(nextChapter.chapter_id);
        } else {
            nextBtn.disabled = true;
            nextBtn.textContent = 'Конец';
        }

        // Добавляем выпадающий список глав
        renderChapterSelector(allChapters, currentIndex);
    }

    function renderChapterSelector(allChapters, currentIndex) {
        const selectorBottom = document.getElementById('chapterSelectorBottom');
        if (!selectorBottom) return;

        const options = allChapters.map((chapter, index) => {
            const isSelected = index === currentIndex;
            return `<option value="${chapter.chapter_id}" ${isSelected ? 'selected' : ''}>
                ${chapter.display_name}: ${chapter.title}
            </option>`;
        }).join('');

        selectorBottom.innerHTML = options;
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
                window.scrollTo(0, scrollPos - 100);
                updateProgressBar(progress.position_percent);
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
        } catch (e) {
            console.warn('Не удалось сохранить прогресс:', e);
        }
    }

    // === НАСТРОЙКИ ЧТЕНИЯ ===

    function toggleTheme() {
        cycleTheme();
    }

    function loadTheme() {
        // Тема загружается автоматически через theme.js
    }

    // Настройка размера шрифта
    function setFontSize(size) {
        const content = document.getElementById('chapterContent');
        content.classList.remove('font-small', 'font-medium', 'font-large');
        
        if (size !== 'medium') {
            content.classList.add(`font-${size}`);
        } else {
            content.classList.add('font-medium');
        }
        
        // Обновляем активную кнопку
        document.querySelectorAll('.font-size-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');
        
        localStorage.setItem('readerFontSize', size);
    }

    // Загрузка сохранённого размера шрифта
    function loadFontSize() {
        const saved = localStorage.getItem('readerFontSize');
        if (saved) {
            const content = document.getElementById('chapterContent');
            content.classList.remove('font-small', 'font-medium', 'font-large');
            
            if (saved !== 'medium') {
                content.classList.add(`font-${saved}`);
            } else {
                content.classList.add('font-medium');
            }
            
            // Обновляем активную кнопку
            document.querySelectorAll('.font-size-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.textContent.includes(saved === 'small' ? '-' : saved === 'large' ? '+' : 'A') && 
                    (saved === 'medium' || btn.textContent.includes(saved === 'small' ? '-' : '+'))) {
                    btn.classList.add('active');
                }
            });
        }
    }

     // === ИНИЦИАЛИЗАЦИЯ ===

    loadTheme();
    loadFontSize();

    window.toggleTheme = toggleTheme;
    window.setFontSize = setFontSize;
    window.navigateToChapter = navigateToChapter; 

    await loadChapter();

    window.addEventListener('beforeunload', () => {
        saveProgress();
    });
});