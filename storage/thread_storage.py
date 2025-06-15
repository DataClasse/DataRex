import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from app.utils.config import settings
from app.utils.logger import logger
from redis import Redis
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ThreadModel(Base):
    __tablename__ = "threads"
    
    id = Column(String, primary_key=True)
    user_id = Column(String)
    title = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    messages = Column(JSON)
    provider = Column(String)

class ThreadStorage:
    def __init__(self):
        if settings.DATABASE_URL.startswith("redis"):
            self.redis = Redis.from_url(settings.REDIS_URL)
            self.mode = "redis"
        else:
            self.engine = create_engine(settings.DATABASE_URL)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            self.mode = "database"

    def create_thread(self, user_id: str, title: str = "New Conversation", provider: str = None) -> str:
        thread_id = str(uuid.uuid4())
        thread_data = {
            "id": thread_id,
            "user_id": user_id,
            "title": title,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "messages": [],
            "provider": provider or settings.DEFAULT_PROVIDER
        }
        
        if self.mode == "redis":
            self.redis.set(f"thread:{thread_id}", json.dumps(thread_data, default=str))
        else:
            session = self.Session()
            thread = ThreadModel(**thread_data)
            session.add(thread)
            session.commit()
            session.close()
        
        return thread_id

    def get_thread(self, thread_id: str) -> Dict:
        if self.mode == "redis":
            data = self.redis.get(f"thread:{thread_id}")
            return json.loads(data) if data else None
        else:
            session = self.Session()
            thread = session.query(ThreadModel).filter_by(id=thread_id).first()
            session.close()
            return {
                "id": thread.id,
                "user_id": thread.user_id,
                "title": thread.title,
                "created_at": thread.created_at,
                "updated_at": thread.updated_at,
                "messages": thread.messages,
                "provider": thread.provider
            } if thread else None

    def update_thread(self, thread_id: str, update_data: Dict):
        thread = self.get_thread(thread_id)
        if not thread:
            raise ValueError("Thread not found")
        
        thread.update(update_data)
        thread["updated_at"] = datetime.utcnow()
        
        if self.mode == "redis":
            self.redis.set(f"thread:{thread_id}", json.dumps(thread, default=str))
        else:
            session = self.Session()
            session.query(ThreadModel).filter_by(id=thread_id).update(update_data)
            session.commit()
            session.close()

    def add_message(self, thread_id: str, message: Dict):
        thread = self.get_thread(thread_id)
        if not thread:
            raise ValueError("Thread not found")
        
        thread["messages"].append(message)
        self.update_thread(thread_id, {"messages": thread["messages"]})

    def list_threads(self, user_id: str) -> List[Dict]:
        if self.mode == "redis":
            keys = self.redis.keys("thread:*")
            threads = []
            for key in keys:
                thread = json.loads(self.redis.get(key))
                if thread["user_id"] == user_id:
                    threads.append({
                        "id": thread["id"],
                        "title": thread["title"],
                        "created_at": thread["created_at"],
                        "updated_at": thread["updated_at"]
                    })
            return threads
        else:
            session = self.Session()
            threads = session.query(ThreadModel).filter_by(user_id=user_id).all()
            session.close()
            return [{
                "id": t.id,
                "title": t.title,
                "created_at": t.created_at,
                "updated_at": t.updated_at
            } for t in threads]