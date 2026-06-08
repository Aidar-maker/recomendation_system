document.addEventListener('DOMContentLoaded', async () => {
    // Проверка авторизации
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    // Проверка прав админа
    try {
        const user = await userAPI.getMe();
        
        if (user.role !== 'admin') {
            showToast('Доступ запрещён: требуются права администратора', 'error');
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1500);
            return;
        }
        
        localStorage.setItem('userRole', user.role);
        
    } catch (e) {
        console.error('Ошибка проверки прав:', e);
        window.location.href = 'dashboard.html';
        return;
    }

    // Элементы DOM
    const createBookForm = document.getElementById('createBookForm');
    const addChapterForm = document.getElementById('addChapterForm');
    const selectBook = document.getElementById('selectBook');
    const booksListContainer = document.getElementById('booksListContainer');
    const logoutBtn = document.getElementById('logout-btn');

    // Элементы для обложки
    const coverTypeUrl = document.getElementById('coverTypeUrl');
    const coverTypeFile = document.getElementById('coverTypeFile');
    const coverUrlGroup = document.getElementById('coverUrlGroup');
    const coverFileGroup = document.getElementById('coverFileGroup');
    const bookImageUrl = document.getElementById('bookImageUrl');
    const bookImageFile = document.getElementById('bookImageFile');
    const coverPreview = document.getElementById('coverPreview');
    const coverPreviewImg = document.getElementById('coverPreviewImg');
    const clearCoverBtn = document.getElementById('clearCoverBtn');
    
    let uploadedCoverUrl = null; // URL загруженного файла
    let allBooks = [];
    let allGenres = [];


    // === ЗАГРУЗКА ЖАНРОВ ===
    async function loadGenres() {
        try {
            const response = await apiRequest('/genres');
            allGenres = response;
            
            const genresContainer = document.getElementById('genresContainer');
            if (genresContainer) {
                genresContainer.innerHTML = allGenres.map(genre => `
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
            }
        } catch (e) {
            console.error('Ошибка загрузки жанров:', e);
        }
    }

    // Переключение между URL и файлом
    if (coverTypeUrl && coverTypeFile) {
        coverTypeUrl.addEventListener('change', () => {
            if (coverTypeUrl.checked) {
                coverUrlGroup.style.display = 'block';
                coverFileGroup.style.display = 'none';
                bookImageFile.value = ''; // Очищаем файл
            }
        });
        
        coverTypeFile.addEventListener('change', () => {
            if (coverTypeFile.checked) {
                coverUrlGroup.style.display = 'none';
                coverFileGroup.style.display = 'block';
                bookImageUrl.value = ''; // Очищаем URL
            }
        });
    }

    // Превью при выборе файла
    if (bookImageFile) {
        bookImageFile.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                // Проверяем размер
                if (file.size > 5 * 1024 * 1024) {
                    showToast('Файл слишком большой (макс 5 МБ)', 'error');
                    bookImageFile.value = '';
                    return;
                }
                
                // Показываем превью
                const reader = new FileReader();
                reader.onload = (e) => {
                    coverPreviewImg.src = e.target.result;
                    coverPreview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Превью при вводе URL
    if (bookImageUrl) {
        bookImageUrl.addEventListener('input', (e) => {
            const url = e.target.value.trim();
            if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
                coverPreviewImg.src = url;
                coverPreviewImg.onerror = () => {
                    coverPreview.style.display = 'none';
                };
                coverPreviewImg.onload = () => {
                    coverPreview.style.display = 'block';
                };
            } else {
                coverPreview.style.display = 'none';
            }
        });
    }

    // Кнопка "Убрать обложку"
    if (clearCoverBtn) {
        clearCoverBtn.addEventListener('click', () => {
            bookImageUrl.value = '';
            bookImageFile.value = '';
            coverPreview.style.display = 'none';
            coverPreviewImg.src = '';
            uploadedCoverUrl = null;
        });
    }

    // === ЗАГРУЗКА СПИСКА КНИГ ===
    async function loadBooksList() {
        try {
            const response = await apiRequest('/books');
            allBooks = response.books;
            
            // Заполняем select для добавления глав
            selectBook.innerHTML = '<option value="">Выберите книгу...</option>';
            allBooks.forEach(book => {
                const option = document.createElement('option');
                option.value = book.book_id;
                option.textContent = `${book.title} (${book.author})`;
                selectBook.appendChild(option);
            });

            // Отображаем список книг
            renderBooksList();
            
        } catch (e) {
            console.error('Ошибка загрузки книг:', e);
            booksListContainer.innerHTML = `
                <div class="alert alert-danger">❌ Ошибка: ${e.message}</div>
            `;
        }
    }

    // Отображение списка книг с кнопками удаления
    function renderBooksList() {
        if (allBooks.length === 0) {
            booksListContainer.innerHTML = `
                <div class="text-center text-muted py-5">
                    📚 Книг пока нет. Создайте первую!
                </div>
            `;
            return;
        }

        booksListContainer.innerHTML = allBooks.map(book => `
            <div class="book-list-item" data-book-id="${book.book_id}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h5 class="mb-1">${escapeHtml(book.title)}</h5>
                        <p class="text-muted mb-1">${escapeHtml(book.author)}</p>
                        <small class="text-muted">
                            📑 ${book.chapters ? book.chapters.length : 0} глав
                            ${book.year_publication ? `• ${book.year_publication}` : ''}
                        </small>
                    </div>
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-outline-primary" onclick="window.open('book_detail.html?book=${book.book_id}', '_blank')">
                            👁 Просмотр
                        </button>
                        <button class="btn btn-sm btn-outline-danger btn-delete-book" data-book-id="${book.book_id}">
                            🗑 Удалить
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        // Добавляем обработчики на кнопки удаления
        document.querySelectorAll('.btn-delete-book').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const bookId = parseInt(btn.dataset.bookId);
                await deleteBook(bookId);
            });
        });
    }

    // Удаление книги
    async function deleteBook(bookId) {
        const book = allBooks.find(b => b.book_id === bookId);
        if (!book) return;

        if (!confirm(`❗ Вы уверены, что хотите удалить книгу "${book.title}"?\n\nВсе главы будут удалены безвозвратно!`)) {
            return;
        }

        try {
            await apiRequest(`/admin/books/${bookId}`, {
                method: 'DELETE'
            });

            showToast(`Книга "${book.title}" удалена`, 'success');
            await loadBooksList(); // Перезагружаем список
            
        } catch (e) {
            showToast(`Ошибка удаления`, 'error');
        }
    }

    // Удаление главы
    async function deleteChapter(bookId, chapterId, chapterTitle) {
        if (!confirm(`❗ Вы уверены, что хотите удалить главу "${chapterTitle}"?`)) {
            return;
        }

        try {
            await apiRequest(`/admin/books/${bookId}/chapters/${chapterId}`, {
                method: 'DELETE'
            });

            showToast(`Глава "${chapterTitle}" удалена`, 'success');
            await loadBooksList(); // Перезагружаем список
            
        } catch (e) {
            showToast(`Ошибка удаления: ${e.message}`, 'error');
        }
    }

    // === МОДЕРАЦИЯ ЗАПРОСОВ ===
    async function loadModerationRequests(status = '') {
        const container = document.getElementById('moderationContainer');
        if (!container) return;

        try {
            const params = status ? `?status=${status}` : '';
            const requests = await apiRequest(`/admin/moderation/requests${params}`);

            if (requests.length === 0) {
                container.innerHTML = '<p class="text-muted text-center">Нет запросов</p>';
                return;
            }

            const statusColors = {
                'pending': 'warning',
                'approved': 'success',
                'rejected': 'danger'
            };

            container.innerHTML = requests.map(req => `
                <div class="border-bottom pb-3 mb-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h5>${req.title}</h5>
                            <p class="text-muted small">От: ${req.username} (${req.email})</p>
                            <p>${req.description}</p>
                            <span class="badge bg-${statusColors[req.status]}">${req.status}</span>
                            ${req.admin_note ? `<p class="small mt-2"><b>Комментарий:</b> ${req.admin_note}</p>` : ''}
                        </div>
                        ${req.status === 'pending' ? `
                            <div class="d-flex gap-2">
                                <button class="btn btn-sm btn-success" onclick="approveRequest(${req.request_id})">✅ Одобрить</button>
                                <button class="btn btn-sm btn-danger" onclick="rejectRequest(${req.request_id})">❌ Отклонить</button>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `).join('');

        } catch (e) {
            console.error('Ошибка загрузки модерации:', e);
            container.innerHTML = '<p class="text-danger">Ошибка загрузки</p>';
        }
    }

    // Одобрить запрос
    window.approveRequest = async (requestId) => {
        const note = prompt('Комментарий (необязательно):');
        try {
            await apiRequest(`/admin/moderation/${requestId}/decision`, {
                method: 'PUT',
                body: { status: 'approved', admin_note: note || null }
            });
            showToast('Запрос одобрен!', 'success');
            await loadModerationRequests();
        } catch (e) {
            showToast(`Ошибка: ${e.message}`, 'error');
        }
    };

    // Отклонить запрос
    window.rejectRequest = async (requestId) => {
        const note = prompt('Причина отклонения:');
        if (!note) return;
        try {
            await apiRequest(`/admin/moderation/${requestId}/decision`, {
                method: 'PUT',
                body: { status: 'rejected', admin_note: note }
            });
            showToast('Запрос отклонён', 'success');
            await loadModerationRequests();
        } catch (e) {
            showToast(`Ошибка: ${e.message}`, 'error');
        }
    };

    // Фильтр модерации
    const moderationFilter = document.getElementById('moderationFilter');
    if (moderationFilter) {
        moderationFilter.addEventListener('change', (e) => {
            loadModerationRequests(e.target.value);
        });
    }

    // === СОЗДАНИЕ КНИГИ ===
    if (createBookForm) {
        createBookForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Собираем выбранные жанры
            const selectedGenres = [];
            document.querySelectorAll('.genre-checkbox:checked').forEach(checkbox => {
                selectedGenres.push(parseInt(checkbox.value));
            });

            // Определяем способ загрузки обложки
            let imageUrl = null;
            const useFile = coverTypeFile && coverTypeFile.checked;
            
            if (useFile && bookImageFile && bookImageFile.files[0]) {
                // Загружаем файл
                const submitBtn = createBookForm.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Загрузка обложки...';
                
                try {
                    const formData = new FormData();
                    formData.append('file', bookImageFile.files[0]);
                    
                    const uploadResponse = await fetch(`${API_URL}/admin/upload-cover`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                        },
                        body: formData
                    });
                    
                    if (!uploadResponse.ok) {
                        const errorData = await uploadResponse.json();
                        throw new Error(errorData.detail || 'Ошибка загрузки файла');
                    }
                    
                    const uploadResult = await uploadResponse.json();
                    imageUrl = uploadResult.url;
                    
                    showToast('Обложка загружена!', 'success');
                    
                } catch (error) {
                    showToast(`Ошибка загрузки обложки: ${error.message}`, 'error');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '✨ Создать книгу';
                    return;
                }
            } else if (bookImageUrl && bookImageUrl.value.trim()) {
                // Используем URL
                imageUrl = bookImageUrl.value.trim();
            }

            const bookData = {
                title: document.getElementById('bookTitle').value,
                author: document.getElementById('bookAuthor').value,
                year_publication: parseInt(document.getElementById('bookYear').value) || null,
                publisher: document.getElementById('bookPublisher').value || null,
                image_url: imageUrl,
                description: document.getElementById('bookDescription').value || null,
                genre_ids: selectedGenres
            };

            const submitBtn = createBookForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Создание...';

            try {
                const result = await apiRequest('/admin/books', {
                    method: 'POST',
                    body: bookData
                });

                showToast(`Книга "${bookData.title}" успешно создана!`, 'success');
                
                createBookForm.reset();
                coverPreview.style.display = 'none';
                uploadedCoverUrl = null;
                
                await loadBooksList();
                
                const addChapterTab = document.getElementById('add-chapter-tab');
                const tab = new bootstrap.Tab(addChapterTab);
                tab.show();
                selectBook.value = result.book_id;
                
            } catch (error) {
                showToast(`Ошибка создания книги: ${error.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '✨ Создать книгу';
            }
        });
    }

    // === ДОБАВЛЕНИЕ ГЛАВЫ ===
    if (addChapterForm) {
        addChapterForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const bookId = parseInt(selectBook.value);
            if (!bookId) {
                showToast('Выберите книгу', 'error');
                return;
            }

            const chapterData = {
                title: document.getElementById('chapterTitle').value,
                content_html: document.getElementById('chapterContent').value,
                order_number: parseInt(document.getElementById('chapterOrder').value)
            };

            const submitBtn = addChapterForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Добавление...';

            try {
                await apiRequest(`/admin/books/${bookId}/chapters`, {
                    method: 'POST',
                    body: chapterData
                });

                showToast(`Глава "${chapterData.title}" добавлена!`, 'success');
                
                document.getElementById('chapterTitle').value = '';
                document.getElementById('chapterContent').value = '';
                document.getElementById('chapterOrder').value = parseInt(document.getElementById('chapterOrder').value) + 1;
                
                await loadBooksList();
                
            } catch (error) {
                showToast(`Ошибка добавления главы: ${error.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '💾 Добавить главу';
            }
        });
    }

    // === ВЫХОД ===
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

    // === ПРЕДПРОСМОТР HTML ===
    const previewBtn = document.getElementById('previewBtn');
    if (previewBtn) {
        previewBtn.addEventListener('click', () => {
            const chapterTitle = document.getElementById('chapterTitle').value;
            const chapterContent = document.getElementById('chapterContent').value;

            if (!chapterTitle || !chapterContent) {
                showToast('Заполните название и содержание главы', 'error');
                return;
            }

            // Заполняем модальное окно
            document.getElementById('previewTitle').textContent = chapterTitle;
            document.getElementById('previewContent').innerHTML = chapterContent;

            // Открываем модальное окно
            const previewModal = new bootstrap.Modal(document.getElementById('previewModal'));
            previewModal.show();
        });
    }

    // === ЭКСПОРТ БИБЛИОТЕКИ В CSV ===
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', async () => {
            try {
                const token = localStorage.getItem('accessToken');
                
                const response = await fetch(`${API_URL}/library/export`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.status === 403) {
                    showToast('Доступ запрещен: только для администраторов', 'error');
                    return;
                }

                if (!response.ok) {
                    throw new Error('Ошибка сервера при экспорте');
                }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `library_${new Date().toISOString().slice(0,10)}.csv`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);

                showToast('Библиотека экспортирована!', 'success');
                
            } catch (e) {
                console.error('Ошибка экспорта:', e);
                showToast(`Ошибка экспорта: ${e.message}`, 'error');
            }
        });
    }

    // === МОДЕРАЦИЯ ЗАЯВОК ПОЛЬЗОВАТЕЛЕЙ ===
    let currentSubmissionType = 'books';

    // Функция загрузки заявок
    async function loadUserSubmissions(type = 'books') {
        currentSubmissionType = type;
        const container = document.getElementById('userSubmissionsContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status"></div>
            </div>
        `;

        try {
            const endpoint = type === 'books' ? '/admin/submissions/books' : '/admin/submissions/chapters';
            const submissions = await apiRequest(endpoint);

            if (submissions.length === 0) {
                container.innerHTML = '<p class="text-muted text-center">Нет заявок</p>';
                return;
            }

            const statusColors = {
                'pending': 'warning',
                'approved': 'success',
                'rejected': 'danger'
            };

            const statusTexts = {
                'pending': ' На рассмотрении',
                'approved': '✅ Одобрено',
                'rejected': ' Отклонено'
            };

            let html = '';

            if (type === 'books') {
                html = submissions.map(sub => `
                    <div class="border rounded p-3 mb-3 bg-white shadow-sm">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h5 class="mb-0">${sub.title} <small class="text-muted">(${sub.author})</small></h5>
                            <span class="badge bg-${statusColors[sub.status]}">${statusTexts[sub.status]}</span>
                        </div>
                        <p class="text-muted small mb-1">От: ${sub.username} (${sub.email}) • ${new Date(sub.created_at).toLocaleDateString('ru-RU')}</p>
                        <p class="mb-1"><b>Год:</b> ${sub.year_publication || '—'} | <b>Издательство:</b> ${sub.publisher || '—'}</p>
                        <p class="mb-2"><b>Описание:</b> ${sub.description || 'Нет описания'}</p>
                        ${sub.genre_ids && sub.genre_ids.length > 0 ? `<p class="mb-2"><b>Жанры:</b> ${sub.genre_ids.map(id => `<span class="badge bg-secondary">ID ${id}</span>`).join(' ')}</p>` : ''}
                        
                        ${sub.admin_note ? `<div class="alert alert-light border mb-2"><small><b>Комментарий админа:</b> ${sub.admin_note}</small></div>` : ''}

                        ${sub.status === 'pending' ? `
                            <div class="d-flex gap-2 mt-2">
                                <button class="btn btn-sm btn-success" onclick="approveBookSubmission(${sub.submission_id})">✅ Одобрить и создать книгу</button>
                                <button class="btn btn-sm btn-outline-danger" onclick="rejectBookSubmission(${sub.submission_id})">❌ Отклонить</button>
                            </div>
                        ` : ''}
                    </div>
                `).join('');
            } else {
                html = submissions.map(sub => `
                    <div class="border rounded p-3 mb-3 bg-white shadow-sm">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h5 class="mb-0">${sub.chapter_title} <small class="text-muted">(для книги "${sub.book_title}")</small></h5>
                            <span class="badge bg-${statusColors[sub.status]}">${statusTexts[sub.status]}</span>
                        </div>
                        <p class="text-muted small mb-1">От: ${sub.username} (${sub.email}) • Порядок: ${sub.order_number} • ${new Date(sub.created_at).toLocaleDateString('ru-RU')}</p>
                        
                        <div class="bg-light p-2 rounded mb-2" style="max-height: 150px; overflow-y: auto;">
                            <small><b>Предпросмотр контента (HTML):</b></small>
                            <hr class="my-1">
                            ${sub.chapter_content.substring(0, 500)}${sub.chapter_content.length > 500 ? '...' : ''}
                        </div>

                        ${sub.admin_note ? `<div class="alert alert-light border mb-2"><small><b>Комментарий админа:</b> ${sub.admin_note}</small></div>` : ''}

                        ${sub.status === 'pending' ? `
                            <div class="d-flex gap-2 mt-2">
                                <button class="btn btn-sm btn-success" onclick="approveChapterSubmission(${sub.submission_id})">✅ Одобрить и добавить главу</button>
                                <button class="btn btn-sm btn-outline-danger" onclick="rejectChapterSubmission(${sub.submission_id})">❌ Отклонить</button>
                            </div>
                        ` : ''}
                    </div>
                `).join('');
            }

            container.innerHTML = html;

        } catch (e) {
            console.error('Ошибка загрузки заявок:', e);
            container.innerHTML = '<p class="text-danger">Ошибка загрузки</p>';
        }
    }

    // === ДЕЙСТВИЯ АДМИНА ===

    // Одобрить книгу
    window.approveBookSubmission = async (id) => {
        const note = prompt('Комментарий (необязательно):');
        try {
            await apiRequest(`/admin/submissions/books/${id}/decision`, {
                method: 'PUT',
                body: { status: 'approved', admin_note: note || null }
            });
            showToast('Книга создана и заявка одобрена!', 'success');
            loadUserSubmissions(currentSubmissionType);
        } catch (e) {
            showToast(`Ошибка: ${e.message}`, 'error');
        }
    };

    // Отклонить книгу
    window.rejectBookSubmission = async (id) => {
        const note = prompt('Причина отклонения (обязательно):');
        if (!note) return;
        try {
            await apiRequest(`/admin/submissions/books/${id}/decision`, {
                method: 'PUT',
                body: { status: 'rejected', admin_note: note }
            });
            showToast('Заявка отклонена', 'success');
            loadUserSubmissions(currentSubmissionType);
        } catch (e) {
            showToast(`Ошибка: ${e.message}`, 'error');
        }
    };

    // Одобрить главу
    window.approveChapterSubmission = async (id) => {
        const note = prompt('Комментарий (необязательно):');
        try {
            await apiRequest(`/admin/submissions/chapters/${id}/decision`, {
                method: 'PUT',
                body: { status: 'approved', admin_note: note || null }
            });
            showToast('Глава добавлена и заявка одобрена!', 'success');
            loadUserSubmissions(currentSubmissionType);
        } catch (e) {
            showToast(`Ошибка: ${e.message}`, 'error');
        }
    };

    // Отклонить главу
    window.rejectChapterSubmission = async (id) => {
        const note = prompt('Причина отклонения (обязательно):');
        if (!note) return;
        try {
            await apiRequest(`/admin/submissions/chapters/${id}/decision`, {
                method: 'PUT',
                body: { status: 'rejected', admin_note: note }
            });
            showToast('Заявка отклонена', 'success');
            loadUserSubmissions(currentSubmissionType);
        } catch (e) {
            showToast(`Ошибка: ${e.message}`, 'error');
        }
    };

    // Обработчики вкладок "Книги" / "Главы" в заявках пользователей
    document.querySelectorAll('[data-submission-type]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('[data-submission-type]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadUserSubmissions(btn.dataset.submissionType);
        });
    });

    // Загрузка заявок при переключении на вкладку "Заявки пользователей"
    const userSubmissionsTab = document.getElementById('user-submissions-tab');
    if (userSubmissionsTab) {
        userSubmissionsTab.addEventListener('shown.bs.tab', () => {
            loadUserSubmissions('books');
        });
    }

    // Загружаем модерацию при переключении на вкладку
    const moderationTab = document.getElementById('moderation-tab');
    if (moderationTab) {
        moderationTab.addEventListener('shown.bs.tab', () => {
            loadModerationRequests();
        });
    }

    // === ИНИЦИАЛИЗАЦИЯ ===
    await Promise.all([
        loadGenres(),
        loadBooksList()
    ]);
});