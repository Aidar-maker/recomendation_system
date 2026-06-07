document.addEventListener('DOMContentLoaded', async () => {
    // Проверка авторизации
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.href = 'index.html';
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

    // === СОЗДАНИЕ КНИГИ ===
    if (createBookForm) {
        createBookForm.addEventListener('submit', async (e) => {
            e.preventDefault();

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
                description: document.getElementById('bookDescription').value || null
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

    // === ИНИЦИАЛИЗАЦИЯ ===
    await loadBooksList();
});