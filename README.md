#Вход в MySql
docker-compose exec db mysql -uroot -prootpassword book_recommender

#Очистка БД
docker volume rm recomendation_system_db_data

docker-compose restart ml-service
docker-compose down
docker-compose up

# Остановите ML-сервис
docker-compose stop ml-service

# Пересоберите с кэшем (быстрее)
docker-compose build ml-service

# Запустите
docker-compose up -d ml-service

Gb

# Проверка статуса контейнеров
docker-compose ps


# Запускаем все сервисы в фоновом режиме
docker-compose up -d --build

# Запуск с чистой БД
docker-compose up -d