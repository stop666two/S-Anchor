from PIL import Image, ImageDraw, ImageFont
import io
import os

from . import BaseWatermark, register


class VisibleWatermark(BaseWatermark):
    type_id = 'visible'
    name = 'Visible Overlay'

    def embed_order(self) -> int:
        return 60

    def extract_order(self) -> int:
        return 10

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        text = payload.decode('utf-8', errors='replace')
        if not text:
            return carrier, {}

        result = carrier.convert('RGBA')
        overlay = Image.new('RGBA', result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        opacity = int(params.get('opacity', 0.3) * 255)
        x_pct = params.get('x', 50)
        y_pct = params.get('y', 50)
        font_size = params.get('font_size', 48)
        rotation = params.get('rotation', 0)

        try:
            font = ImageFont.truetype('arial.ttf', font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        cx = int(result.width * x_pct / 100)
        cy = int(result.height * y_pct / 100)
        x = cx - tw // 2
        y = cy - th // 2

        txt_layer = Image.new('RGBA', result.size, (0, 0, 0, 0))
        txt_draw = ImageDraw.Draw(txt_layer)
        txt_draw.text((x, y), text, fill=(255, 255, 255, opacity), font=font)

        if rotation:
            txt_layer = txt_layer.rotate(rotation, center=(cx, cy), expand=False)

        result = Image.alpha_composite(result, txt_layer).convert('RGB')
        return result, {'text': text, 'opacity': opacity}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        return b'', {}


register(VisibleWatermark())
