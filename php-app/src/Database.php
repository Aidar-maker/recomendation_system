<?php
namespace App;

use PDO;
use PDOException;

/**
 * Класс для подключения к базе данных (Singleton)
 */
class Database {
    private static $instance = null;
    private $pdo;
    
    private function __construct() {
        // Получаем настройки из переменных окружения (из docker-compose.yml)
        $host = getenv('DB_HOST') ?: 'db';
        $db = getenv('DB_NAME') ?: 'book_recommender';
        $user = getenv('DB_USER') ?: 'bookuser';
        $pass = getenv('DB_PASS') ?: 'bookpassword';
        
        // DSN (Data Source Name) - строка подключения
        $dsn = "mysql:host=$host;dbname=$db;charset=utf8mb4";
        
        // Настройки PDO
        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,  // Выбрасывать исключения при ошибках
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,  // Возвращать ассоциативные массивы
            PDO::ATTR_EMULATE_PREPARES => false,  // Использовать подготовленные выражения
        ];
        
        try {
            $this->pdo = new PDO($dsn, $user, $pass, $options);
        } catch (PDOException $e) {
            throw new PDOException("Connection failed: " . $e->getMessage());
        }
    }
    
    // Singleton: возвращаем один и тот же экземпляр
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    // Возвращаем PDO объект для выполнения запросов
    public function getConnection() {
        return $this->pdo;
    }
}