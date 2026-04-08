<?php
require_once __DIR__ . '/../vendor/autoload.php';

use App\Database;
use App\RecommendationClient;

session_start();

$db = Database::getInstance()->getConnection();
$mlClient = new RecommendationClient();

// Пример для авторизованного пользователя
$userId = $_SESSION['user_id'] ?? null;
$recommendations = [];

if ($userId) {
    $recommendations = $mlClient->getRecommendations($userId, 5);
}
?>

<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Книжный Советник</title>
    <style>
        .book-card { border: 1px solid #ddd; padding: 15px; margin: 10px; }
        .recommendations { background: #f9f9f9; padding: 20px; }
    </style>
</head>
<body>
    <h1>Добро пожаловать в Книжный Советник</h1>
    
    <?php if ($userId): ?>
        <div class="recommendations">
            <h2> Рекомендации для вас</h2>
            <?php if (!empty($recommendations)): ?>
                <div style="display: flex; flex-wrap: wrap;">
                <?php foreach ($recommendations as $book): ?>
                    <div class="book-card">
                        <h3><?= htmlspecialchars($book['title']) ?></h3>
                        <p>Автор: <?= htmlspecialchars($book['author']) ?></p>
                        <p>Прогноз рейтинга: ⭐ <?= $book['predicted_rating'] ?></p>
                    </div>
                <?php endforeach; ?>
                </div>
            <?php else: ?>
                <p>Пока нет рекомендаций. Оцените несколько книг!</p>
            <?php endif; ?>
        </div>
    <?php else: ?>
        <p><a href="/login.php">Войдите</a> для получения персональных рекомендаций</p>
    <?php endif; ?>
</body>
</html>