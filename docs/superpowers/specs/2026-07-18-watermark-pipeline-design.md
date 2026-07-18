# Multi-Type Watermark Pipeline Design

> **Status:** Design Approved
> **Date:** 2026-07-18

---

## 1. Architecture

The system is refactored from a single-algorithm architecture to a **watermark pipeline**:

```
                    ┌───────────────────┐
                    │  Pipeline (有序)   │
                    │  embed_order[]    │
                    │  extract_order[]  │
                    └───────┬───────────┘
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
        ┌────────┐   ┌────────┐    ┌──────────┐
        │ freq   │   │ lsb    │    │ visible  │ ...
        │ (DWT..)│   │(空间)  │    │ (可见)   │
        └────────┘   └────────┘    └──────────┘
```

Each watermark type implements a common interface:

```python
class WatermarkType(ABC):
    type_id: str                         # unique key
    name: str                            # display name

    @abstractmethod
    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        ...

    @abstractmethod
    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        ...

    def embed_order(self) -> int:        # lower = earlier
        return 50

    def extract_order(self) -> int:      # visible done first during extract
        return 50
```

## 2. Watermark Types

### 2.1 `freq` — Frequency Domain (Existing)
- **Algorithm:** DWT(Haar) → DCT(8×8 block) → SVD → QIM → BCH(15,7)
- **File:** `core/watermarks/freq.py` (refactored from `core/watermark.py`)
- **Robustness:** ★★★★
- **Capacity:** ~10 bytes (256px, sync+bch)
- **embed_order:** 10 (applied first)
- **extract_order:** 60 (extracted last)

### 2.2 `dft` — DFT Phase Modulation
- **Algorithm:** FFT → embed in phase component of mid-frequencies
- **File:** `core/watermarks/dft.py`
- **Robustness:** ★★★★★ (rotation, scaling, translation invariant)
- **Capacity:** ~4 bytes
- **embed_order:** 20
- **extract_order:** 50
- **Key technique:** DFT magnitude is shift-invariant; phase is robust to geometric attacks

### 2.3 `spread` — Spread Spectrum
- **Algorithm:** Modulate watermark bits with PN sequence, add across whole image
- **File:** `core/watermarks/spread.py`
- **Robustness:** ★★★★★ (very robust, survives most attacks)
- **Capacity:** ~2 bytes
- **embed_order:** 30
- **extract_order:** 40

### 2.4 `patchwork` — Statistical Patchwork
- **Algorithm:** Split image into random patch pairs, shift luminance statistics
- **File:** `core/watermarks/patchwork.py`
- **Robustness:** ★★★ (good against JPEG)
- **Capacity:** ~8 bytes
- **embed_order:** 40
- **extract_order:** 30

### 2.5 `lsb` — LSB Steganography
- **Algorithm:** Replace LSB of pixel values
- **File:** `core/watermarks/lsb.py`
- **Robustness:** ★ (destroyed by compression/resize)
- **Capacity:** ★★★★★ (high, ~image_w×image_h/8 bytes)
- **embed_order:** 50
- **extract_order:** 20

### 2.6 `visible` — Visible Overlay
- **Algorithm:** Draw text or image on top of carrier with configurable opacity/position
- **File:** `core/watermarks/visible.py`
- **Robustness:** N/A (visible by design)
- **Capacity:** N/A
- **embed_order:** 60 (always last)
- **extract_order:** 10 (always first)
- **Note:** This is an overlay, not a hidden watermark

## 3. Pipeline Engine

**File:** `core/pipeline.py`

```python
def run_embed(carrier: Image.Image, watermark_specs: list[WatermarkSpec]) -> tuple[Image.Image, dict]:
    """Apply multiple watermark types sequentially."""

def run_extract(stego: Image.Image, watermark_specs: list[WatermarkSpec]) -> list[ExtractResult]:
    """Extract multiple watermark types in reverse order."""
```

## 4. API Changes

### POST /api/embed

```json
{
  "image_b64": "...",
  "watermarks": [
    {"type": "freq", "text": "secret", "level": 2, "bch": true, "sync": true, "alpha": 0.05, "delta": 36},
    {"type": "lsb", "text": "large hidden message..."},
    {"type": "visible", "text": "S-ANCHOR", "opacity": 0.3, "x": 50, "y": 50}
  ]
}
```

Response changes:
- `results[]` array with per-type result (psnr, bits, etc.)
- `image_b64` is the final composited image
- `pipeline_log[]` shows what was applied in what order

### POST /api/extract

```json
{
  "image_b64": "...",
  "watermarks": [
    {"type": "lsb"},
    {"type": "freq", "level": 2, "bch": true, "sync": true, "delta": 36},
    {"type": "visible"}
  ]
}
```

Response: array of extraction results per watermark type.

### POST /api/capacity (Extended)

Accepts watermark specs array and returns per-type and total capacity.

### GET /api/watermark-types

Returns list of available watermark types with their metadata (name, description, params schema, capacity estimate).

## 5. Frontend Changes

### Watermark list redesign
- Each watermark entry shows: type icon + text preview + order index
- "Add Watermark" → shows type selector dropdown
- Selecting type changes parameter panel dynamically

### Parameter panel
- Dynamic form fields based on selected watermark type
- Shared params (text, position, opacity) shown when applicable
- Type-specific params (level, delta, alpha for freq)

### Pipeline visualization
- In the parameters panel, show "PIPELINE" section
- List all watermarks in embed order with numbered steps
- Drag to reorder (where ordering is meaningful)

### Capacity display
- Show per-type and total capacity
- Color-coded warning when approaching/over limit

## 6. File Structure

```
python-core/
  core/
    __init__.py
    config.py                    # + WatermarkSpec dataclass
    pipeline.py                  # NEW: pipeline orchestrator
    watermark.py                 # KEEP as legacy wrapper for freq-only
    metrics.py
    bch_codec.py
    sync_pattern.py
    watermarks/
      __init__.py                # NEW: registry
      freq.py                    # MOVED: from core/watermark.py
      dft.py                     # NEW
      spread.py                  # NEW
      patchwork.py               # NEW
      lsb.py                     # NEW
      visible.py                 # NEW
  server.py                      # MODIFIED: multi-type API
```

## 7. Testing

| Test | Scope |
|------|-------|
| Each type: embed → extract roundtrip | Unit per type |
| Each type: non-destructive (PSNR/SSIM) | Unit per type |
| Multi-type pipeline roundtrip | Integration |
| Capacity exceeded → error | Integration |
| Frontend type selection | E2E |

## 8. Implementation Order

1. **Core refactor**: Create `watermarks/__init__.py` registry, `WatermarkSpec` dataclass, abstract `BaseWatermark`
2. **Move `freq`** to `watermarks/freq.py`
3. **Build `lsb`** — simplest new type, validates architecture
4. **Build `visible`** — validates overlay mechanics
5. **Build `patchwork`** — statistical domain
6. **Build `dft`** — geometric robustness
7. **Build `spread`** — high robustness
8. **Build `pipeline.py`** — orchestrator
9. **Update `server.py`** — multi-type API
10. **Update Go mediator** — proxy changes
11. **Update frontend** — dynamic type selection + pipeline viz
12. **Full integration tests**

---

## 9. Architecture Decisions

### Why embed order ≠ extract order?
Visible watermarks are destructive (they overlay on top). During extraction, we need to detect these first before attempting hidden watermark extraction. Similarly, LSB modifies the lowest bits, which freq/spread/dft/patchwork don't touch, so LSB is applied later in embed but extracted earlier.

### Why not just use a single `embed_order` / `extract_order` (simple sort)?
Because embed and extract traverse in opposite directions. The first embedded watermark is the hardest to detect (it's buried under all subsequent modifications). So extract must work backwards: detect visible first, remove it, then LSB, etc.

### New params for freq type
The freq type gains optional `visible_text` and `visible_opacity` params for convenience, but the `visible` type should be preferred for clarity.
