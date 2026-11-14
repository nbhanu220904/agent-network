import json
import httpx
import os

# API = 'http://localhost:8000/api/v1'
API = os.getenv('API_URL', 'http://localhost:8000') + '/api/v1'

AGENTS = {
    'swiggy': ('Swiggy', 'Food Delivery', 'Interested in payment partnerships, bank card offers, festive promotions and restaurant discounts.'),
    'phonepe': ('PhonePe', 'Payments & Fintech', 'Interested in e-commerce promotions, food delivery festive discounts, UPI payment partnerships and merchant cashback.'),
    'flipkart': ('Flipkart', 'E-commerce', 'Interested in festive sales, payment offers, logistics partnerships and consumer promotions.'),
    'hdfc': ('HDFC Bank', 'Banking', 'Interested in credit and debit card offers, card partnerships with food delivery and e-commerce, EMI and cashback tie-ups during festive seasons.'),
    'bajaj': ('Bajaj Auto', 'Automotive', 'Interested in motorcycle launches, vehicle financing, dealership networks and auto component suppliers. Not interested in food, delivery or retail offers.'),
}

creds = {}
for key, (name, industry, manifesto) in AGENTS.items():
    r = httpx.post(f'{API}/agents/register',
                   headers={'X-Admin-Token': os.getenv('REGISTRATION_TOKEN', '')},
                   json={
                       'company_name': name,
                       'industry_category': industry,
                       'webhook_url': f'http://localhost:9001/{key}/events',
                       'interest_manifesto': manifesto,
                   }, timeout=90)
    r.raise_for_status()
    creds[key] = r.json()
    print('registered', name, creds[key]['agent_id'])

SUBS = {
    'hdfc': ('follow', 'festive-card-offers', ['card', 'cashback', 'festive', 'discount']),
    'phonepe': ('follow', 'payments-offers', ['upi', 'cashback', 'payment']),
    'bajaj': ('mute', 'food-delivery', ['delivery', 'restaurant', 'food']),
}
for key, (kind, topic, keywords) in SUBS.items():
    r = httpx.post(f'{API}/agents/me/subscriptions',
                   json={'kind': kind, 'topic': topic, 'keywords': keywords},
                   headers={'X-API-Key': creds[key]['api_key']}, timeout=30)
    r.raise_for_status()
    print('subscription', key, kind, topic)

json.dump(creds, open('mock_agents/credentials.json', 'w'), indent=2)