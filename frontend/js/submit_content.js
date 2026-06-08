document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    let allBooks = [];
    let allGenres = [];
    let currentSubmissionsTab = 'books';

    // === ЗАГРУЗКА ДАННЫХ ===
    async function loadGenres() {
        try {
            allGenres = await apiRequest('/genres');
            const container = document.getElementById('bookGenresContainer');
            
            container.innerHTML = allGenres.map(genre => `
                <div class="col-md-4 col-lg-3">
                    <div class="form-check">
                        <input class="form-check-input genre-checkbox" type="checkbox" 
                               value="${genre.genre_id}" id="genre_${genre.genre_id}">
                        <label class="form-check-label" for="genre_${genre.genre_id}">
                            ${genre.genre_name}
                        </label>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            console.error('Ошибка загрузки жанров:', e);
        }
    }

    async function loadBooks() {
        try {
            const user = await userAPI.getMe();
            
            if (user.role === 'admin') {
                const response = await apiRequest('/books');
                allBooks = response.books;
            } else {
                allBooks = await apiRequest('/my-books');
            }
            
            const select = document.getElementById('selectBook');
            
            if (allBooks.length === 0) {
                select.innerHTML = '<option value="">У вас нет книг</option>';
                return;
            }
            
            select.innerHTML = '<option value="">Выберите книгу...</option>' +
                allBooks.map(book => `
                    <option value="${book.book_id}">${book.title} (${book.author})</option>
                `).join('');
                
            // Добавляем обработчик для показа глав
            select.addEventListener('change', async () => {
                const bookId = parseInt(select.value);
                await loadExistingChapters(bookId);
            });
            
        } catch (e) {
            console.error('Ошибка загрузки книг:', e);
            showToast('Ошибка загрузки списка книг', 'error');
        }
    }

    // Загрузка существующих глав
    async function loadExistingChapters(bookId) {
        const chaptersBlock = document.getElementById('existingChaptersBlock');
        const chaptersList = document.getElementById('existingChaptersList');
        
        if (!bookId) {
            chaptersBlock.style.display = 'none';
            return;
        }
        
        try {
            const book = await apiRequest(`/books/${bookId}`);
            const chapters = book.chapters || [];
            
            if (chapters.length === 0) {
                chaptersList.innerHTML = '<p class="text-muted mb-0">📖 В книге пока нет глав</p>';
                chaptersBlock.style.display = 'block';
                return;
            }
            
            // Сортируем главы по номеру
            chapters.sort((a, b) => parseFloat(a.order_number) - parseFloat(b.order_number));
            
            let html = '<ul class="list-unstyled mb-0">';
            chapters.forEach(chapter => {
                const orderNum = parseFloat(chapter.order_number);
                const displayNum = orderNum == Math.floor(orderNum) ? Math.floor(orderNum) + 1 : orderNum;
                
                html += `
                    <li class="d-flex justify-content-between align-items-center py-2 border-bottom">
                        <span><b>Глава ${displayNum}:</b> ${chapter.title}</span>
                        <span class="badge bg-secondary">№ ${chapter.order_number}</span>
                    </li>
                `;
            });
            html += '</ul>';
            
            // Показываем рекомендуемый номер для новой главы
            const maxOrder = Math.max(...chapters.map(c => parseFloat(c.order_number)));
            const nextOrder = maxOrder + 1;
            
            html += `<div class="mt-2 p-2 bg-white rounded">
                <small>💡 <b>Рекомендуемый номер для новой главы:</b> <code>${nextOrder}</code></small>
            </div>`;
            
            chaptersList.innerHTML = html;
            chaptersBlock.style.display = 'block';
            
        } catch (e) {
            console.error('Ошибка загрузки глав:', e);
            chaptersList.innerHTML = '<p class="text-danger mb-0">Ошибка загрузки глав</p>';
            chaptersBlock.style.display = 'block';
        }
    }

    async function loadMySubmissions() {
        const container = document.getElementById('mySubmissionsContent');
        
        try {
            if (currentSubmissionsTab === 'books') {
                const submissions = await apiRequest('/submissions/my-books');
                renderSubmissions(container, submissions, 'book');
            } else {
                const submissions = await apiRequest('/submissions/my-chapters');
                renderSubmissions(container, submissions, 'chapter');
            }
        } catch (e) {
            container.innerHTML = '<p class="text-danger">Ошибка загрузки</p>';
        }
    }

    function renderSubmissions(container, submissions, type) {
        if (submissions.length === 0) {
            container.innerHTML = '<p class="text-muted">У вас пока нет заявок</p>';
            return;
        }

        const statusConfig = {
            'pending': { color: 'warning', text: '⏳ На рассмотрении' },
            'approved': { color: 'success', text: '✅ Одобрено' },
            'rejected': { color: 'danger', text: '❌ Отклонено' }
        };

        container.innerHTML = submissions.map(sub => {
            const status = statusConfig[sub.status] || statusConfig['pending'];
            const title = type === 'book' ? sub.title : `${sub.book_title} - ${sub.chapter_title}`;
            
            return `
                <div class="border-bottom pb-3 mb-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">${title}</h6>
                            <span class="badge bg-${status.color}">${status.text}</span>
                            ${sub.admin_note ? `
                                <div class="mt-2 p-2 bg-light rounded">
                                    <small><b>Комментарий админа:</b> ${sub.admin_note}</small>
                                </div>
                            ` : ''}
                            <small class="text-muted d-block mt-1">
                                ${new Date(sub.created_at).toLocaleDateString('ru-RU')}
                            </small>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // === ПОДАЧА ЗАЯВКИ НА КНИГУ ===
    const bookForm = document.getElementById('bookSubmissionForm');
    if (bookForm) {
        bookForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const selectedGenres = [];
            document.querySelectorAll('.genre-checkbox:checked').forEach(cb => {
                selectedGenres.push(parseInt(cb.value));
            });

            const submissionData = {
                title: document.getElementById('bookTitle').value,
                author: document.getElementById('bookAuthor').value,
                year_publication: parseInt(document.getElementById('bookYear').value) || null,
                publisher: document.getElementById('bookPublisher').value || null,
                image_url: document.getElementById('bookImageUrl').value || null,
                description: document.getElementById('bookDescription').value || null,
                genre_ids: selectedGenres
            };

            const submitBtn = bookForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Отправка...';

            try {
                await apiRequest('/submissions/books', {
                    method: 'POST',
                    body: submissionData
                });

                showToast('Заявка отправлена на модерацию!', 'success');
                bookForm.reset();
                
            } catch (error) {
                showToast(`Ошибка: ${error.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '📤 Отправить заявку';
            }
        });
    }

    // === ПОДАЧА ЗАЯВКИ НА ГЛАВУ ===
    const chapterForm = document.getElementById('chapterSubmissionForm');
    if (chapterForm) {
        chapterForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const submissionData = {
                book_id: parseInt(document.getElementById('selectBook').value),
                chapter_title: document.getElementById('chapterTitle').value,
                chapter_content: document.getElementById('chapterContent').value,
                order_number: parseInt(document.getElementById('chapterOrder').value)
            };

            const submitBtn = chapterForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Отправка...';

            try {
                await apiRequest('/submissions/chapters', {
                    method: 'POST',
                    body: submissionData
                });

                showToast('Заявка на главу отправлена!', 'success');
                chapterForm.reset();
                
            } catch (error) {
                showToast(`Ошибка: ${error.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '📤 Отправить заявку';
            }
        });
    }


    // === РЕДАКТИРОВАНИЕ ГЛАВЫ ===
    const editChapterForm = document.getElementById('editChapterSubmissionForm');
    const editSelectBook = document.getElementById('editSelectBook');
    const editSelectChapter = document.getElementById('editSelectChapter');
    
    // Загрузка книг для редактирования
    async function loadBooksForEdit() {
        if (!editSelectBook) return;
        
        try {
            const user = await userAPI.getMe();
            let books;
            
            if (user.role === 'admin') {
                const response = await apiRequest('/books');
                books = response.books;
            } else {
                books = await apiRequest('/my-books');
            }
            
            if (books.length === 0) {
                editSelectBook.innerHTML = '<option value="">У вас нет книг</option>';
                return;
            }
            
            editSelectBook.innerHTML = '<option value="">Выберите книгу...</option>' +
                books.map(book => `
                    <option value="${book.book_id}">${book.title} (${book.author})</option>
                `).join('');
                
        } catch (e) {
            console.error('Ошибка загрузки книг:', e);
            editSelectBook.innerHTML = '<option value="">Ошибка загрузки</option>';
        }
    }
    
    // Вызываем загрузку
    loadBooksForEdit();
    
    // Обработчик выбора книги
    if (editSelectBook) {
        editSelectBook.addEventListener('change', async () => {
            const bookId = parseInt(editSelectBook.value);
            if (!bookId) {
                editSelectChapter.innerHTML = '<option value="">Сначала выберите книгу</option>';
                return;
            }
            
            try {
                const book = await apiRequest(`/books/${bookId}`);
                const chapters = book.chapters || [];
                
                if (chapters.length === 0) {
                    editSelectChapter.innerHTML = '<option value="">В этой книге нет глав</option>';
                    return;
                }
                
                editSelectChapter.innerHTML = '<option value="">Выберите главу...</option>' +
                    chapters.map(ch => {
                        const orderNum = parseFloat(ch.order_number);
                        const displayNum = orderNum == Math.floor(orderNum) ? Math.floor(orderNum) + 1 : orderNum;
                        
                        return `<option value="${ch.chapter_id}" 
                                data-title="${ch.title}" 
                                data-order="${ch.order_number}">
                            Глава ${displayNum}: ${ch.title}
                        </option>`;
                    }).join('');
                    
            } catch (e) {
                console.error('Ошибка загрузки глав:', e);
            }
        });
    }
    
    // Автозаполнение полей при выборе главы
    if (editSelectChapter) {
        editSelectChapter.addEventListener('change', () => {
            const selectedOption = editSelectChapter.options[editSelectChapter.selectedIndex];
            if (selectedOption.value) {
                document.getElementById('editChapterTitle').value = selectedOption.dataset.title || '';
                document.getElementById('editChapterOrder').value = selectedOption.dataset.order || '';
            }
        });
    }
    
    // Отправка формы
    if (editChapterForm) {
        editChapterForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submissionData = {
                book_id: parseInt(editSelectBook.value),
                chapter_id: parseInt(editSelectChapter.value),
                chapter_title: document.getElementById('editChapterTitle').value,
                chapter_content: document.getElementById('editChapterContent').value,
                order_number: parseFloat(document.getElementById('editChapterOrder').value),
                is_edit: true
            };
            
            const submitBtn = editChapterForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Отправка...';
            
            try {
                await apiRequest('/submissions/chapters', {
                    method: 'POST',
                    body: submissionData
                });
                
                showToast('Заявка отправлена!', 'success');
                editChapterForm.reset();
                
            } catch (error) {
                showToast(`Ошибка: ${error.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '📤 Отправить заявку на редактирование';
            }
        });
    }

    // === ПЕРЕКЛЮЧЕНИЕ МОИХ ЗАЯВОК ===
    document.querySelectorAll('#mySubmissionsTabs .nav-link').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#mySubmissionsTabs .nav-link').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentSubmissionsTab = btn.dataset.tab;
            loadMySubmissions();
        });
    });

    // === ИНИЦИАЛИЗАЦИЯ ===
    await Promise.all([loadGenres(), loadBooks()]);
    loadMySubmissions();
});