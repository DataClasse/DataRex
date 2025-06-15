from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, threads, auth
from app.utils.config import settings
from app.utils.logger import logger
from app.utils.monitoring import setup_metrics
import uvicorn

app = FastAPI(
    title="DataRex API",
    description="Multimodal Chatbot with GigaChain and YandexGPT",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение эндпоинтов
app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(threads.router, prefix="/api")

# Настройка метрик Prometheus
setup_metrics(app)

@app.on_event("startup")
async def startup():
    logger.info("DataRex application started")
    # Инициализация подключений к БД
    from app.storage.thread_storage import ThreadStorage
    ThreadStorage()  # Автоматическое создание таблиц при необходимости

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        ssl_keyfile="./key.pem" if os.path.exists("./key.pem") else None,
        ssl_certfile="./cert.pem" if os.path.exists("./cert.pem") else None
    )