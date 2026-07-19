# S-ANCHOR - Frequency Domain Blind Watermark System

> Multi-layered watermark engine: embed/extract 10 types of watermarks in images via a three-tier architecture.

## Architecture

```
Browser (HTML/CSS/JS) → Go Mediator (rate limit + proxy) → Python Core (pipeline + 10 algorithms)
```

- **Frontend:** Plain HTML+CSS+JS, no framework, dark cream editorial UI
- **Go Mediator:** HTTP reverse proxy with rate limiting, CORS validation, worker pool
- **Python Core:** FastAPI server running pipelined watermark embedding/extraction

## Watermark Types (10)

| Type | Algorithm | Robustness | Capacity | BCH | Encryption |
|------|-----------|-----------|----------|-----|------------|
| `freq` | DWT-DCT-SVD-QIM | ★★★★ | ~10B | ✅ | ❌ |
| `dft` | DFT magnitude QIM | ★★★★ | ~10B | ✅ | ❌ |
| `dwtsvd` | DWT-SVD on LL band | ★★★ | ~10B | ✅ | ❌ |
| `dct_block` | DCT mid-band QIM | ★★★ | ~50B | ✅ | ✅ |
| `svd` | 8x8 block SVD QIM | ★★★ | ~50B | ✅ | ✅ |
| `spread` | Spread spectrum | ★★★★★ | ~2B | ❌ | ❌ |
| `patchwork` | Statistical patch pairs | ★★★ | ~8B | ❌ | ❌ |
| `lsb` | LSB steganography | ★ | unlimited | ❌ | ✅ |
| `reversible` | Difference expansion | ★ | unlimited | ❌ | ✅ |
| `visible` | Text overlay | N/A | N/A | N/A | ❌ |

## Quick Start

```bash
# Start all services
start.bat

# Or manually:
cd python-core && py -3 -m uvicorn server:app --host 127.0.0.1 --port 9001
cd go-mediator && mediator.exe
cd frontend && py -3 -m http.server 8000 --bind 127.0.0.1
```

Frontend: http://127.0.0.1:8000  
Go API: http://127.0.0.1:8080  
Python API: http://127.0.0.1:9001

## Testing

```bash
# Python (40 tests)
cd python-core && py -3 -m pytest ../tests/ -v

# Go (13 tests)
cd go-mediator && go test ./... -v

# Lint
cd python-core && py -3 -m ruff check .
```

## Password Protection

4 types support AES-like encryption with PBKDF2 key derivation:
`lsb`, `svd`, `dct_block`, `reversible`

Workflow:
1. Import a `.pass.json` file (watermarks with passwords)
2. Click EMBED (password used automatically for encryption)
3. Switch to EXTRACT mode
4. **Manually enter the password** in the password field
5. Click EXTRACT

## Example JSON Files

| File | Types | Passwords |
|------|-------|-----------|
| `watermarks.example.json` | freq, dft, dct_block, svd | dct_block + svd |
| `watermarks.nopass.json` | freq, dft, dct_block, svd | none |
| `watermarks.fragile.pass.json` | lsb, reversible, visible | lsb + reversible |
| `watermarks.fragile.nopass.json` | lsb, reversible, visible | none |
