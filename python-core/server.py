import os
import io
import base64
import uuid
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from core.config import WatermarkConfig
from core.watermark import embed_watermark, extract_watermark

app = FastAPI(title='Watermark Core Engine', version='1.0.0')


class EmbedRequest(BaseModel):
    image_b64: str = Field(..., description='Base64 encoded PNG image')
    watermark_text: str = Field(default='', description='Text watermark to embed')
    alpha: float = Field(default=0.05, ge=0.01, le=1.0)
    delta: float = Field(default=36.0, ge=1.0, le=200.0)
    level: int = Field(default=2, ge=1, le=4)
    sync_enabled: bool = True
    bch_enabled: bool = True


class ExtractRequest(BaseModel):
    image_b64: str = Field(..., description='Base64 encoded PNG stego image')
    delta: float = Field(default=36.0)
    level: int = Field(default=2)
    sync_enabled: bool = True
    bch_enabled: bool = True


class EmbedResponse(BaseModel):
    image_b64: str
    psnr: float
    ssim: float
    bits_embedded: int
    job_id: str
    level_used: int = 2


class ExtractResponse(BaseModel):
    watermark_text: str
    watermark_hex: str
    sync_found: bool
    sync_corr: float
    job_id: str


@app.post('/api/embed', response_model=EmbedResponse)
def embed(req: EmbedRequest):
    try:
        raw = base64.b64decode(req.image_b64)
        img = Image.open(io.BytesIO(raw)).convert('RGB')
    except Exception as e:
        return JSONResponse(status_code=400, content={'error': f'Invalid image: {e}'})

    config = WatermarkConfig(
        alpha=req.alpha,
        delta=req.delta,
        level=req.level,
        sync_enabled=req.sync_enabled,
        bch_enabled=req.bch_enabled,
    )

    watermark_bytes = req.watermark_text.encode('utf-8')

    try:
        result_img, metrics = embed_watermark(img, watermark_bytes, config)
    except ValueError as e:
        return JSONResponse(status_code=400, content={'error': str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': f'Embed failed: {e}'})

    buf = io.BytesIO()
    result_img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode()

    return EmbedResponse(
        image_b64=b64,
        psnr=metrics['psnr'],
        ssim=metrics['ssim'],
        bits_embedded=metrics['bits_embedded'],
        job_id=uuid.uuid4().hex[:12],
        level_used=metrics.get('level_used', req.level),
    )


@app.post('/api/extract', response_model=ExtractResponse)
def extract(req: ExtractRequest):
    try:
        raw = base64.b64decode(req.image_b64)
        img = Image.open(io.BytesIO(raw)).convert('RGB')
    except Exception as e:
        return JSONResponse(status_code=400, content={'error': f'Invalid image: {e}'})

    config = WatermarkConfig(
        delta=req.delta,
        level=req.level,
        sync_enabled=req.sync_enabled,
        bch_enabled=req.bch_enabled,
    )

    try:
        extracted_bytes, ext_info = extract_watermark(img, config=config)
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': f'Extract failed: {e}'})

    return ExtractResponse(
        watermark_text=extracted_bytes.decode('utf-8', errors='replace'),
        watermark_hex=extracted_bytes.hex(),
        sync_found=ext_info.get('sync_found', False),
        sync_corr=ext_info.get('sync_corr', 0.0),
        job_id=uuid.uuid4().hex[:12],
    )


@app.get('/api/health')
def health():
    return {'status': 'ok', 'engine': 'dwt-dct-svd'}


if __name__ == '__main__':
    port = int(os.environ.get('WATERMARK_PORT', '9001'))
    uvicorn.run(app, host='127.0.0.1', port=port, log_level='info')
