# parse-gov-kz

📰 Gov.kz News Parser & CKAN Uploader
Этот проект автоматически парсит новости с портала www.gov.kz по министерствам Республики Казахстан и публикует их на портале открытых данных data.opengov.kz в формате CSV через CKAN API.

🔧 Возможности
Парсинг новостей с gov.kz на 3 языках: kk, ru, en

Сохранение всех новостей в CSV-файл

Поддержка парсинга по министерствам

Загрузка или обновление CSV-файла как ресурса на CKAN

Автоматическое создание датасета, если он не существует

Обновление метаданных CKAN-датасета

📁 Структура проекта
bash
Копировать
Редактировать
gov-news-project/
├── gov_kz_news_parser.py          # Скрипт парсинга gov.kz
├── enhanced_ckan_uploader.py     # Скрипт загрузки CSV на CKAN
├── .env               # Секреты (например, CKAN_TOKEN)
└── README.md          # Этот файл
⚙️ Установка
Клонируйте репозиторий:

git clone https://github.com/your-username/gov-news-project.git
cd gov-news-project

Установите зависимости:

pip install -r requirements.txt
Создайте .env файл:

CKAN_TOKEN=ваш_токен
📌 Скрипт 1: Парсинг новостей с gov.kz (parser.py)
Парсит новости министерств Казахстана с портала gov.kz, сохраняет в CSV (один файл) на трёх языках.

✅ Пример запуска:

python parser.py --output news.csv
📥 Аргументы:

Аргумент	Обязателен	Описание
--output	✅	Путь к результирующему CSV-файлу
--lang	❌	Язык новостей: kk, ru, en или all (по умолчанию: all)
--limit	❌	Максимум новостей на одно министерство (по умолчанию: 50)
📌 Скрипт 2: Загрузка в CKAN (upload_ckan.py)
Загружает CSV-файл на портал CKAN (data.opengov.kz) в датасет и создаёт его при необходимости.

✅ Пример запуска:

python upload_ckan.py \
  --host data.opengov.kz \
  --file news.csv \
  --dataset gov-news-2025 \
  --dataset-title "Новости министерств РК" \
  --dataset-desc "Автоматическая выгрузка новостей с портала gov.kz" \
  --org mininf \
  --email info@min.gov.kz
📥 Обязательные аргументы:
--host: Хост CKAN (data.opengov.kz)

--file: Путь к CSV-файлу

--dataset: ID датасета (создаётся при отсутствии)

--org: ID организации в CKAN

--email: Email автора данных

⚙️ Необязательные параметры:
--token: CKAN API токен (если не указан — берётся из .env)

--dataset-title: Название датасета

--dataset-desc: Описание датасета

--tags: Теги (по умолчанию: news,government,kazakhstan,ministries)

--resource-name: Название ресурса

--resource-desc: Описание ресурса

--source: URL источника (по умолчанию: https://www.gov.kz)

--update-metadata: Флаг для обновления метаданных

--delay: Задержка между запросами (по умолчанию: 1 секунда)

🧪 Рабочий пример (комбинированный)

# Шаг 1: Спарсить новости
python parser.py --output news.csv --lang all

# Шаг 2: Загрузить в CKAN
python upload_ckan.py \
  --host data.opengov.kz \
  --file news.csv \
  --dataset gov-news-2025 \
  --dataset-title "Новости министерств РК" \
  --dataset-desc "Автоматическая выгрузка новостей с портала gov.kz" \
  --org mininf \
  --email info@min.gov.kz
🛡️ Требования
Python 3.7+

API-токен с правами на создание/изменение датасетов в CKAN

Подключение к интернету