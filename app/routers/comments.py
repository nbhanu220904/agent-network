from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.db import pool
from app.schemas import CommentCreate
from app.security import current_agent, looks_malicious

router = APIRouter()

@router.post('/posts/{post_id}/comments', status_code=201)
def add_comment(post_id: UUID, body: CommentCreate, agent_id=Depends(current_agent)):
    if body.author_agent_id != agent_id:
        raise HTTPException(403, 'author_agent_id does not match your API key')
    if looks_malicious(body.content):
        raise HTTPException(422, 'Comment rejected by safety filter')
    with pool.connection() as conn:
        cid = conn.execute(
            'INSERT INTO comments (post_id, author_agent_id, content) VALUES (%s, %s, %s) RETURNING id',
            (post_id, agent_id, body.content),
        ).fetchone()[0]
        conn.execute(
            'UPDATE routing_logs SET status = %s WHERE post_id = %s AND target_agent_id = %s',
            ('ENGAGED', post_id, agent_id),
        )
    return {'comment_id': str(cid)}

@router.get('/posts/{post_id}/comments')
def list_comments(post_id: UUID):
    with pool.connection() as conn:
        rows = conn.execute(
            '''SELECT a.company_name, c.content FROM comments c
               JOIN agents a ON a.id = c.author_agent_id
               WHERE c.post_id = %s ORDER BY c.created_at''',
            (post_id,),
        ).fetchall()
    return [{'agent': r[0], 'content': r[1]} for r in rows]