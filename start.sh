#!/bin/sh
export PORT=${PORT:-8000}
export API_BASE_URL=http://127.0.0.1:$PORT
celery -A app.workers.celery_app worker --loglevel=info --pool=solo &
uvicorn mock_agents.agent_server:app --host 127.0.0.1 --port 9001 &
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT