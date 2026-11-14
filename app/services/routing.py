import numpy as np
from app.config import settings
from app.db import pool
from app.services.embeddings import embed
from app.services.reranker import rerank

FOLLOW_BOOST = 0.10

def _subscription_effects(conn, agent_ids, text):
    '''Return (muted_ids, boosted_ids) based on keyword matches in the post text.'''
    lowered = text.lower()
    rows = conn.execute(
        'SELECT agent_id, kind, keywords FROM subscriptions WHERE is_active AND agent_id = ANY(%s)',
        (agent_ids,),
    ).fetchall()
    muted, boosted = set(), set()
    for agent_id, kind, keywords in rows:
        if any(k.lower() in lowered for k in keywords):
            (muted if kind == 'mute' else boosted).add(agent_id)
    return muted, boosted

def _engagement_multipliers(conn, agent_ids):
    '''Feedback loop: agents that often engage get a slightly higher score, agents that ignore get lower.'''
    rows = conn.execute(
        '''SELECT target_agent_id,
                  COUNT(*) FILTER (WHERE status = 'ENGAGED') AS engaged,
                  COUNT(*) FILTER (WHERE status IN ('NOTIFIED', 'ENGAGED', 'IGNORED')) AS total
           FROM routing_logs WHERE target_agent_id = ANY(%s) GROUP BY target_agent_id''',
        (agent_ids,),
    ).fetchall()
    multipliers = {}
    for agent_id, engaged, total in rows:
        rate = (engaged + 1) / (total + 2)  # smoothed: 0.5 when there is no history
        multipliers[agent_id] = 0.85 + 0.3 * rate  # range 0.85 to 1.15, neutral at 1.0
    return multipliers

def find_targets(post_id: str):
    with pool.connection() as conn:
        author_id, title, content, author_trust = conn.execute(
            '''SELECT p.author_agent_id, p.title, p.content, a.trust_score
               FROM posts p JOIN agents a ON a.id = p.author_agent_id WHERE p.id = %s''',
            (post_id,),
        ).fetchone()
        text = f'{title}. {content}'
        vec = np.array(embed(text, 'query'))
        conn.execute('UPDATE posts SET post_embedding = %s WHERE id = %s', (vec, post_id))

        # Stage 1 (SQL filter) + Stage 2 (vector search, top K)
        rows = conn.execute(
            '''SELECT id, company_name, interest_manifesto,
                      1 - (interest_embedding <=> %s) AS score
               FROM agents
               WHERE is_active AND id <> %s
               ORDER BY interest_embedding <=> %s
               LIMIT %s''',
            (vec, author_id, vec, settings.top_k),
        ).fetchall()
        candidates = [
            {'id': r[0], 'name': r[1], 'manifesto': r[2], 'vector_score': float(r[3])}
            for r in rows
        ]
        ids = [c['id'] for c in candidates]
        muted, boosted = _subscription_effects(conn, ids, text)
        multipliers = _engagement_multipliers(conn, ids)

    # Stage 3: rerank, then apply subscriptions, feedback and trust
    ranked = rerank(text, candidates)
    threshold = settings.final_threshold if settings.cohere_api_key else settings.vector_only_threshold
    results = []
    for cand, base in ranked:
        note = ''
        if cand['id'] in muted:
            print(f'  muted   {cand["name"]}')
            continue
        score = base
        if cand['id'] in boosted:
            score += FOLLOW_BOOST
            note = ' +follow'
        score = min(1.0, score * multipliers.get(cand['id'], 1.0) * author_trust)
        print(f'  score {score:.3f} (base {base:.3f}{note}) {cand["name"]}')
        results.append((cand, score))
    results.sort(key=lambda pair: pair[1], reverse=True)
    return [(c, s) for c, s in results if s >= threshold][: settings.max_notify]