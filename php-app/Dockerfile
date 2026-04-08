FROM php:8.1-fpm

# Устанавливаем расширения PHP
RUN docker-php-ext-install pdo pdo_mysql

WORKDIR /var/www/html

# Копируем весь код
COPY . .

# Создаем простой автолоадер вручную (вместо Composer)
RUN mkdir -p vendor/autoload && \
    echo '<?php \
    spl_autoload_register(function ($class) { \
        $prefix = "App\\\\"; \
        $base_dir = __DIR__ . "/../src/"; \
        $len = strlen($prefix); \
        if (strncmp($prefix, $class, $len) !== 0) { \
            return; \
        } \
        $relative_class = substr($class, $len); \
        $file = $base_dir . str_replace("\\\\", "/", $relative_class) . ".php"; \
        if (file_exists($file)) { \
            require $file; \
        } \
    });' > vendor/autoload.php

EXPOSE 80

CMD ["php-fpm"]