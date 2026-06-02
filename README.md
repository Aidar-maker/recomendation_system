docker exec -it book_ml alembic revision --autogenerate -m "initial schema" 
docker exec -it book_ml alembic upgrade head    
docker exec -it book_db mysql -uroot -prootpassword book_recommender -e "SHOW TABLES;"