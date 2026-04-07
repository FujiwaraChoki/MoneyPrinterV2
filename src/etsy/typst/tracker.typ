// tracker.typ — 31-day circle habit/goal tracker

#let render-tracker(page, product-spec, cfg, theme) = {
  let page-title  = page.at("title", default: "Monthly Tracker")
  let section     = page.at("section_name", default: "")
  let page-num    = page.at("page_number", default: 1)
  let page-total  = product-spec.at("page_count", default: 1)
  let title-theme = product-spec.at("title_theme", default: "Planner")
  let body        = page.at("body", default: ())

  // Up to 6 rows; fill with placeholders if body is short
  let rows = range(6).map(i => {
    if i < body.len() { str(body.at(i)) } else { "Row " + str(i + 1) }
  })

  // Build column definitions in code mode (not inside content block)
  // total width: 7.6in (8.5in minus 2×0.45in padding)
  // 1.4in label + 31×0.185in days + 0.27in total = 7.415in ✓
  let col-w    = 0.185in
  let tot-w    = 0.27in
  let lbl-w    = 1.4in
  let day-cols = (lbl-w,) + range(31).map(i => col-w) + (tot-w,)

  theme.render-header(title-theme, page-title, page-num, page-total, cfg)

  theme.content-area(cfg)[
    // Column headers
    #grid(
      columns: day-cols,
      gutter: 0pt,
      align: center + horizon,
      box(
        fill: cfg.primary, radius: 3pt,
        inset: (x: 6pt, y: 4pt), width: lbl-w,
      )[
        #set align(left)
        #text(size: 8pt, font: cfg.body-font, fill: white, weight: "bold")[TRACKER]
      ],
      ..range(1, 32).map(d =>
        text(size: 6.5pt, font: cfg.body-font, fill: cfg.muted)[#str(d)]
      ),
      text(size: 6.5pt, font: cfg.body-font, fill: cfg.muted)[✓],
    )

    #v(4pt)
    #line(length: 100%, stroke: 1pt + cfg.secondary)
    #v(6pt)

    // Data rows
    #for (i, label) in rows.enumerate() {
      let row-bg = if calc.odd(i) { cfg.bg } else { cfg.line-col.transparentize(60%) }
      block(
        width: 100%,
        fill: row-bg,
        radius: 2pt,
        inset: (y: 3pt),
      )[
        #grid(
          columns: day-cols,
          gutter: 0pt,
          align: center + horizon,
          pad(left: 6pt)[
            #set align(left)
            #text(size: 8pt, font: cfg.body-font, fill: cfg.dark)[#label]
          ],
          ..range(31).map(j =>
            box(width: 9pt, height: 9pt, stroke: 0.5pt + cfg.muted, radius: 50%)[]
          ),
          box(width: 22pt, height: 14pt, stroke: 0.5pt + cfg.secondary, radius: 2pt)[],
        )
      ]
      v(3pt)
    }

    #v(1fr)
    #theme.three-col-footer("What Worked", "Improve Next Month", "Focus For Next Month", cfg, lines: 2)
  ]

  theme.render-footer(cfg)
}
