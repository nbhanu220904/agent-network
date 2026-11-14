from celery import Celery
from app.config import settings

celery_app = Celery('agentnet', broker=settings.redis_url, include=['app.workers.tasks'])