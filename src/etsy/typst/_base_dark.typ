// _base_dark.typ — Dark Luxury template family
// Aesthetic: near-black background sections, gold accents, heavy serif headers
// Best for: executive planners, focus/productivity, reading trackers, evening routines

// ── Font resolution (same map as _base.typ) ───────────────────────────────────
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
    family:       "dark-luxury",
    primary:      rgb(doc.at("primary",    default: "#1A1A2E")),
    secondary:    rgb(doc.at("secondary",  default: "#C9A84C")),
    bg:           rgb("#FAF8F4"),
    dark:         rgb("#0D0D0D"),
    muted:        rgb("#8A8A7A"),
    line-col:     rgb("#2C2C3E"),
    mid:          rgb("#4A4A5E"),
    heading-font: hf,
    body-font:    bf,
    // dark-luxury extras
    header-bg:    rgb("#0D0D1A"),
    accent-stripe: rgb(doc.at("secondary", default: "#C9A84C")),
  )
}

// ── Layout constants ───────────────────────────────────────────────────────────
#let _header-h   = 0.9in
#let _stripe-h   = 6pt
#let _footer-h   = 1.0in
#let _content-h  = 11in - _header-h - _stripe-h - _footer-h
#let _pad-x      = 0.5in

// ── Page header (deep dark + thick gold stripe) ────────────────────────────────
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
        columns: (1.4in, 1fr, 1in),
        align: (left + horizon, center + horizon, right + horizon),
        gutter: 0pt,
        text(size: 7.5pt, font: cfg.body-font, fill: cfg.secondary)[#upper(title-theme)],
        text(size: 16pt, font: "Playfair Display", weight: "bold")[#page-title],
        text(size: 7.5pt, font: cfg.body-font, fill: cfg.secondary)[#str(page-num) / #str(page-total)],
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

// ── Page footer ────────────────────────────────────────────────────────────────
#let render-footer(cfg) = block(
  width: 100%,
  height: _footer-h,
  fill: cfg.header-bg,
  inset: 0pt,
)[
  #pad(x: _pad-x, top: 0.18in)[
    #set text(size: 7pt, fill: cfg.secondary, font: cfg.body-font)
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
  size: 6.5pt, font: cfg.body-font, fill: cfg.secondary, tracking: 0.28em,
)[#upper(t)]

#let gold-rule(cfg) = line(length: 100%, stroke: 1.5pt + cfg.secondary)

#let writing-line(cfg) = {
  line(length: 100%, stroke: 0.4pt + rgb("#C0BDB5"))
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
  fill: none, radius: 1pt,
)[]

#let gold-badge(n, cfg) = box(
  width: 16pt, height: 16pt,
  fill: cfg.secondary, radius: 50%,
)[
  #set align(center + horizon)
  #text(size: 7.5pt, font: cfg.body-font, fill: cfg.header-bg, weight: "bold")[#n]
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
