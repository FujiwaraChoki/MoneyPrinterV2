// _base_bold.typ — Bold Playful template family
// Aesthetic: electric blue + hot pink, chunky type, color-block sections
// Best for: ADHD planners, teacher resources, fitness logs, social media calendars

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
  let hf = resolve-font(doc.at("font_heading", default: "lato"))
  let bf = resolve-font(doc.at("font_body",    default: "DM Sans 9pt"))
  (
    family:       "bold-playful",
    primary:      rgb(doc.at("primary",   default: "#4361EE")),  // electric blue
    secondary:    rgb(doc.at("secondary", default: "#F72585")),  // hot pink
    bg:           rgb(doc.at("bg",        default: "#FFFFFF")),
    dark:         rgb("#1A1A2E"),
    muted:        rgb("#6B7280"),
    line-col:     rgb("#E5E7EB"),
    mid:          rgb("#4B5563"),
    heading-font: hf,
    body-font:    bf,
    // bold extras
    header-bg:    rgb(doc.at("primary", default: "#4361EE")),
    tint:         rgb("#EEF0FD"),
  )
}

// ── Layout constants ───────────────────────────────────────────────────────────
#let _header-h   = 0.85in
#let _stripe-h   = 5pt
#let _footer-h   = 1.1in
#let _content-h  = 11in - _header-h - _stripe-h - _footer-h
#let _pad-x      = 0.45in

// ── Header ─────────────────────────────────────────────────────────────────────
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
      #grid(
        columns: (1.25in, 1fr, 1in),
        align: (left + horizon, center + horizon, right + horizon),
        gutter: 0pt,
        text(size: 7pt, font: cfg.body-font, fill: cfg.secondary, weight: "bold")[#upper(title-theme)],
        text(size: 16pt, font: cfg.heading-font, fill: white, weight: "black")[#upper(page-title)],
        text(size: 7pt, font: cfg.body-font, fill: white)[#str(page-num) / #str(page-total)],
      )
    ]
    #v(1fr)
  ]
  rect(width: 100%, height: _stripe-h, fill: cfg.secondary)
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

// ── Footer ─────────────────────────────────────────────────────────────────────
#let render-footer(cfg) = block(
  width: 100%,
  height: _footer-h,
  fill: cfg.bg,
  inset: 0pt,
)[
  #pad(x: _pad-x)[
    #line(length: 100%, stroke: 1.5pt + cfg.primary)
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
  size: 7pt, font: cfg.body-font, fill: cfg.primary, tracking: 0.15em, weight: "bold",
)[#upper(t)]

#let gold-rule(cfg) = line(length: 100%, stroke: 1.5pt + cfg.primary)

#let writing-line(cfg) = line(length: 100%, stroke: (paint: cfg.line-col, thickness: 0.5pt))

#let writing-lines(n, cfg) = {
  for i in range(n) {
    writing-line(cfg)
    if i < n - 1 { v(0.215in) }
  }
}

#let checkbox(cfg) = box(
  width: 9pt, height: 9pt,
  stroke: 1.5pt + cfg.primary,
  fill: none, radius: 2pt,
)[]

#let gold-badge(n, cfg) = box(
  width: 16pt, height: 16pt,
  fill: cfg.secondary, radius: 3pt,
)[
  #set align(center + horizon)
  #text(size: 7.5pt, font: cfg.body-font, fill: white, weight: "black")[#n]
]

#let three-col-footer(h1, h2, h3, cfg, lines: 3) = {
  gold-rule(cfg)
  v(7pt)
  let col(heading) = pad(x: 0.08in)[
    #block(height: 0.22in, fill: cfg.tint, radius: 3pt, inset: (x: 6pt, y: 4pt))[
      #section-label(heading, cfg)
    ]
    #v(6pt)
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
