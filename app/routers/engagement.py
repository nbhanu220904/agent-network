from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.db import pool
from app.schemas import ReportCreate
from app.security import current_agent

router = APIRouter()
REPORT_THRESHOLD = 3

@router.post('/posts/{post_id}/ignore')
def ignore(post_id: UUID, agent_id=Depends(current_agent)):
    with pool.connection() as conn:
        conn.execute(
            'UPDATE routing_logs SET status = %s WHERE post_id = %s AND target_agent_id = %s AND status = %s',
            ('IGNORED', post_id, agent_id, 'NOTIFIED'),
        )
    return {'status': 'ignored'}

@router.post('/posts/{post_id}/report', status_code=201)
def report(post_id: UUID, body: ReportCreate, agent_id=Depends(current_agent)):
    with pool.connection() as conn:
        row = conn.execute('SELECT author_agent_id FROM posts WHERE id = %s', (post_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'Post not found')
        conn.execute(
            'INSERT INTO reports (post_id, reporter_agent_id, reason) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING',
            (post_id, agent_id, body.reason),
        )
        count = conn.execute(
            'SELECT COUNT(DISTINCT reporter_agent_id) FROM reports WHERE post_id = %s', (post_id,)
        ).fetchone()[0]
        if count == REPORT_THRESHOLD:  # drop the author's trust once, when the threshold is crossed
            conn.execute(
                'UPDATE agents SET trust_score = GREATEST(0.2, trust_score - 0.2) WHERE id = %s', (row[0],)
            )
    return {'reports': count}