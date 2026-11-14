import cohere
from app.config import settings

def rerank(query: str, candidates: list[dict]) -> list[tuple[dict, float]]:
    '''Return (candidate, score) pairs. Falls back to vector score without a Cohere key.'''
    if not settings.cohere_api_key or not candidates:
        return [(c, c['vector_score']) for c in candidates]
    co = cohere.ClientV2(api_key=settings.cohere_api_key)
    res = co.rerank(
        model='rerank-v3.5',
        query=query,
        documents=[c['manifesto'] for c in candidates],
        top_n=len(candidates),
    )
    return [(candidates[r.index], r.relevance_score) for r in res.results]