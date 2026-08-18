#!/usr/bin/env python3
"""Quick test of model catalog."""

from shared_library.model_factory.catalog import get_model_catalog

try:
    catalog = get_model_catalog(surface='chat')
    print('✓ Catalog loads OK')
    print(f'  Schema: {catalog.get("schema_version")}')
    print(f'  Surface: {catalog.get("surface")}')
    print(f'  Profiles: {len(catalog.get("profiles", []))}')
    print(f'  Models: {len(catalog.get("models", []))}')
    
    # Show first 3 profiles
    for p in catalog.get("profiles", [])[:3]:
        print(f'    - {p.get("id")}: {p.get("label")}')
    
    # Show first 3 models
    for m in catalog.get("models", [])[:3]:
        print(f'    - {m.get("id")}: {m.get("short_name")}')
        
except Exception as e:
    print(f'✗ Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
