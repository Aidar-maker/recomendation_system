<?php
namespace App;

class Database {
    private static $instance = null;
    private $pdo;
    
    private function __construct() {
        $host = getenv('DB_HOST') ?: 'db';
        $db = getenv('DB_NAME') ?: 'book_recommender';
        $user = getenv('DB_USER') ?: 'bookuser';
        $pass = getenv('DB_PASS') ?: 'bookpassword';
        
        $dsn = "mysql:host=$host;dbname=$db;charset=utf8mb4";
        $options = [
            \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
            \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
        ];
        
        $this->pdo = new \PDO($dsn, $user, $pass, $options);
    }
    
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    public function getConnection() {
        return $this->pdo;
    }
}