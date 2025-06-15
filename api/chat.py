from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.chat_manager import ChatManager
from app.services.auth_service import AuthService
from app.utils.logger import logger
import os
import uuid

router = APIRouter()
chat_manager = ChatManager()
auth_scheme = HTTPBearer()

@router.post("/threads/{thread_id}/messages")
async def create_message(
    thread_id: str,
    message: str,
    temperature: Optional[float] = Query(None, ge=0.1, le=1.0, description="Температура генерации"),
    top_p: Optional[float] = Query(None, ge=0.1, le=1.0, description="Кумулятивная вероятность"),
    max_tokens: Optional[int] = Query(None, gt=0, le=8192, description="Макс. количество токенов"),
    file: UploadFile = File(None),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    try:
        # Аутентификация пользователя
        user_id = AuthService().get_current_user(token.credentials)
        
        # Обработка файла
        file_data = None
        if file:
            # Сохраняем файл временно
            file_path = f"{settings.STORAGE_PATH}/uploads/{uuid.uuid4()}_{file.filename}"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
            
            # Получаем информацию о треде для выбора провайдера
            thread = chat_manager.thread_storage.get_thread(thread_id)
            provider_name = thread.get("provider", settings.DEFAULT_PROVIDER)
            
            # Обрабатываем файл
            file_data = await chat_manager.file_processor.process_file(
                provider_name, 
                file_path
            )
        
        # Отправляем сообщение с параметрами
        response = await chat_manager.send_message(
            thread_id, 
            user_id, 
            message, 
            file_data,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens
        )
        return response
    
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))