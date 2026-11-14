from fastapi import APIRouter, Depends
from app.db import pool
from app.schemas import SubscriptionCreate
from app.security import current_agent

router = APIRouter()

@router.post('/agents/me/subscriptions', status_code=201)
def add_subscription(body: SubscriptionCreate, agent_id=Depends(current_agent)):
    with pool.connection() as conn:
        sid = conn.execute(
            'INSERT INTO subscriptions (agent_id, kind, topic, keywords) VALUES (%s, %s, %s, %s) RETURNING id',
            (agent_id, body.kind, body.topic, body.keywords),
        ).fetchone()[0]
    return {'subscription_id': str(sid)}

@router.get('/agents/me/subscriptions')
def list_subscriptions(agent_id=Depends(current_agent)):
    with pool.connection() as conn:
        rows = conn.execute(
            'SELECT id, kind, topic, keywords FROM subscriptions WHERE agent_id = %s AND is_active',
            (agent_id,),
        ).fetchall()
    return [{'id': str(r[0]), 'kind': r[1], 'topic': r[2], 'keywords': r[3]} for r in rows]