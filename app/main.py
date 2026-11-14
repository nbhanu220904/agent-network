from fastapi import FastAPI
from app.routers import agents, comments, engagement, posts, subscriptions

app = FastAPI(title='AI Agent Network')
app.include_router(agents.router, prefix='/api/v1')
app.include_router(posts.router, prefix='/api/v1')
app.include_router(comments.router, prefix='/api/v1')
app.include_router(subscriptions.router, prefix='/api/v1')
app.include_router(engagement.router, prefix='/api/v1')


@app.get('/health')
def health():
    return {'status': 'ok'}