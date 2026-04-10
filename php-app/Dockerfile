# Базовый образ PHP с FPM (FastCGI Process Manager)
FROM php:8.1-fpm

# Устанавливаем расширения для работы с MySQL
RUN docker-php-ext-install pdo pdo_mysql

# Рабочая директория внутри контейнера
WORKDIR /var/www/html

# Копируем весь код приложения
COPY . .

# Создаём простой автолоадер классов (вместо Composer для простоты)
RUN mkdir -p vendor/autoload && \
    echo '<?php \
    spl_autoload_register(function ($class) { \
        $prefix = "App\\\\"; \
        $base_dir = __DIR__ . "/../src/"; \
        $len = strlen($prefix); \
        if (strncmp($prefix, $class, $len) !== 0) return; \
        $relative_class = substr($class, $len); \
        $file = $base_dir . str_replace("\\\\", "/", $relative_class) . ".php"; \
        if (file_exists($file)) require $file; \
    });' > vendor/autoload.php

# Открываем порт 80
EXPOSE 80

# Запускаем PHP-FPM
CMD ["php-fpm"]