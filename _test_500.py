"""Replicate the 500 error scenario."""
import json, sys
sys.path.insert(0, r'D:\administrator\Documents\project\S-Anchor\python-core')
import numpy as np
from PIL import Image
from core.pipeline import run_embed, run_extract
from core.watermarks import WatermarkSpec

# Load the example JSON
with open(r'D:\administrator\Documents\project\S-Anchor\frontend\watermarks.example.json') as f:
    cfg = json.load(f)

# Build specs from JSON
embed_specs = []
for w in cfg['watermarks']:
    kwargs = {'type': w['type'], 'text': w['text']}
    for k, v in w.items():
        if k in ('type', 'text'):
            continue
        kwargs[k] = v
    embed_specs.append(WatermarkSpec(**kwargs))

# Embed
img = Image.fromarray(np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8), 'RGB')
try:
    result, res = run_embed(img, embed_specs)
    print(f'Embedded {len(res)} types')
except Exception as e:
    print(f'Embed ERROR: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Extract (simulate the frontend request)
extract_specs = []
for w in cfg['watermarks']:
    kwargs = {'type': w['type']}
    if w['type'] == 'freq':
        kwargs['delta'] = 36
        kwargs['level'] = 1  # from import
        kwargs['sync'] = w.get('sync', False)
        kwargs['bch'] = w.get('bch', False)
    if w.get('password'):
        kwargs['password'] = 'STOP666'  # from extract panel
    extract_specs.append(WatermarkSpec(**kwargs))

try:
    ext = run_extract(result, extract_specs)
    print(f'Extracted {len(ext)} types:')
    for r in ext:
        print(f'  [{r["type"]}] text="{r.get("text","")[:20]}"')
except Exception as e:
    print(f'Extract ERROR: {e}')
    import traceback
    traceback.print_exc()
