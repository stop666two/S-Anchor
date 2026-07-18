import base64
import io
import os
import uuid

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel

from core.config import WatermarkConfig
from core.pipeline import run_embed, run_extract
from core.watermark import calc_capacity
from core.watermarks import WatermarkSpec, list_types

app = FastAPI(title='Watermark Core Engine', version='2.0.0')


class WatermarkSpecModel(BaseModel):
    type: str
    text: str = ''
    alpha: float | None = None
    delta: float | None = None
    level: int | None = None
    sync: bool | None = None
    bch: bool | None = None
    opacity: float | None = None
    x: int | None = None
    y: int | None = None
    font_size: int | None = None
    rotation: int | None = None
    seed: int | None = None
    strength: float | None = None
    spread_factor: int | None = None
    r_min: float | None = None
    r_max: float | None = None
    n_bits: int | None = None
    password: str | None = None


class EmbedRequest(BaseModel):
    image_b64: str
    watermarks: list[WatermarkSpecModel]


class ExtractRequest(BaseModel):
    image_b64: str
    watermarks: list[WatermarkSpecModel]


class EmbedResponse(BaseModel):
    image_b64: str
    results: list[dict] = []
    job_id: str = ''


class ExtractResponse(BaseModel):
    results: list[dict] = []
    job_id: str = ''


def _to_spec(m: WatermarkSpecModel) -> WatermarkSpec:
    params = {k: v for k, v in m.model_dump(exclude={'type', 'text'}).items() if v is not None}
    return WatermarkSpec(type=m.type, text=m.text, **params)


@app.post('/api/embed')
def embed(req: EmbedRequest):
    try:
        raw = base64.b64decode(req.image_b64)
        img = Image.open(io.BytesIO(raw)).convert('RGB')
    except Exception as e:
        return JSONResponse(status_code=400, content={'error': f'Invalid image: {e}'})

    specs = [_to_spec(m) for m in req.watermarks]
    try:
        result_img, results = run_embed(img, specs)
    except ValueError as e:
        return JSONResponse(status_code=400, content={'error': str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': f'Embed failed: {e}'})

    buf = io.BytesIO()
    result_img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode()
    return EmbedResponse(image_b64=b64, results=results, job_id=uuid.uuid4().hex[:12])


@app.post('/api/extract')
def extract(req: ExtractRequest):
    try:
        raw = base64.b64decode(req.image_b64)
        img = Image.open(io.BytesIO(raw)).convert('RGB')
    except Exception as e:
        return JSONResponse(status_code=400, content={'error': f'Invalid image: {e}'})

    specs = [_to_spec(m) for m in req.watermarks]
    try:
        results = run_extract(img, specs)
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': f'Extract failed: {e}'})

    return ExtractResponse(results=results, job_id=uuid.uuid4().hex[:12])


@app.get('/api/watermark-types')
def watermark_types():
    return {'types': list_types()}


@app.get('/api/capacity')
def capacity(width: int = 256, height: int = 256, level: int = 2, sync_enabled: bool = True, bch_enabled: bool = True):
    config = WatermarkConfig(level=level, sync_enabled=sync_enabled, bch_enabled=bch_enabled)
    return calc_capacity(width, height, config)


@app.get('/api/health')
def health():
    return {'status': 'ok', 'engine': 'pipeline-v2'}


if __name__ == '__main__':
    port = int(os.environ.get('WATERMARK_PORT', '9001'))
    uvicorn.run(app, host='127.0.0.1', port=port, log_level='info')
