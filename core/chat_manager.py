from app.providers.adapter import ProviderAdapter
from app.storage.thread_storage import ThreadStorage
from app.services.file_processor import FileProcessor
from app.plugins.vision_plugin import VisionPlugin
from app.utils.config import settings
from app.utils.logger import logger
from typing import Dict, List, Optional, Union
import os

class ChatManager:
    """Управление логикой чата и взаимодействием с провайдерами"""
    
    def __init__(self):
        self.thread_storage = ThreadStorage()
        self.provider_adapter = ProviderAdapter()
        self.file_processor = FileProcessor()
        self.vision_plugin = VisionPlugin(self.provider_adapter)
    
    async def send_message(
        self,
        thread_id: str,
        user_id: str,
        message: str,
        file_data: Optional[dict] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> dict:
        """
        Отправка сообщения и получение ответа от AI
        
        :param thread_id: Идентификатор треда
        :param user_id: Идентификатор пользователя
        :param message: Текст сообщения
        :param file_data: Данные файла (если есть)
        :param temperature: Температура генерации
        :param top_p: Кумулятивная вероятность
        :param max_tokens: Максимальное количество токенов
        :return: Ответ AI
        """
        # Получение треда
        thread = self.thread_storage.get_thread(thread_id)
        if not thread or thread["user_id"] != user_id:
            raise ValueError("Thread not found or access denied")
        
        provider_name = thread.get("provider", settings.DEFAULT_PROVIDER)
        
        # Формирование сообщения пользователя
        user_message = {"role": "user", "content": message}
        if file_data:
            user_message["file"] = file_data
        
        # Добавление сообщения в тред
        self.thread_storage.add_message(thread_id, user_message)
        
        # Получение истории сообщений
        messages = thread["messages"] + [user_message]
        
        # Отправка запроса к провайдеру
        response = await self.provider_adapter.send_request(
            provider_name,
            messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens
        )
        
        # Формирование ответа AI
        ai_message = {
            "role": "assistant",
            "content": response["content"],
            "provider": provider_name,
            "params": response.get("params", {})
        }
        
        # Добавление ответа AI в тред
        self.thread_storage.add_message(thread_id, ai_message)
        
        return ai_message
    
    async def analyze_image(
        self,
        image_path: str,
        prompt: str = "Опиши изображение детально",
        temperature: float = 0.4,
        max_tokens: int = 1024
    ) -> Dict[str, Union[str, dict]]:
        """
        Анализирует изображение с помощью плагина анализа изображений
        
        :param image_path: Путь к изображению
        :param prompt: Промпт для анализа
        :param temperature: Температура генерации
        :param max_tokens: Максимальное количество токенов
        :return: Результат анализа
        """
        # Проверка существования файла
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Анализ изображения
        return await self.vision_plugin.analyze_image(
            image_path,
            prompt,
            temperature,
            max_tokens
        )
    
    async def create_thread(
        self,
        user_id: str,
        title: str = "New Conversation",
        provider: str = None
    ) -> str:
        """
        Создает новый тред для диалога
        
        :param user_id: Идентификатор пользователя
        :param title: Заголовок треда
        :param provider: Провайдер по умолчанию
        :return: Идентификатор созданного треда
        """
        return self.thread_storage.create_thread(
            user_id=user_id,
            title=title,
            provider=provider
        )
    
    async def get_thread_messages(
        self,
        thread_id: str,
        user_id: str
    ) -> List[Dict]:
        """
        Получает сообщения треда
        
        :param thread_id: Идентификатор треда
        :param user_id: Идентификатор пользователя
        :return: Список сообщений
        """
        thread = self.thread_storage.get_thread(thread_id)
        if not thread or thread["user_id"] != user_id:
            raise ValueError("Thread not found or access denied")
        return thread["messages"]
    
    async def delete_thread(
        self,
        thread_id: str,
        user_id: str
    ) -> bool:
        """
        Удаляет тред
        
        :param thread_id: Идентификатор треда
        :param user_id: Идентификатор пользователя
        :return: Статус удаления
        """
        thread = self.thread_storage.get_thread(thread_id)
        if not thread or thread["user_id"] != user_id:
            return False
        
        # Удаление файлов треда
        for message in thread["messages"]:
            if "file" in message and "path" in message["file"]:
                file_path = message["file"]["path"]
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.error(f"Error deleting file {file_path}: {str(e)}")
        
        # Удаление треда из хранилища
        return self.thread_storage.delete_thread(thread_id)
    
    async def list_user_threads(
        self,
        user_id: str
    ) -> List[Dict]:
        """
        Возвращает список тредов пользователя
        
        :param user_id: Идентификатор пользователя
        :return: Список тредов
        """
        return self.thread_storage.list_threads(user_id)