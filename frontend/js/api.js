// frontend/js/api.js

// Базовый адрес API
const API_URL = 'http://127.0.0.1:8000/api/v1';

/**
 * Универсальная функция для запросов к API.
 * Автоматически добавляет заголовок Authorization, если токен есть.
 */
async function apiRequest(endpoint, options = {}) {
    // 1. Получаем токен из localStorage
    const token = localStorage.getItem('accessToken');

    // 2. Формируем заголовки
    const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
    };

    // 3. Собираем параметры запроса
    const config = {
        method: options.method || 'GET',
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined
    };

    try {
        // 4. Делаем запрос
        const response = await fetch(`${API_URL}${endpoint}`, config);

        // 5. Если ошибка 401 (Unauthorized) — значит токен протух
        if (response.status === 401) {
            // Не редиректим, если уже на странице входа
            if (!window.location.pathname.includes('index.html')) {
                localStorage.removeItem('accessToken');
                localStorage.removeItem('userEmail');
                window.location.href = 'index.html';
                return null;
            }
            // Если мы на index.html — просто выбрасываем ошибку
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Неверный email или пароль');
        }

        // 6. Если ошибка сервера (не 2xx)
        if (!response.ok) {
            // Пробуем получить текст ошибки
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            try {
                const errorData = await response.clone().json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                // Если не JSON — оставляем текстовую ошибку
            }
            throw new Error(errorMessage);
        }

        // 7. Проверяем, есть ли контент в ответе
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else {
            return null; // Или пустой объект, если нужно
        }

    } catch (error) {
        console.error('API Error:', error);
        // Не показываем alert для каждой ошибки (раздражает)
        // alert(`Ошибка: ${error.message}`);
        throw error;
    }
}

// Конкретные методы

// Авторизация
const authAPI = {
    login: (email, password) => apiRequest('/auth/login', {
        method: 'POST',
        body: { email, password }
    }),
    register: (username, email, password) => apiRequest('/auth/register', {
        method: 'POST',
        body: { username, email, password }
    })
};

// Рекомендации
const recommendAPI = {
    getRecommendations: (limit = 5) => apiRequest('/recommend', {
        method: 'POST',
        body: { limit }
    }),
    getGenres: () => apiRequest('/genres'),
    getRecommendationsByGenres: (genres, limit = 5) => apiRequest('/recommend/genres', {
        method: 'POST',
        body: { genres, limit }
    }),
    getSimilarBooks: (bookId, limit = 5) => apiRequest('/similar', {
        method: 'POST',
        body: { book_id: bookId, limit }
    })
};

// Избранное и Статусы
const booksAPI = {
    getFavorites: (sort = 'date', order = 'desc') => apiRequest(`/favorites?sort=${sort}&order=${order}`),
    addFavorite: (bookId) => apiRequest(`/favorites/${bookId}`, { method: 'POST' }),
    removeFavorite: (bookId) => apiRequest(`/favorites/${bookId}`, { method: 'DELETE' }),

    getStatuses: (status = null, sort = 'date', order = 'desc') => {
        let url = `/reading-statuses?sort=${sort}&order=${order}`;
        if (status) url += `&status=${status}`;
        return apiRequest(url);
    },
    setStatus: (bookId, statusValue) => apiRequest(`/reading-statuses/${bookId}`, {
        method: 'POST',
        body: { status: statusValue }
    }),
    removeStatus: (bookId) => apiRequest(`/reading-statuses/${bookId}`, { method: 'DELETE' })
};

// Оценки
const ratingsAPI = {
    getMyRatings: (sort = 'date', order = 'desc') => apiRequest(`/my-ratings?sort=${sort}&order=${order}`),
    setRating: (bookId, rating) => apiRequest('/ratings', {
        method: 'POST',
        body: { book_id: bookId, rating }
    }),
    deleteRating: (bookId) => apiRequest(`/ratings/${bookId}`, { method: 'DELETE' })
};

const statsAPI = {
    getReadingStats: () => apiRequest('/stats/reading')
};