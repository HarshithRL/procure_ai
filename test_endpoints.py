#!/usr/bin/env python3
"""Test the critical new endpoints."""

import sys
import json

sys.path.insert(0, '.')
from web_app import create_app

# Create test app
app = create_app('development')
client = app.test_client()

print("=" * 60)
print("Test 1: GET /bff/model-catalog")
print("=" * 60)
try:
    resp = client.get('/bff/model-catalog?surface=chat')
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.get_json()
        print(f'Schema version: {data.get("schema_version")}')
        print(f'Profiles: {len(data.get("profiles", []))}')
        print(f'Models: {len(data.get("models", []))}')
        print('✓ Catalog endpoint works')
    else:
        print(f'Error: {resp.get_data(as_text=True)[:200]}')
except Exception as e:
    print(f'✗ Error: {type(e).__name__}: {e}')

print("\n" + "=" * 60)
print("Test 2: Check base.html has extra_js block")
print("=" * 60)
try:
    with open('web_app/templates/base.html', 'r') as f:
        content = f.read()
        if '{% block extra_js %}' in content:
            print('✓ extra_js block declared in base.html')
        else:
            print('✗ extra_js block NOT found in base.html')
except Exception as e:
    print(f'✗ Error: {e}')

print("\n" + "=" * 60)
print("Test 3: Check feedback.js exists")
print("=" * 60)
try:
    from pathlib import Path
    if Path('web_app/static/js/feedback.js').exists():
        print('✓ feedback.js exists')
        with open('web_app/static/js/feedback.js', 'r') as f:
            content = f.read()
            if 'feedback.rate' in content:
                print('✓ feedback.js has rate() function')
    else:
        print('✗ feedback.js does NOT exist')
except Exception as e:
    print(f'✗ Error: {e}')

print("\n" + "=" * 60)
print("Test 4: Check chat-stream.js has fallback handler")
print("=" * 60)
try:
    with open('web_app/static/dist/chat-stream.js', 'r') as f:
        content = f.read()
        if "event.event === 'on_chat_model_end'" in content:
            print('✓ on_chat_model_end fallback handler added')
        else:
            print('✗ on_chat_model_end handler NOT found')
        if 'loadAndRenderModelCatalog' in content:
            print('✓ loadAndRenderModelCatalog function added')
        else:
            print('✗ loadAndRenderModelCatalog NOT found')
except Exception as e:
    print(f'✗ Error: {e}')

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
