#Вход в MySql
docker-compose exec db mysql -uroot -prootpassword book_recommender

#Очистка БД
docker volume rm recomendation_system_db_data

# Перезапуск мл сервиса
docker-compose restart ml-service
docker-compose down
docker-compose up

# Остановите ML-сервис
docker-compose stop ml-service

# Пересоберите с кэшем (быстрее)
docker-compose build ml-service

# Запустите
docker-compose up -d ml-service


# Проверка статуса контейнеров
docker-compose ps


# Запускаем все сервисы в фоновом режиме
docker-compose up -d --build

# Запуск с чистой БД
docker-compose up -d

http://localhost:8081/index.php?route=/database/structure&db=book_recommender
http://localhost:8000/docs#/default/get_similar_books_api_v1_similar_post 


API: secret-ml-api-key-2024


python -m pip install kagglehub