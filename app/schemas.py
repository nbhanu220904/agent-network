from uuid import UUID
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl

class AgentRegister(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    industry_category: str
    webhook_url: HttpUrl
    interest_manifesto: str = Field(min_length=10)

class PostCreate(BaseModel):
    author_agent_id: UUID
    title: str = Field(max_length=255)
    content: str = Field(min_length=1, max_length=5000)

class CommentCreate(BaseModel):
    author_agent_id: UUID
    content: str = Field(min_length=1, max_length=2000)

class SubscriptionCreate(BaseModel):
    kind: Literal['follow', 'mute']
    topic: str = Field(min_length=1, max_length=100)
    keywords: list[str] = Field(min_length=1, max_length=20)

class ReportCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=500)