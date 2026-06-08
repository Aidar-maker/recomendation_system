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
            currentBook = await apiRequest(`/books/${bookId}`);
            bookTitleEl.textContent = currentBook.title;

            currentChapter = await apiRequest(`/books/${bookId}/chapters/${chapterId}`);
            
            chapterTitleEl.textContent = currentChapter.title;
            chapterContentEl.innerHTML = currentChapter.content_html;

            // Обновляем кнопки навигации с учётом всех глав
            updateNavButtons(currentChapter.all_chapters || []);

            await loadProgress();
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
        // Ищем или создаём контейнер для селектора
        let selectorContainer = document.querySelector('.chapter-selector');
        if (!selectorContainer) {
            selectorContainer = document.createElement('div');
            selectorContainer.className = 'chapter-selector';
            selectorContainer.style.cssText = `
                position: fixed;
                top: 70px;
                right: 20px;
                z-index: 100;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                padding: 10px;
                max-width: 300px;
            `;
            
            // Вставляем после header
            const header = document.querySelector('.reader-header');
            if (header) {
                header.parentNode.insertBefore(selectorContainer, header.nextSibling);
            }
        }

        const options = allChapters.map((chapter, index) => {
            const isSelected = index === currentIndex;
            return `<option value="${chapter.chapter_id}" ${isSelected ? 'selected' : ''}>
                ${chapter.display_name}: ${chapter.title}
            </option>`;
        }).join('');

        selectorContainer.innerHTML = `
            <label class="form-label mb-1"><b>Выбрать главу:</b></label>
            <select class="form-select form-select-sm" onchange="navigateToChapter(parseInt(this.value))">
                ${options}
            </select>
        `;
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
        cycleTheme();
    }

    function loadTheme() {
        // Тема загружается автоматически через theme.js
        // Здесь можно добавить специфичные для читалки настройки
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