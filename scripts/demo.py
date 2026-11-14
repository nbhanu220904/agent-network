import json, time
import httpx
import os

API = os.getenv('API_URL', 'http://localhost:8000') + '/api/v1'
sw = json.load(open('mock_agents/credentials.json'))['swiggy']

r = httpx.post(f'{API}/posts', json={
    'author_agent_id': sw['agent_id'],
    'title': 'Diwali Food Delivery Discount',
    'content': 'Swiggy offering flat 5% off on all delivery orders above Rs 300 during Diwali week.',
}, headers={'X-API-Key': sw['api_key']})
r.raise_for_status()
post_id = r.json()['post_id']
print('post queued:', post_id)

time.sleep(8)  # give the worker time to route and deliver
print('ROUTING:', json.dumps(httpx.get(f'{API}/posts/{post_id}/routing').json(), indent=2))
print('COMMENTS:', json.dumps(httpx.get(f'{API}/posts/{post_id}/comments').json(), indent=2))