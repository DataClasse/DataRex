from fastapi import APIRouter, UploadFile, File, Query, Depends
from fastapi.security import HTTPBearer
from app.core.chat_manager import ChatManager
from app.services.auth_service import AuthService
from app.utils.logger import logger
import os
import uuid

router = APIRouter()
auth_scheme = HTTPBearer()

@router.post("/analyze-image")
async def analyze_image_endpoint(
    image: UploadFile = File(...),
    prompt: str = Query("Опиши изображение детально", description="Промпт для анализа"),
    temperature: float = Query(0.4, ge=0.1, le=1.0, description="Температура генерации"),
    max_tokens: int = Query(1024, gt=0, le=4096, description="Макс. количество токенов"),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    try:
        # Аутентификация пользователя
        user_id = AuthService().get_current_user(token.credentials)
        
        # Сохраняем изображение
        file_path = f"{settings.STORAGE_PATH}/uploads/{uuid.uuid4()}_{image.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            buffer.write(await image.read())
        
        # Анализируем изображение
        chat_manager = ChatManager()
        analysis = await chat_manager.analyze_image(
            file_path,
            prompt,
            temperature,
            max_tokens
        )
        
        return analysis
    
    except Exception as e:
        logger.error(f"Image analysis error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }