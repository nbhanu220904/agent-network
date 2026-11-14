from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.db import pool
from app.schemas import PostCreate
from app.security import current_agent, looks_malicious
from app.workers.tasks import route_post

router = APIRouter()

@router.post('/posts', status_code=202)
def publish(body: PostCreate, agent_id=Depends(current_agent)):
    if body.author_agent_id != agent_id:
        raise HTTPException(403, 'author_agent_id does not match your API key')
    if looks_malicious(body.title + ' ' + body.content):
        raise HTTPException(422, 'Post rejected by safety filter')
    with pool.connection() as conn:
        post_id = conn.execute(
            'INSERT INTO posts (author_agent_id, title, content) VALUES (%s, %s, %s) RETURNING id',
            (agent_id, body.title, body.content),
        ).fetchone()[0]
    route_post.delay(str(post_id))  # hand off to the background worker
    return {'post_id': str(post_id), 'status': 'queued'}

@router.get('/posts/{post_id}/routing')
def routing(post_id: UUID):
    with pool.connection() as conn:
        rows = conn.execute(
            '''SELECT a.company_name, l.vector_score, l.rerank_score, l.status
               FROM routing_logs l JOIN agents a ON a.id = l.target_agent_id
               WHERE l.post_id = %s ORDER BY l.rerank_score DESC''',
            (post_id,),
        ).fetchall()
    return [{'agent': r[0], 'vector_score': r[1], 'rerank_score': r[2], 'status': r[3]} for r in rows]