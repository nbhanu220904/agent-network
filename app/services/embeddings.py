from google import genai
from google.genai import types
from app.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)

def embed(text: str, kind: str = 'document') -> list[float]:
    '''kind is 'document' for stored text (agent interests) or 'query' for incoming posts.'''
    task = 'RETRIEVAL_QUERY' if kind == 'query' else 'RETRIEVAL_DOCUMENT'
    result = _client.models.embed_content(
        model='gemini-embedding-001',
        contents=text,
        config=types.EmbedContentConfig(task_type=task, output_dimensionality=1536),
    )
    return result.embeddings[0].values  # 1536 numbers