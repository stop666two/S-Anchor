# S-ANCHOR — 频域盲水印系统 / Frequency Domain Blind Watermark System

> 多层水印引擎：在图片中嵌入/提取 10 种水印，三层架构。
> Multi-layered watermark engine: embed/extract 10 types of watermarks in images.

---

## 系统架构 / Architecture

```
浏览器 / Browser (HTML/CSS/JS) 
    → Go 中介层 / Go Mediator (限流 + 代理 / rate limit + proxy) 
        → Python 核心 / Python Core (流水线 + 10 种算法 / pipeline + 10 algorithms)
```

---

## 快速启动 / Quick Start

**Windows:**
```bash
# 一键启动所有服务 / Start all services
start.bat

# 或者手动启动 / Or manually:
cd python-core && py -3 -m uvicorn server:app --host 127.0.0.1 --port 9001
cd go-mediator && mediator.exe
cd frontend && py -3 -m http.server 8000 --bind 127.0.0.1
```

**访问地址 / URLs:**
- 前端界面 / Frontend: http://127.0.0.1:8000
- Go API 接口: http://127.0.0.1:8080
- Python API 接口: http://127.0.0.1:9001

---

## 水印类型 / Watermark Types (10 种)

| 类型 / Type | 算法 / Algorithm | 鲁棒性 / Robust | 容量 / Capacity | BCH | 加密 / Encrypt |
|-------------|-----------------|-----------------|-----------------|-----|---------------|
| `freq` | DWT-DCT-SVD-QIM | ★★★★ | ~10B | ✅ | ❌ |
| `dft` | DFT 幅值 QIM | ★★★★ | ~10B | ✅ | ❌ |
| `dwtsvd` | DWT-SVD LL 子带 | ★★★ | ~10B | ✅ | ❌ |
| `dct_block` | DCT 中频 QIM | ★★★ | ~50B | ✅ | ✅ |
| `svd` | 8x8 块 SVD QIM | ★★★ | ~50B | ✅ | ✅ |
| `spread` | 扩频 / Spread spectrum | ★★★★★ | ~2B | ❌ | ❌ |
| `patchwork` | 统计 Patch | ★★★ | ~8B | ❌ | ❌ |
| `lsb` | LSB 隐写 | ★ | 无限 / ∞ | ❌ | ✅ |
| `reversible` | 可逆 / Reversible | ★ | 无限 / ∞ | ❌ | ✅ |
| `visible` | 可见文字叠加 / Text overlay | — | — | ❌ | ❌ |

---

## 密码保护 / Password Protection

4 种类型支持 PBKDF2 派生密钥加密：
**lsb、svd、dct_block、reversible**

**工作流程 / Workflow:**

1. 导入 `.pass.json` 配置文件（水印含有密码）
2. 点击 EMBED 嵌入（密码自动用于加密）
3. 切换到 EXTRACT 模式
4. **手动在密码框输入密码** / Manually enter the password
5. 点击 EXTRACT

> 不输入密码 → 显示 `[NEEDS PASSWORD]`
> 输入错误密码 → 显示 `[WRONG PASSWORD]`

---

## 示例 JSON 文件 / Example JSON Files

| 文件 / File | 类型 / Types | 密码 / Passwords |
|-------------|-------------|-----------------|
| `watermarks.example.json` | freq, dft, dct_block, svd | dct_block + svd |
| `watermarks.nopass.json` | freq, dft, dct_block, svd | 无 / none |
| `watermarks.fragile.pass.json` | lsb, reversible, visible | lsb + reversible |
| `watermarks.fragile.nopass.json` | lsb, reversible, visible | 无 / none |

---

## 测试 / Testing

```bash
# Python 测试 (40 个) / Python tests (40)
cd python-core && py -3 -m pytest ../tests/ -v

# Go 测试 (13 个) / Go tests (13)
cd go-mediator && go test ./... -v

# Python 代码风格检查 / Lint
cd python-core && py -3 -m ruff check .
```

---

## 开发 / Development

**项目结构 / Project Structure:**
```
S-Anchor/
├── frontend/              # 前端静态文件 / Frontend static files
│   ├── index.html         # 主页面 / Main page
│   ├── style.css          # 样式 / Styles (Claude 温暖奶油风)
│   ├── state.js           # 全局状态 + i18n / Global state
│   ├── ui.js              # UI 交互 / UI interactions
│   └── embed-extract.js   # 嵌入/提取逻辑 / Embed/Extract logic
├── go-mediator/           # Go 中介层 / Go mediator
│   ├── main.go            # HTTP 服务 / HTTP server
│   └── main_test.go       # 测试 / Tests
├── python-core/           # Python 核心引擎 / Python core
│   ├── server.py          # FastAPI 服务
│   ├── core/
│   │   ├── pipeline.py    # 嵌入/提取流水线
│   │   ├── crypto.py      # 加密 / Encryption
│   │   ├── bch_codec.py   # BCH 纠错码 / Error correction
│   │   └── watermarks/    # 10 种水印实现
│   └── requirements.txt
├── tests/                 # Python 测试
├── docs/                  # 文档 / Documentation
│   └── UI_DESIGN.md       # UI 设计规范
└── README.md
```

---

## 许可证 / License

MIT
