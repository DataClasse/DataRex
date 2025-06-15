datarex/
├── core/                         # Ядро системы
│   ├── chat_manager.py           # Управление тредами и диалогами
│   ├── context_optimizer.py      # Интеллектуальное управление контекстом
│   ├── provider_router.py        # Маршрутизация между провайдерами
│   └── plugin_system.py          # Система плагинов
├── providers/                    # Интеграции с AI API
│   ├── gigachain_provider.py     # Реализация GigaChain API
│   ├── yandexgpt_provider.py     # Реализация YandexGPT API
│   ├── base_provider.py          # Базовый интерфейс провайдера
│   └── adapter.py                # Адаптер для унификации ответов
├── services/                     # Бизнес-логика
│   ├── file_processor.py         # Обработка мультимодальных данных
│   ├── auth_service.py           # Аутентификация и авторизация
│   ├── cache_manager.py          # Управление кешированием
│   └── token_counter.py          # Подсчет токенов
├── storage/                      # Хранилища данных
│   ├── thread_storage.py         # Управление тредами (Redis/SQLite)
│   ├── file_storage.py           # Хранение загруженных файлов
│   └── vector_storage.py         # Векторные базы данных
├── api/                          # API Endpoints
│   ├── chat.py                   # Эндпоинты чата
│   ├── threads.py                # Управление тредами
│   ├── files.py                  # Работа с файлами
│   └── auth.py                   # Аутентификация
├── utils/                        # Вспомогательные утилиты
│   ├── config.py                 # Конфигурация приложения
│   ├── logger.py                 # Логирование
│   └── monitoring.py             # Мониторинг и метрики
├── plugins/                      # Расширения функционала
│   ├── rag_plugin.py             # Retrieval-Augmented Generation
│   ├── vision_plugin.py          # Расширенная обработка изображений
│   └── code_plugin.py            # Генерация кода
├── tests/                        # Тесты
├── frontend/                     # Vue.js фронтенд
├── scripts/                      # Скрипты развертывания
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.template
└── main.py                       # Точка входа в приложение