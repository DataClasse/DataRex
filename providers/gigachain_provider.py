from .base_provider import BaseProvider
from app.utils.config import settings
from app.utils.logger import logger
from gigachain import GigaChat, GigaChatMultimodal
import os

class GigaChainProvider(BaseProvider):
    provider_name = "gigachain"

    def __init__(self):
        self.text_client = GigaChat(
            credentials=settings.GIGA_API_KEY,
            verify_ssl_certs=False,
            model=settings.GIGA_MODEL
        )
        self.multimodal_client = GigaChatMultimodal(
            credentials=settings.GIGA_API_KEY,
            profanity_check=False
        )

    async def send_request(
        self,
        messages: List[Dict],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        # Применение значений по умолчанию и валидация
        temperature = temperature or settings.GIGA_TEMPERATURE
        top_p = top_p or settings.GIGA_TOP_P
        max_tokens = max_tokens or settings.GIGA_MAX_TOKENS
        temperature, top_p, max_tokens = self._validate_params(temperature, top_p, max_tokens)
        
        try:
            # Определяем, есть ли изображения
            has_image = any('image' in msg for msg in messages)
            client = self.multimodal_client if has_image else self.text_client
            
            # Преобразуем сообщения в формат GigaChain
            giga_messages = []
            for msg in messages:
                if 'image' in msg:
                    giga_messages.append({
                        'role': msg['role'],
                        'content': msg.get('content', ''),
                        'image': msg['image']
                    })
                else:
                    giga_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            # Отправляем запрос с параметрами
            response = await client.ainvoke(
                giga_messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens
            )
            
            return {
                "content": response.choices[0].message.content,
                "model": settings.GIGA_MODEL,
                "provider": self.provider_name,
                "params": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_tokens": max_tokens
                }
            }
        except Exception as e:
            logger.error(f"GigaChain request error: {str(e)}")
            raise

    async def process_file(self, file_path: str, **kwargs) -> Optional[str]:
        """Обработка файлов средствами экосистемы GigaChain"""
        from gigachain.document_loaders import TextLoader, PyPDFLoader
        
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            return "\n\n".join([page.page_content for page in pages])
        
        elif file_path.endswith(('.txt', '.md')):
            loader = TextLoader(file_path)
            documents = loader.load()
            return documents[0].page_content
        
        # Для изображений возвращаем путь (будет обработано мультимодальной моделью)
        elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            return file_path
        
        return None

    def count_tokens(self, text: str) -> int:
        # Для GigaChain: 1 токен ≈ 4 символа
        return len(text) // 4

    def truncate_messages(self, messages: List[Dict], max_tokens: int) -> List[Dict]:
        """Интеллектуальное усечение контекста с приоритизацией"""
        current_tokens = sum(self.count_tokens(msg['content']) for msg in messages)
        if current_tokens <= max_tokens:
            return messages
        
        # Сохраняем системные промпты и последние сообщения
        important_messages = [msg for msg in messages if msg.get('role') == 'system']
        other_messages = [msg for msg in messages if msg.get('role') != 'system']
        
        # Оставляем последние N сообщений
        MAX_LAST_MESSAGES = 5
        truncated = important_messages + other_messages[-MAX_LAST_MESSAGES:]
        
        return truncated