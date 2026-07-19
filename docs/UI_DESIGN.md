# S-ANCHOR UI Design

> **Style:** Claude Warm Cream Editorial
> **Palette:** Cream canvas + Coral accent + Dark navy technical surfaces

## Color System

| Token | Hex | Usage |
|-------|-----|-------|
| `--canvas` | `#faf9f5` | Main page background, warm cream |
| `--surface-soft` | `#f5f0e8` | Soft section backgrounds, parameter groups |
| `--surface-card` | `#efe9de` | Card backgrounds |
| `--surface-dark` | `#181715` | Technical panels (preview, comparison, log) |
| `--surface-dark-elevated` | `#252320` | Elevated dark surfaces |
| `--primary` | `#cc785c` | Coral — CTAs, active buttons, accents |
| `--primary-active` | `#a9583e` | Coral hover/press state |
| `--ink` | `#141413` | Primary text (warm near-black) |
| `--body` | `#3d3d3a` | Body text |
| `--muted` | `#6c6a64` | Secondary text, labels |
| `--muted-soft` | `#8e8b82` | Captions, fine print |
| `--hairline` | `#e6dfd8` | Borders, dividers |
| `--on-primary` | `#ffffff` | Text on coral buttons |
| `--on-dark` | `#faf9f5` | Text on dark panels |
| `--success` | `#5db872` | Status indicators |
| `--error` | `#c64545` | Error states |

## Typography

| Level | Font | Size | Weight | Use |
|-------|------|------|--------|-----|
| UI Labels | Inter | 11-13px | 500 | Panel headers, buttons |
| Values | JetBrains Mono | 15-18px | 500 | Slider values, metrics |
| Body | Inter | 12-14px | 400 | Log output, descriptions |
| Log Mono | JetBrains Mono | 12px | 400 | Terminal log |

## Layout

```
┌──────────────────────────────────────────────────────┐
│ Status Bar: [● ONLINE] EMBED | EXTRACT  [ZH|EN|RU]  │
├──────────────────────────────────────────────────────┤
│  ┌─ Left Column (cream canvas) ──┐ ┌─ Right Column ─┐│
│  │  CARRIER                       │ │  PARAMETERS   ││
│  │  ┌─ Drop zone (dashed) ────┐  │ │  (cream cards) ││
│  │  │  + Drop image or click  │  │ │               ││
│  │  └─────────────────────────┘  │ │  ┌──────────┐ ││
│  │  filename | 256x256 | 12KB   │ │  │ EMBED    │ ││
│  │                               │ │  └──────────┘ ││
│  │  PREVIEW                      │ └──────────────┘│
│  │  ┌─ Dark panel ──────────┐   │                   │
│  │  │  [canvas / extract]   │   │                   │
│  │  └───────────────────────┘   │                   │
│  └──────────────────────────────┘                   │
│                                                      │
│  COMPARISON (dark panel)                             │
│  ┌──────────────────────────────────────────────┐   │
│  │  FOUND 4/4 [TYPE] content                    │   │
│  │  PSNR  SSIM  BITS  STATUS                    │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  LOG (dark panel)                                    │
│  ┌──────────────────────────────────────────────┐   │
│  │  [HH:MM:SS] >>> message                      │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

## Components

- **Buttons:** Inter 11px, 500 weight, 8px border-radius, `--primary` accent when active
- **Sliders:** Thin 3px track, 14px coral circular thumb
- **Cards:** `--surface-soft` or `--surface-dark` background, 8-12px border-radius
- **Dark panels:** Preview canvas, comparison view, log — all use `--surface-dark`
- **Modals:** Center-aligned overlay with `backdrop-filter: blur(4px)`

## Responsive

- **> 768px:** Two-column grid
- **< 768px:** Single column, stacked
