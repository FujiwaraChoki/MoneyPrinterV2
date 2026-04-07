// worksheet.typ — Day Designer daily worksheet page
// Each page uses its `body` items as unique named sections (no two pages look alike)

// One named section block: label + n writing lines
#let named-section(label-text, cfg, theme, lines: 3) = {
  theme.section-label(label-text, cfg)
  v(6pt)
  for i in range(lines) {
    theme.writing-line(cfg)
    if i < lines - 1 { v(0.215in) }
  }
}

#let render-worksheet(page, product-spec, cfg, theme) = {
  let page-title  = page.at("title", default: "Daily Plan")
  let section     = page.at("section_name", default: "")
  let page-num    = page.at("page_number", default: 1)
  let page-total  = product-spec.at("page_count", default: 1)
  let title-theme = product-spec.at("title_theme", default: "Planner")
  // body items become the page's unique section labels (trim to 5)
  let body        = page.at("body", default: ())
  let sections    = if body.len() > 0 {
    body.slice(0, calc.min(body.len(), 5))
  } else {
    ("Priorities", "To Do", "Notes", "Ideas", "Follow-Up")
  }

  theme.render-header(title-theme, page-title, page-num, page-total, cfg)

  theme.content-area(cfg)[
    #grid(
      columns: (1fr, 2.3in),
      gutter: 0.25in,

      // ── LEFT COLUMN: themed named sections ──────────────────────────────
      stack(spacing: 0.18in,

        // Top 3 Focus — always first
        stack(spacing: 0pt,
          theme.section-label("Top 3 Focus", cfg),
          v(8pt),
          ..range(3).map(i => {
            grid(
              columns: (16pt, 9pt, 1fr),
              gutter: 7pt,
              align: horizon,
              theme.gold-badge(i + 1, cfg),
              theme.checkbox(cfg),
              box(height: 0.225in)[
                #place(bottom)[
                  #line(length: 100%, stroke: 0.4pt + cfg.line-col)
                ]
              ],
            )
            v(0.1in)
          }),
        ),

  theme.gold-rule(cfg),

        // Dynamic sections from body — unique per page
        ..sections.map(s => {
          let label = if type(s) == dictionary {
            s.at("name", default: str(s))
          } else {
            // Truncate very long labels to the first colon or 38 chars
            let raw = str(s)
            let colon-pos = raw.position(":")
            if colon-pos != none and colon-pos < 40 {
              raw.slice(0, colon-pos)
            } else if raw.len() > 38 {
              raw.slice(0, 38)
            } else {
              raw
            }
          }
          named-section(label, cfg, theme, lines: 3)
        }),

        theme.gold-rule(cfg),

        // Free writing overflow — fills remaining left-column space
        theme.section-label("Notes & Ideas", cfg),
        v(6pt),
        theme.writing-lines(4, cfg),
      ),

      // ── RIGHT COLUMN: clean hourly schedule (empty — user fills in) ─────
      stack(spacing: 0pt,
        theme.section-label("Schedule", cfg),
        v(8pt),
        ..("6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM", "12 PM",
           "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM", "7 PM", "8 PM").map(t => {
          grid(
            columns: (3pt, 0.45in, 1fr),
            gutter: 0pt,
            align: (horizon, left + horizon, left + bottom),
            box(width: 3pt, height: 0.285in, fill: cfg.secondary),
            pad(left: 5pt)[
              #text(size: 7.5pt, font: cfg.body-font, fill: cfg.muted)[#t]
            ],
            box(width: 100%, height: 0.285in, clip: true)[
              #place(bottom)[
                #line(length: 100%, stroke: 0.35pt + cfg.line-col)
              ]
            ],
          )
        }),
      ),
    )

    // ── Three-column footer ───────────────────────────────────────────────
    #v(1fr)
    #theme.three-col-footer("Notes", "Grateful For", "Evening Plans", cfg, lines: 3)
  ]

  theme.render-footer(cfg)
}
