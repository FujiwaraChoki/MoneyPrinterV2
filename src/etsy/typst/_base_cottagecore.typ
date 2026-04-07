// _base_cottagecore.typ — Cottagecore/Organic template family
// Aesthetic: dusty rose + sage green, botanical dividers, soft rounded shapes
// Best for: wedding, pregnancy, garden, meal planning, gratitude journals

// ── Font resolution ─────────────────────────────────────────────────────────
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
  "lato": "Lato",
  "montserrat": "Lato",
  "open sans": "DM Sans 9pt",
  "inter": "DM Sans 9pt",
  "roboto": "DM Sans 9pt",
  "dm sans": "DM Sans 9pt",
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
    family:       "cottagecore",
    primary:      rgb(doc.at("primary",    default: "#7D9B76")),  // sage green
    secondary:    rgb(doc.at("secondary",  default: "#C9957A")),  // dusty rose
    bg:           rgb(doc.at("bg",         default: "#FDF8F3")),  // warm cream
    dark:         rgb("#2D2A27"),
    muted:        rgb("#9A8F87"),
    line-col:     rgb("#E0D5CC"),
    mid:          rgb("#8A7D75"),
    heading-font: hf,
    body-font:    bf,
    // cottagecore extras
    header-bg:    rgb(doc.at("primary", default: "#7D9B76")),
    leaf-accent:  rgb("#A8C4A2"),
  )
}

// ── Layout constants ───────────────────────────────────────────────────────────
#let _header-h   = 0.85in
#let _petal-h    = 4pt
#let _footer-h   = 1.1in
#let _content-h  = 11in - _header-h - _petal-h - _footer-h
#let _pad-x      = 0.45in

// ── Botanical rule (dotted, organic feel) ──────────────────────────────────────
#let _botanical-rule(cfg) = {
  line(length: 100%, stroke: (paint: cfg.secondary, thickness: 1pt, dash: "dotted"))
}

// ── Page header (sage green bar + rose petal strip) ────────────────────────────
#let render-header(title-theme, page-title, page-num, page-total, cfg) = {
  block(
    width: 100%,
    height: _header-h,
    fill: cfg.header-bg,
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
        text(size: 7.5pt, font: cfg.body-font, fill: cfg.leaf-accent)[#title-theme],
        text(size: 15pt, font: "Playfair Display", style: "italic")[#page-title],
        text(size: 7.5pt, font: cfg.body-font, fill: cfg.leaf-accent)[#str(page-num) / #str(page-total)],
      )
    ]
    #v(1fr)
  ]
  rect(width: 100%, height: _petal-h, fill: cfg.secondary)
}

// ── Content area ───────────────────────────────────────────────────────────────
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
    #_botanical-rule(cfg)
    #v(6pt)
    #set text(size: 7pt, fill: cfg.muted, font: cfg.body-font)
    #grid(
      columns: (1fr, 1fr),
      align: (left, right),
      [Digital download · Personal use only],
      [MoneyPrinter+ Generator],
    )
  ]
]

// ── Utilities ──────────────────────────────────────────────────────────────────
#let section-label(t, cfg) = text(
  size: 6.5pt, font: cfg.body-font, fill: cfg.primary, tracking: 0.22em, style: "italic",
)[#upper(t)]

#let gold-rule(cfg) = _botanical-rule(cfg)

#let writing-line(cfg) = {
  line(length: 100%, stroke: (paint: cfg.secondary, thickness: 0.4pt, dash: "dotted"))
}

#let writing-lines(n, cfg) = {
  for i in range(n) {
    writing-line(cfg)
    if i < n - 1 { v(0.215in) }
  }
}

#let checkbox(cfg) = box(
  width: 9pt, height: 9pt,
  stroke: 0.7pt + cfg.secondary,
  fill: none, radius: 3pt,
)[]

#let gold-badge(n, cfg) = box(
  width: 16pt, height: 16pt,
  fill: cfg.secondary, radius: 50%,
)[
  #set align(center + horizon)
  #text(size: 7.5pt, font: cfg.body-font, fill: white, weight: "bold")[#n]
]

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
