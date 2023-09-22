# Проект Foodgram - «Кулинарный Помощник»

### Введение:
Наш сервис - это настоящий кулинарный помощник, который облегчит вам жизнь при приготовлении блюд. Вы сможете создавать и просматривать рецепты, подписываться на интересных авторов, а также добавлять рецепты в избранное и в список покупок. К тому же, список покупок можно выгрузить в виде файла, в котором будут перечислены все необходимые ингредиенты для приготовления выбранных блюд.


Проект доступен по адресу: [https://mc6.ddns.net/cart/](https://mc6.ddns.net/cart/)

### Технологический стек
- Django
- Django Rest Framework
- Docker
- Docker-compose
- Gunicorn
- Nginx
- PostgreSQL

### Процесс работы
- **tests:** Проводим автоматическую проверку кода на соответствие стандартам PEP8, чтобы код был чистым и читаемым.
- **push Docker image to Docker Hub:** Собираем и публикуем образы на DockerHub, что упрощает развертывание на разных серверах.
- **deploy:** Автоматически разворачиваем приложение на боевом сервере при пуше в главную ветку main, обеспечивая моментальное обновление.
- **send_massage:** Отправляем уведомления о статусе деплоя в телеграм-чат, чтобы всегда быть в курсе происходящего.

### Подготовка и запуск проекта
Для успешного запуска проекта у вас должен быть установлен Docker, а также вы должны зарегистрироваться на [DockerHub](https://hub.docker.com/)
- Клонировать проект, используя команду git clone или загрузить ZIP-архив с проектом.
- Перейти в папку \foodgram-project-react\backend и выполнить следующие команды в командной строке:
```bash
sudo docker build -t <логин на DockerHub>/<название образа для бэкенда, какое хотите)> .
sudo docker login
sudo docker push <логин на DockerHub>/<название образа для бэкенда, которое написали> 
```
- Затем перейти в папку \foodgram-project-react\frontend и выполнить аналогичные команды, заменив <название_образа_для_фронтэнда> на ваш вариант.
```bash
sudo docker build -t <логин на DockerHub>/<название образа для фронтэнда, какое хотите)> .
sudo docker login
sudo docker push <логин на DockerHub>/<название образа для фронтэнда, которое написали> 
```
- Изменить файл \foodgram-project-react\infra\deploy\docker-compose.yml:
```
backend:
  image: <логин на DockerHub>/<название образа для бэкенда, которое написали>
  
frontend:
  image: <логин на DockerHub>/<название образа для фронтэнда, которое написали>
```
- В файле \foodgram-project-react\.github\workflows\foodgram_workflow.yml также замените строки::
```
build_and_push_to_docker_hub:
.......
    tags: ${{ secrets.DOCKER_USERNAME }}/<название образа для бэкенда, которое написали>
    
deploy:
.......
    sudo docker pull ${{ secrets.DOCKER_USERNAME }}/<название образа для бэкенда, которое написали>
```
- Выполнить вход на удаленный сервер
- Установить docker на сервер:
```bash
sudo apt install docker.io 
```
- Установить docker-compose на сервер:
```bash
sudo apt-get update
sudo apt install docker-compose
```
- Скопировать файл docker-compose.yml и nginx.conf из директории infra на сервер:
```bash
scp docker-compose.yml <username>@<host>:/home/<username>/
scp nginx.conf <username>@<host>:/home/<username>/
```
- Для работы с Workflow добавить в Secrets GitHub переменные окружения:
```
DOCKER_PASSWORD=<пароль DockerHub>
DOCKER_USERNAME=<имя пользователя DockerHub>

USER=<username для подключения к серверу>
HOST=<IP сервера>
PASSPHRASE=<пароль для сервера, если он установлен>
SSH_KEY=<ваш SSH ключ (для получения команда: cat ~/.ssh/id_rsa)>

TELEGRAM_TO=<ID своего телеграм-аккаунта>
TELEGRAM_TOKEN=<токен вашего бота>
```
- После деплоя изменений в git, дождитесь выполнения всех Actions.
- Зайдите на боевой сервер и выполните команды:
  * Создаем и применяем миграции
    ```bash
    sudo docker-compose exec backend python manage.py migrate
    ```
  * Подгружаем статику
    ```bash
    sudo docker-compose exec backend python manage.py collectstatic --no-input 
    ```
  * Создать суперпользователя Django
    ```bash
    sudo docker-compose exec backend python manage.py createsuperuser
    ```
  * Загрузить подготовленный список ингредиентов
    ```bash
    sudo docker-compose exec backend python manage.py loaddata ingredients.json
    ```

- Проект будет доступен по вашему IP-адресу.

#### REST API
Для детальной документации по API, пожалуйста, используйте - http://<IP-адрес вашего сервера>/api/docs/

#### Автор:
Юрий Пылёв - [https://github.com/ya-yura](https://github.com/ya-yura)
