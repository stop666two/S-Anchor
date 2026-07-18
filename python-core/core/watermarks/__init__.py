from abc import ABC, abstractmethod
from typing import Any
from PIL import Image
from numpy.typing import NDArray


class WatermarkSpec:
    type: str
    text: str = ''
    params: dict = None

    def __init__(self, type: str, text: str = '', **kwargs):
        self.type = type
        self.text = text
        self.params = kwargs or {}

    def to_dict(self) -> dict:
        return {'type': self.type, 'text': self.text, **self.params}


class BaseWatermark(ABC):
    type_id: str = ''
    name: str = ''

    @abstractmethod
    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        pass

    @abstractmethod
    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        pass

    def embed_order(self) -> int:
        return 50

    def extract_order(self) -> int:
        return 50


_registry: dict[str, BaseWatermark] = {}


def register(wm: BaseWatermark):
    _registry[wm.type_id] = wm


def get(type_id: str) -> BaseWatermark | None:
    return _registry.get(type_id)


def list_types() -> list[dict]:
    return [
        {
            'type_id': wm.type_id,
            'name': wm.name,
            'embed_order': wm.embed_order(),
            'extract_order': wm.extract_order(),
        }
        for wm in sorted(_registry.values(), key=lambda x: x.embed_order())
    ]


def sorted_for_embed() -> list[BaseWatermark]:
    return sorted(_registry.values(), key=lambda x: x.embed_order())


def sorted_for_extract() -> list[BaseWatermark]:
    return sorted(_registry.values(), key=lambda x: x.extract_order())
