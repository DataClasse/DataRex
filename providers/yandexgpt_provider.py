from .base_provider import BaseProvider
from app.utils.config import settings
from app.utils.logger import logger
import httpx
import base64
import os
from typing import List, Dict, Any, Optional

class YandexGPTProvider(BaseProvider):
    provider_name = "yandexgpt"

    def __init__(self):
        self.api_url = "https://llm.api.cloud.yandex.net/llm/v1alpha/chat"
        self.vision_url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"

    async def send_request(
        self,
        messages: List[Dict],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        # Применение значений по умолчанию и валидация
        temperature = temperature or settings.YANDEX_TEMPERATURE
        top_p = top_p or settings.YANDEX_TOP_P
        max_tokens = max_tokens or settings.YANDEX_MAX_TOKENS
        temperature, top_p, max_tokens = self._validate_params(temperature, top_p, max_tokens)
        
        headers = {
            "Authorization": f"Api-Key {settings.YANDEX_API_KEY}",
            "x-folder-id": settings.YANDEX_FOLDER_ID
        }
        
        # Оптимизация контекста
        messages = self.truncate_messages(messages, settings.MAX_CONTEXT_TOKENS)
        
        payload = {
            "model": "general",
            "messages": messages,
            "generationOptions": {
                "temperature": temperature,
                "topP": top_p,
                "maxTokens": max_tokens
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return {
                "content": data['result']['alternatives'][0]['message']['text'],
                "model": "YandexGPT",
                "provider": self.provider_name,
                "params": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_tokens": max_tokens
                }
            }

    async def process_file(self, file_path: str, **kwargs) -> Optional[str]:
        """Обработка файлов средствами экосистемы Yandex"""
        # Для изображений используем Yandex Vision
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            return await self._process_image_with_vision(file_path)
        
        # Для документов можно использовать Yandex DocAI (заглушка)
        elif file_path.endswith(('.pdf', '.docx')):
            return await self._process_document(file_path)
        
        # Для текстовых файлов просто читаем содержимое
        elif file_path.endswith(('.txt', '.md')):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        
        return None

    async def _process_image_with_vision(self, file_path: str) -> str:
        """Использование Yandex Vision API для обработки изображений"""
        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        payload = {
            "analyze_specs": [{
                "content": image_data,
                "features": [{
                    "type": "TEXT_DETECTION"
                }]
            }]
        }
        
        headers = {
            "Authorization": f"Api-Key {settings.YANDEX_VISION_API_KEY}",
            "x-folder-id": settings.YANDEX_FOLDER_ID
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.vision_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            text_annotations = data['results'][0]['results'][0]['textDetection']['pages'][0]['blocks']
            return " ".join([block['lines'][0]['words'][0]['text'] for block in text_annotations)

    async def _process_document(self, file_path: str) -> str:
        """Заглушка для обработки документов (реализация через DocAI)"""
        # В реальной реализации здесь будет интеграция с Yandex DocAI
        return f"Document content: {os.path.basename(file_path)}"

    def count_tokens(self, text: str) -> int:
        # Для YandexGPT: 1 токен ≈ 1 слово
        return len(text.split())

    def truncate_messages(self, messages: List[Dict], max_tokens: int) -> List[Dict]:
        """Усечение контекста с сохранением важных сообщений"""
        current_tokens = 0
        truncated = []
        
        # Проходим в обратном порядке, сохраняя последние сообщения
        for msg in reversed(messages):
            msg_tokens = self.count_tokens(msg['content'])
            if current_tokens + msg_tokens <= max_tokens:
                truncated.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
                
        return truncated