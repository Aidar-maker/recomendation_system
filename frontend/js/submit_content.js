document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    let allBooks = [];
    let allGenres = [];
    let currentSubmissionsTab = 'books';

    // === ЗАГРУЗКА ЖАНРОВ ===
    async function loadGenres() {
        try {
            allGenres = await apiRequest('/genres');
            const container = document.getElementById('bookGenresContainer');
            
            if (container) {
                container.innerHTML = allGenres.map(genre => `
                    <label class="genre-checkbox">
                        <input type="checkbox" class="genre-checkbox-input" 
                               value="${genre.genre_id}" id="genre_${genre.genre_id}">
                        <span>${genre.genre_name}</span>
                    </label>
                `).join('');
            }
        } catch (e) {
            console.error('Ошибка загрузки жанров:', e);
        }
    }

    // === ЗАГРУЗКА КНИГ ===
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
            
            if (!select) return;
            
            if (allBooks.length === 0) {
                select.innerHTML = '<option value="">У вас нет книг</option>';
                return;
            }
            
            select.innerHTML = '<option value="">Выберите книгу...</option>' +
                allBooks.map(book => `
                    <option value="${book.book_id}">${escapeHtml(book.title)} (${escapeHtml(book.author)})</option>
                `).join('');
                
            select.addEventListener('change', async () => {
                const bookId = parseInt(select.value);
                await loadExistingChapters(bookId);
            });
            
        } catch (e) {
            console.error('Ошибка загрузки книг:', e);
            showToast('Ошибка загрузки списка книг', 'error');
        }
    }

    // === ЗАГРУЗКА СУЩЕСТВУЮЩИХ ГЛАВ ===
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
                chaptersList.innerHTML = '<div class="empty-chapters">В книге пока нет глав</div>';
                chaptersBlock.style.display = 'block';
                return;
            }
            
            chapters.sort((a, b) => parseFloat(a.order_number) - parseFloat(b.order_number));
            
            let html = '<ul class="chapters-list">';
            chapters.forEach(chapter => {
                const orderNum = parseFloat(chapter.order_number);
                const displayNum = orderNum == Math.floor(orderNum) ? Math.floor(orderNum) + 1 : orderNum;
                
                html += `
                    <li class="chapter-item">
                        <span class="chapter-item-name"><b>Глава ${displayNum}:</b> ${escapeHtml(chapter.title)}</span>
                        <span class="chapter-item-number">№ ${chapter.order_number}</span>
                    </li>
                `;
            });
            html += '</ul>';
            
            const maxOrder = Math.max(...chapters.map(c => parseFloat(c.order_number)));
            const nextOrder = maxOrder + 1;
            
            html += `
                <div class="recommendation-box">
                    Рекомендуемый номер для новой главы: <code>${nextOrder}</code>
                </div>
            `;
            
            chaptersList.innerHTML = html;
            chaptersBlock.style.display = 'block';
            
        } catch (e) {
            console.error('Ошибка загрузки глав:', e);
            chaptersList.innerHTML = '<div class="empty-chapters" style="color: var(--danger);">Ошибка загрузки глав</div>';
            chaptersBlock.style.display = 'block';
        }
    }

    // === ЗАГРУЗКА МОИХ ЗАЯВОК ===
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
            container.innerHTML = '<div class="empty-state">Ошибка загрузки</div>';
        }
    }

    function renderSubmissions(container, submissions, type) {
        if (submissions.length === 0) {
            container.innerHTML = '<div class="empty-state">У вас пока нет заявок</div>';
            return;
        }

        function getStatusText(status) {
            const map = {
                'pending': 'На рассмотрении',
                'approved': 'Одобрено',
                'rejected': 'Отклонено'
            };
            return map[status] || status;
        }

        container.innerHTML = submissions.map(sub => {
            const title = type === 'book' 
                ? escapeHtml(sub.title) 
                : `${escapeHtml(sub.book_title)} — ${escapeHtml(sub.chapter_title)}`;
            
            return `
                <div class="submission-item">
                    <h6 class="submission-title">${title}</h6>
                    <span class="status-badge status-${sub.status}">${getStatusText(sub.status)}</span>
                    ${sub.admin_note ? `
                        <div class="submission-note">
                            <b>Комментарий админа:</b> ${escapeHtml(sub.admin_note)}
                        </div>
                    ` : ''}
                    ${sub.created_at ? `
                        <span class="submission-date">
                            ${new Date(sub.created_at).toLocaleDateString('ru-RU')}
                        </span>
                    ` : ''}
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
            document.querySelectorAll('.genre-checkbox-input:checked').forEach(cb => {
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
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Отправка...';

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
                submitBtn.innerHTML = originalText;
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
                order_number: parseFloat(document.getElementById('chapterOrder').value)
            };

            const submitBtn = chapterForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Отправка...';

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
                submitBtn.innerHTML = originalText;
            }
        });
    }

    // === РЕДАКТИРОВАНИЕ ГЛАВЫ ===
    const editChapterForm = document.getElementById('editChapterSubmissionForm');
    const editSelectBook = document.getElementById('editSelectBook');
    const editSelectChapter = document.getElementById('editSelectChapter');
    
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
                    <option value="${book.book_id}">${escapeHtml(book.title)} (${escapeHtml(book.author)})</option>
                `).join('');
                
        } catch (e) {
            console.error('Ошибка загрузки книг:', e);
            editSelectBook.innerHTML = '<option value="">Ошибка загрузки</option>';
        }
    }
    
    loadBooksForEdit();
    
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
                                data-title="${escapeHtml(ch.title)}" 
                                data-order="${ch.order_number}">
                            Глава ${displayNum}: ${escapeHtml(ch.title)}
                        </option>`;
                    }).join('');
                    
            } catch (e) {
                console.error('Ошибка загрузки глав:', e);
            }
        });
    }
    
    if (editSelectChapter) {
        editSelectChapter.addEventListener('change', () => {
            const selectedOption = editSelectChapter.options[editSelectChapter.selectedIndex];
            if (selectedOption.value) {
                document.getElementById('editChapterTitle').value = selectedOption.dataset.title || '';
                document.getElementById('editChapterOrder').value = selectedOption.dataset.order || '';
            }
        });
    }
    
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
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Отправка...';
            
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
                submitBtn.innerHTML = originalText;
            }
        });
    }

    // === ПЕРЕКЛЮЧЕНИЕ МОИХ ЗАЯВОК ===
    document.querySelectorAll('.pill-btn[data-tab]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.pill-btn[data-tab]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentSubmissionsTab = btn.dataset.tab;
            loadMySubmissions();
        });
    });

    // === ВЫХОД ===
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('userEmail');
            window.location.href = 'index.html';
        });
    }

    // === ЭКРАНИРОВАНИЕ HTML ===
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // === ИНИЦИАЛИЗАЦИЯ ===
    await Promise.all([loadGenres(), loadBooks()]);
    loadMySubmissions();
});