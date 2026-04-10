<?php
// Подключаем автолоадер
require_once __DIR__ . '/../vendor/autoload.php';

use App\Database;
use App\RecommendationClient;

// Стартуем сессию (для авторизации)
session_start();

// Получаем подключения
$db = Database::getInstance()->getConnection();
$mlClient = new RecommendationClient();

// Получаем ID текущего пользователя (если авторизован)
$userId = $_SESSION['user_id'] ?? null;
$recommendations = [];

// Если пользователь авторизован - получаем рекомендации
if ($userId) {
    $recommendations = $mlClient->getRecommendations($userId, 5);
}
?>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Книжный Советник</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; }
        .book-card { 
            background: white; 
            border: 1px solid #ddd; 
            border-radius: 8px; 
            padding: 15px; 
            margin: 10px; 
            display: inline-block;
            width: 250px;
            vertical-align: top;
        }
        .book-card h3 { margin: 0 0 10px 0; color: #2c3e50; }
        .book-card p { margin: 5px 0; color: #7f8c8d; }
        .rating { color: #f39c12; font-weight: bold; }
        .login-link { background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
        .recommendations { background: white; padding: 20px; border-radius: 8px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Книжный Советник</h1>
        
        <?php if ($userId): ?>
            <p>Привет! Вот рекомендации для вас:</p>
            
            <div class="recommendations">
                <h2>📖 Рекомендации для вас</h2>
                <?php if (!empty($recommendations)): ?>
                    <?php foreach ($recommendations as $book): ?>
                        <div class="book-card">
                            <h3><?= htmlspecialchars($book['title']) ?></h3>
                            <p>Автор: <?= htmlspecialchars($book['author']) ?></p>
                            <p class="rating">⭐ <?= $book['predicted_rating'] ?>/5</p>
                        </div>
                    <?php endforeach; ?>
                <?php else: ?>
                    <p>Пока нет рекомендаций. Оцените несколько книг!</p>
                <?php endif; ?>
            </div>
        <?php else: ?>
            <p><a href="/login.php" class="login-link">Войти</a> для получения персональных рекомендаций</p>
        <?php endif; ?>
    </div>
</body>
</html>