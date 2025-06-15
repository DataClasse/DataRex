from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseProvider(ABC):
    provider_name: str

    @abstractmethod
    async def send_request(
        self,
        messages: List[Dict],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def process_file(self, file_path: str, **kwargs) -> Optional[str]:
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        pass

    @abstractmethod
    def truncate_messages(self, messages: List[Dict], max_tokens: int) -> List[Dict]:
        pass
    
    def _validate_params(
        self,
        temperature: Optional[float],
        top_p: Optional[float],
        max_tokens: Optional[int]
    ) -> tuple:
        """Валидация и нормализация параметров"""
        # Ограничение значений в допустимых диапазонах
        temperature = max(0.1, min(temperature, 1.0)) if temperature is not None else None
        top_p = max(0.1, min(top_p, 1.0)) if top_p is not None else None
        max_tokens = min(max_tokens, 8192) if max_tokens is not None else None
        
        return temperature, top_p, max_tokens