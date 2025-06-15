from .gigachain_provider import GigaChainProvider
from .yandexgpt_provider import YandexGPTProvider
from app.utils.config import settings

class ProviderAdapter:
    def __init__(self):
        self.providers = {
            "gigachain": GigaChainProvider(),
            "yandexgpt": YandexGPTProvider()
        }
        self.default_provider = settings.DEFAULT_PROVIDER

    def get_provider(self, provider_name: str = None) -> BaseProvider:
        provider_name = provider_name or self.default_provider
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not supported")
        return self.providers[provider_name]

    async def send_request(self, provider_name: str, messages: List[Dict], **kwargs):
        provider = self.get_provider(provider_name)
        return await provider.send_request(messages, **kwargs)

    async def process_file(self, provider_name: str, file_path: str, **kwargs):
        provider = self.get_provider(provider_name)
        return await provider.process_file(file_path, **kwargs)