// _base.typ — Day Designer-inspired shared utilities
// Palette: forest green + warm gold + cream

// ── Font resolution ────────────────────────────────────────────────────────────
#let _font-map = (
  "helvetica-bold": "Lato",
  "helvetica": "Lato",
  "georgia-bold": "Playfair Display",
  "georgia": "Playfair Display",
  "trebuchet-bold": "Lato",
  "trebuchet": "Lato",
  "times-bold": "Playfair Display",
  "times-roman": "Playfair Display",
  "courier-bold": "Lato",
  "courier": "Lato",
  "playfair display": "Playfair Display",
  "playfair display bold": "Playfair Display",
  "lato": "Lato",
  "lato bold": "Lato",
  "montserrat": "Lato",
  "montserrat bold": "Lato",
  "montserrat semi bold": "Lato",
  "montserrat regular": "Lato",
  "open sans": "DM Sans 9pt",
  "open sans regular": "DM Sans 9pt",
  "open sans bold": "DM Sans 9pt",
  "inter": "DM Sans 9pt",
  "inter regular": "DM Sans 9pt",
  "inter bold": "Lato",
  "roboto": "DM Sans 9pt",
  "roboto regular": "DM Sans 9pt",
  "dm sans": "DM Sans 9pt",
  "dm-sans": "DM Sans 9pt",
  "dmsans": "DM Sans 9pt",
  "dm sans 9pt": "DM Sans 9pt",
)

#let resolve-font(name) = {
  let key = lower(str(name))
  _font-map.at(key, default: "DM Sans 9pt")
}

// ── Configuration builder ──────────────────────────────────────────────────────
#let make-config(doc) = {
  let hf = resolve-font(doc.at("font_heading", default: "playfair display"))
  let bf = resolve-font(doc.at("font_body", default: "DM Sans 9pt"))
  (
    family:       "clean-minimal",
    primary:      rgb(doc.at("primary",    default: "#2E5944")),
    secondary:    rgb(doc.at("secondary",  default: "#C9A84C")),
    bg:           rgb(doc.at("bg",         default: "#FAF7F2")),
    dark:         rgb(doc.at("text_dark",  default: "#1A1A1A")),
    muted:        rgb(doc.at("text_muted", default: "#7A7A6A")),
    line-col:     rgb(doc.at("rule_line",  default: "#D8D4CB")),
    mid:          rgb("#6B5B4E"),
    heading-font: hf,
    body-font:    bf,
  )
}

// ── Layout constants ───────────────────────────────────────────────────────────
#let _header-h   = 0.8in
#let _strip-h    = 4pt
#let _footer-h   = 1.12in
#let _content-h  = 11in - _header-h - _strip-h - _footer-h
#let _pad-x      = 0.45in

// ── Page header (primary bar + gold strip) ────────────────────────────────────
#let render-header(title-theme, page-title, page-num, page-total, cfg) = {
  block(
    width: 100%,
    height: _header-h,
    fill: cfg.primary,
    clip: true,
    inset: 0pt,
  )[
    #v(1fr)
    #pad(x: _pad-x)[
      #set text(fill: white)
      #grid(
        columns: (1.2in, 1fr, 1in),
        align: (left + horizon, center + horizon, right + horizon),
        gutter: 0pt,
        text(size: 8pt, font: cfg.body-font)[#title-theme],
        text(size: 15pt, font: "Playfair Display", weight: "bold")[#page-title],
        text(size: 8pt, font: cfg.body-font)[#str(page-num) / #str(page-total)],
      )
    ]
    #v(1fr)
  ]
  rect(width: 100%, height: _strip-h, fill: cfg.secondary)
}

// ── Content area shell (cream background with padding) ────────────────────────
#let content-area(cfg, body) = block(
  width: 100%,
  height: _content-h,
  fill: cfg.bg,
  clip: true,
  inset: 0pt,
)[
  #pad(x: _pad-x, top: 0.22in, bottom: 0.12in)[
    #body
  ]
]

// ── Page footer ────────────────────────────────────────────────────────────────
#let render-footer(cfg) = block(
  width: 100%,
  height: _footer-h,
  fill: cfg.bg,
  inset: 0pt,
)[
  #pad(x: _pad-x)[
    #line(length: 100%, stroke: 0.5pt + cfg.secondary)
    #v(5pt)
    #set text(size: 7pt, fill: cfg.muted, font: cfg.body-font)
    #grid(
      columns: (1fr, 1fr),
      align: (left, right),
      [Digital download for personal planning use],
      [MoneyPrinter+ Generator],
    )
  ]
]

// ── Utilities ──────────────────────────────────────────────────────────────────
#let section-label(t, cfg) = text(
  size: 6.5pt, font: cfg.body-font, fill: cfg.primary, tracking: 0.22em,
)[#upper(t)]

#let gold-rule(cfg) = line(length: 100%, stroke: 1.5pt + cfg.secondary)

#let writing-line(cfg) = {
  line(length: 100%, stroke: 0.4pt + cfg.line-col)
}

#let writing-lines(n, cfg) = {
  for i in range(n) {
    writing-line(cfg)
    if i < n - 1 { v(0.215in) }
  }
}

// Small open checkbox
#let checkbox(cfg) = box(
  width: 9pt, height: 9pt,
  stroke: 0.7pt + cfg.mid,
  fill: none, radius: 1pt,
)[]

// Gold circle badge with number
#let gold-badge(n, cfg) = box(
  width: 16pt, height: 16pt,
  fill: cfg.secondary, radius: 50%,
)[
  #set align(center + horizon)
  #text(size: 7.5pt, font: cfg.body-font, fill: white, weight: "bold")[#n]
]

// Three-column section footer with writing lines
#let three-col-footer(h1, h2, h3, cfg, lines: 3) = {
  gold-rule(cfg)
  v(7pt)
  let col(heading) = pad(x: 0.08in)[
    #section-label(heading, cfg)
    #v(7pt)
    #for i in range(lines) {
      writing-line(cfg)
      if i < lines - 1 { v(0.2in) }
    }
  ]
  grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 0.18in,
    col(h1), col(h2), col(h3),
  )
}
