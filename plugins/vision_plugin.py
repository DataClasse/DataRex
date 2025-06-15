# plugins/vision_plugin.py
from app.providers.adapter import ProviderAdapter
from app.utils.config import settings
from app.utils.logger import logger
from app.services.file_storage import FileStorage
from typing import Dict, Optional, Union
import httpx
import base64
import os
import uuid
import mimetypes
import json

class VisionPlugin:
    """Плагин для расширенного анализа изображений с поддержкой мультимодальных моделей"""
    
    def __init__(self, provider_adapter: ProviderAdapter):
        self.provider_adapter = provider_adapter
        self.file_storage = FileStorage()
        self.supported_formats = ['.png', '.jpg', '.jpeg', '.webp', '.bmp']
    
    async def analyze_image(
        self, 
        image_path: str, 
        prompt: str = "Опиши изображение детально",
        temperature: float = 0.4,
        max_tokens: int = 1024
    ) -> Dict[str, Union[str, dict]]:
        """
        Анализирует изображение с помощью мультимодальной модели
        
        :param image_path: Путь к изображению
        :param prompt: Промпт для анализа
        :param temperature: Температура генерации
        :param max_tokens: Максимальное количество токенов
        :return: Результат анализа с метаданными
        """
        try:
            # Проверка формата изображения
            if not self._is_supported_format(image_path):
                return self._process_unsupported_format(image_path)
            
            # Определение провайдера по конфигурации
            provider_name = settings.DEFAULT_PROVIDER
            
            # Для GigaChain используем прямой мультимодальный запрос
            if provider_name == "gigachain":
                return await self._analyze_with_gigachain(image_path, prompt, temperature, max_tokens)
            
            # Для YandexGPT используем Vision API + YandexGPT
            elif provider_name == "yandexgpt":
                return await self._analyze_with_yandex(image_path, prompt, temperature, max_tokens)
            
            # Для других провайдеров используем базовый метод
            else:
                return await self._basic_image_analysis(image_path, prompt)
        
        except Exception as e:
            logger.error(f"Image analysis error: {str(e)}")
            return {
                "status": "error",
                "message": f"Ошибка анализа изображения: {str(e)}",
                "provider": provider_name
            }
    
    async def _analyze_with_gigachain(
        self,
        image_path: str,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Union[str, dict]]:
        """Анализ изображения с помощью GigaChain Multimodal API"""
        # Формируем мультимодальное сообщение
        messages = [{
            "role": "user",
            "content": prompt,
            "image": image_path
        }]
        
        # Отправляем запрос
        response = await self.provider_adapter.send_request(
            "gigachain",
            messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "status": "success",
            "analysis": response["content"],
            "provider": "gigachain",
            "params": response.get("params", {})
        }
    
    async def _analyze_with_yandex(
        self,
        image_path: str,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Union[str, dict]]:
        """Анализ изображения с помощью Yandex Vision API + YandexGPT"""
        # Получаем описание изображения через Vision API
        vision_description = await self._get_vision_description(image_path)
        
        # Формируем запрос к YandexGPT
        messages = [
            {"role": "system", "content": "Ты - ассистент, который описывает изображения"},
            {"role": "user", "content": f"{prompt}\n\nОписание изображения: {vision_description}"}
        ]
        
        # Отправляем запрос
        response = await self.provider_adapter.send_request(
            "yandexgpt",
            messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "status": "success",
            "analysis": response["content"],
            "vision_description": vision_description,
            "provider": "yandexgpt",
            "params": response.get("params", {})
        }
    
    async def _get_vision_description(self, image_path: str) -> str:
        """Получает описание изображения через Yandex Vision API"""
        # Чтение и кодирование изображения
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        payload = {
            "analyze_specs": [{
                "content": image_data,
                "features": [
                    {"type": "OBJECT_DETECTION"},
                    {"type": "TEXT_DETECTION"},
                    {"type": "FACE_DETECTION"}
                ]
            }]
        }
        
        headers = {
            "Authorization": f"Api-Key {settings.YANDEX_VISION_API_KEY}",
            "x-folder-id": settings.YANDEX_FOLDER_ID
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # Извлекаем результаты анализа
            results = []
            features = data['results'][0]['results']
            
            for feature in features:
                if 'objectDetection' in feature:
                    objects = [obj['name'] for obj in feature['objectDetection']['objects']]
                    results.append(f"Объекты: {', '.join(objects)}")
                
                if 'textDetection' in feature:
                    text = feature['textDetection']['text']
                    results.append(f"Текст: {text}")
                
                if 'faceDetection' in feature:
                    faces = feature['faceDetection']['faces']
                    results.append(f"Лиц: {len(faces)}")
            
            return "; ".join(results)
    
    async def _basic_image_analysis(
        self, 
        image_path: str,
        prompt: str
    ) -> Dict[str, Union[str, dict]]:
        """Базовый анализ изображения для неподдерживаемых провайдеров"""
        # Просто возвращаем метаданные изображения
        return {
            "status": "info",
            "message": "Прямой анализ изображений не поддерживается текущим провайдером",
            "image_metadata": self._get_image_metadata(image_path),
            "provider": settings.DEFAULT_PROVIDER
        }
    
    def _is_supported_format(self, image_path: str) -> bool:
        """Проверяет поддерживаемый формат изображения"""
        ext = os.path.splitext(image_path)[1].lower()
        return ext in self.supported_formats
    
    def _process_unsupported_format(self, image_path: str) -> Dict[str, str]:
        """Обработка неподдерживаемых форматов изображений"""
        ext = os.path.splitext(image_path)[1].lower()
        return {
            "status": "error",
            "message": f"Неподдерживаемый формат изображения: {ext}",
            "supported_formats": ", ".join(self.supported_formats)
        }
    
    def _get_image_metadata(self, image_path: str) -> Dict[str, Union[str, int]]:
        """Извлекает метаданные изображения"""
        try:
            import PIL.Image
            from PIL.ExifTags import TAGS
            
            with PIL.Image.open(image_path) as img:
                # Базовые метаданные
                metadata = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height
                }
                
                # EXIF данные
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif() is not None:
                    for tag, value in img._getexif().items():
                        decoded = TAGS.get(tag, tag)
                        exif_data[decoded] = value
                
                if exif_data:
                    metadata["exif"] = exif_data
                
                return metadata
        except ImportError:
            return {"error": "PIL не установлен для извлечения метаданных"}
        except Exception as e:
            return {"error": str(e)}