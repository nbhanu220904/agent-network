import secrets
import numpy as np
from fastapi import APIRouter, Header, HTTPException
from app.db import pool
from app.schemas import AgentRegister
from app.security import hash_key, new_secret
from app.services.embeddings import embed
from app.config import settings

router = APIRouter()

@router.post('/agents/register', status_code=201)
def register(body: AgentRegister, x_admin_token: str = Header(default='')):
    if settings.registration_token and not secrets.compare_digest(x_admin_token, settings.registration_token):
        raise HTTPException(status_code=403, detail='Registration requires a valid admin token')
    api_key = 'ak_' + secrets.token_urlsafe(24)
    webhook_secret = new_secret()
    vec = np.array(embed(body.interest_manifesto))
    with pool.connection() as conn:
        row = conn.execute(
            '''INSERT INTO agents (company_name, industry_category, webhook_url, webhook_secret,
                                   api_key_hash, interest_manifesto, interest_embedding)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id''',
            (body.company_name, body.industry_category, str(body.webhook_url), webhook_secret,
             hash_key(api_key), body.interest_manifesto, vec),
        ).fetchone()
    # The API key is shown only once; only its hash is stored.
    return {'agent_id': str(row[0]), 'api_key': api_key, 'webhook_secret': webhook_secret}