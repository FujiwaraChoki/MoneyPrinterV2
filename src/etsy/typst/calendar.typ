// calendar.typ — Monthly calendar spread (5-week grid)

#let render-calendar(page, product-spec, cfg, theme) = {
  let page-title  = page.at("title", default: "Monthly Calendar")
  let section     = page.at("section_name", default: "")
  let page-num    = page.at("page_number", default: 1)
  let page-total  = product-spec.at("page_count", default: 1)
  let title-theme = product-spec.at("title_theme", default: "Planner")
  let body        = page.at("body", default: ())

  let day-names   = ("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT")
  let cell-h      = 0.88in
  let all-cells   = range(35)

  theme.render-header(title-theme, page-title, page-num, page-total, cfg)

  theme.content-area(cfg)[
    // Month + Intention fields
    #grid(
      columns: (1.4in, 1.4in, 1fr),
      gutter: 0.22in,
      align: bottom,
      stack(spacing: 3pt,
        theme.section-label("Month", cfg),
        line(length: 100%, stroke: 0.4pt + cfg.line-col),
      ),
      stack(spacing: 3pt,
        theme.section-label("Year", cfg),
        line(length: 100%, stroke: 0.4pt + cfg.line-col),
      ),
      stack(spacing: 3pt,
        theme.section-label("Monthly Intention", cfg),
        line(length: 100%, stroke: 0.4pt + cfg.line-col),
      ),
    )

    #v(0.12in)

    // Day-of-week header row
    #grid(
      columns: range(7).map(i => 1fr),
      gutter: 2pt,
      ..day-names.map(d =>
        box(fill: cfg.primary, width: 100%, height: 20pt, radius: 2pt)[
          #set align(center + horizon)
          #text(size: 7.5pt, font: cfg.body-font, fill: white, weight: "bold", tracking: 0.08em)[#d]
        ]
      ),
    )

    #v(2pt)

    // 5-week grid
    #grid(
      columns: range(7).map(i => 1fr),
      rows: range(5).map(i => cell-h),
      gutter: 2pt,
      ..all-cells.map(i => {
        let hint = if i < body.len() { str(body.at(i)) } else { "" }
        box(
          width: 100%, height: cell-h,
          stroke: 0.4pt + cfg.line-col,
          fill: white,
          radius: 2pt,
          clip: true,
          inset: 0pt,
        )[
          #pad(left: 5pt, top: 3pt)[
            #text(size: 9pt, font: cfg.body-font, fill: cfg.muted)[ ]
          ]
          #pad(x: 5pt, top: 16pt)[
            #for j in range(3) {
              line(length: 100%, stroke: 0.3pt + cfg.line-col)
              v(0.18in)
            }
          ]
        ]
      }),
    )

    #v(1fr)
    #theme.three-col-footer("Monthly Goals", "Key Dates", "Notes", cfg, lines: 2)
  ]

  theme.render-footer(cfg)
}
