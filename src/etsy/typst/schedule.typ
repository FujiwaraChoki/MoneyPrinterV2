// schedule.typ — Full-day hourly schedule page (5AM–10PM)

#let render-schedule(page, product-spec, cfg, theme) = {
  let page-title  = page.at("title", default: "Daily Schedule")
  let page-num    = page.at("page_number", default: 1)
  let page-total  = product-spec.at("page_count", default: 1)
  let title-theme = product-spec.at("title_theme", default: "Planner")
  let body        = page.at("body", default: ())

  let hours = (
    "5 AM", "6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM",
    "12 PM", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM",
    "7 PM", "8 PM", "9 PM", "10 PM",
  )
  let left-hours  = hours.slice(0, 9)
  let right-hours = hours.slice(9)

  // Build hour row as a function in code mode
  let hour-row(lbl, idx) = {
    let hint = if idx < body.len() { str(body.at(idx)) } else { "" }
    grid(
      columns: (0pt, 0.5in, 1fr),
      gutter: 0pt,
      align: (horizon, left + horizon, left + bottom),
      box(width: 3.5pt, height: 0.275in, fill: cfg.secondary.transparentize(30%)),
      pad(left: 5pt)[
        #text(size: 7.5pt, font: cfg.body-font, fill: cfg.muted)[#lbl]
      ],
      box(width: 100%, height: 0.275in)[
        #if hint != "" {
          pad(left: 5pt, bottom: 3pt)[
            #text(size: 7.5pt, font: cfg.body-font, fill: cfg.dark)[#hint]
          ]
        }
        #place(bottom)[
          #line(length: 100%, stroke: 0.35pt + cfg.line-col)
        ]
      ],
    )
  }

  theme.render-header(title-theme, page-title, page-num, page-total, cfg)

  theme.content-area(cfg)[
    // Top fields row
    #grid(
      columns: (1.6in, 1fr, 1fr, 1fr),
      gutter: 0.2in,
      align: bottom,
      stack(spacing: 3pt,
        theme.section-label("Focus for Today", cfg),
        line(length: 100%, stroke: 0.4pt + cfg.line-col),
      ),
      stack(spacing: 3pt,
        theme.section-label("Date", cfg),
        line(length: 100%, stroke: 0.4pt + cfg.line-col),
      ),
      stack(spacing: 3pt,
        theme.section-label("Energy Level", cfg),
        line(length: 100%, stroke: 0.4pt + cfg.line-col),
      ),
      stack(spacing: 3pt,
        theme.section-label("Water", cfg),
        grid(
          columns: range(8).map(i => 10pt),
          gutter: 3pt,
          ..range(8).map(i => box(width: 10pt, height: 10pt, stroke: 0.6pt + cfg.muted, radius: 50%)[]),
        ),
      ),
    )

    #v(0.14in)
  #theme.gold-rule(cfg)
    #v(0.1in)

    // Hour grid — two columns of 9 each
    #grid(
      columns: (1fr, 0.14in, 1fr),
      gutter: 0pt,
      // left column
      stack(spacing: 0pt, ..left-hours.enumerate().map(((i, lbl)) => hour-row(lbl, i))),
      // separator
      box(width: 0.14in)[],
      // right column
      stack(spacing: 0pt, ..right-hours.enumerate().map(((i, lbl)) => hour-row(lbl, i + 9))),
    )

    #v(1fr)
    #theme.three-col-footer("Morning Intentions", "Evening Wins", "Notes & Follow-Ups", cfg, lines: 2)
  ]

  theme.render-footer(cfg)
}
