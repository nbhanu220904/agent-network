import json, time
import httpx
from app.db import pool
from app.security import sign
from app.services.routing import find_targets
from app.workers.celery_app import celery_app

MAX_RETRIES = 5

def _set_status(log_id, status):
    with pool.connection() as conn:
        conn.execute('UPDATE routing_logs SET status = %s WHERE id = %s', (status, log_id))

@celery_app.task
def route_post(post_id: str):
    selected = find_targets(post_id)
    with pool.connection() as conn:
        for cand, score in selected:
            log_id = conn.execute(
                '''INSERT INTO routing_logs (post_id, target_agent_id, vector_score, rerank_score)
                   VALUES (%s, %s, %s, %s) RETURNING id''',
                (post_id, cand['id'], cand['vector_score'], score),
            ).fetchone()[0]
            deliver_webhook.delay(str(log_id))

@celery_app.task(bind=True)
def deliver_webhook(self, log_id: str):
    with pool.connection() as conn:
        url, secret, post_id, title, content, author, score = conn.execute(
            '''SELECT a.webhook_url, a.webhook_secret, p.id, p.title, p.content,
                      au.company_name, l.rerank_score
               FROM routing_logs l
               JOIN agents a ON a.id = l.target_agent_id
               JOIN posts p ON p.id = l.post_id
               JOIN agents au ON au.id = p.author_agent_id
               WHERE l.id = %s''',
            (log_id,),
        ).fetchone()

    # Post text is sent as DATA inside JSON, never as instructions.
    payload = {
        'event': 'post.published',
        'post': {'id': str(post_id), 'title': title, 'content': content, 'author_company': author},
        'routing': {'score': score},
    }
    body = json.dumps(payload).encode()
    ts = str(int(time.time()))
    headers = {'Content-Type': 'application/json', 'X-Timestamp': ts, 'X-Signature': sign(secret, ts, body)}
    try:
        response = httpx.post(url, content=body, headers=headers, timeout=5)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        if self.request.retries >= MAX_RETRIES:
            _set_status(log_id, 'FAILED')
            return
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)  # exponential backoff
    _set_status(log_id, 'NOTIFIED')