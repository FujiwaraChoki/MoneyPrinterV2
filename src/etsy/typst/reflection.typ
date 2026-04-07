// reflection.typ — Journaling reflection page

#let render-reflection(page, product-spec, cfg, theme) = {
  let page-title  = page.at("title", default: "Reflect & Reset")
  let page-num    = page.at("page_number", default: 1)
  let page-total  = product-spec.at("page_count", default: 1)
  let title-theme = product-spec.at("title_theme", default: "Planner")
  let body        = page.at("body", default: ())

  let default-qs = (
    "What went well today?",
    "What challenged me and what did I learn?",
    "What am I most grateful for?",
    "What is my intention for tomorrow?",
  )
  let questions = range(4).map(i => {
    if i < body.len() { str(body.at(i)) } else { default-qs.at(i) }
  })

  let mood-emojis = ("😞", "😐", "🙂", "😊", "🌟")

  theme.render-header(title-theme, page-title, page-num, page-total, cfg)

  theme.content-area(cfg)[
    // Date + mood row
    #grid(
      columns: (1.4in, 1fr, 1.6in),
      gutter: 0.2in,
      align: bottom,
      stack(spacing: 3pt,
        theme.section-label("Date", cfg),
        line(length: 100%, stroke: 0.4pt + cfg.line-col),
      ),
      stack(spacing: 3pt,
        theme.section-label("Mood / Energy", cfg),
        grid(
          columns: range(5).map(i => 20pt),
          gutter: 6pt,
          ..mood-emojis.map(e =>
            box(width: 18pt, height: 18pt, stroke: 0.6pt + cfg.muted, radius: 50%)[
              #set align(center + horizon)
              #text(size: 10pt)[#e]
            ]
          ),
        ),
      ),
      stack(spacing: 3pt,
        theme.section-label("Overall Rating", cfg),
        grid(
          columns: range(5).map(i => 14pt),
          gutter: 4pt,
          ..range(5).map(k =>
            box(width: 12pt, height: 12pt, stroke: 0.5pt + cfg.secondary, radius: 50%)[]
          ),
        ),
      ),
    )

    #v(0.16in)
  #theme.gold-rule(cfg)
    #v(0.12in)

    // 4 reflection question boxes
    #for (i, q) in questions.enumerate() {
      box(
        width: 100%,
        stroke: 0.5pt + cfg.line-col,
        radius: 5pt,
        fill: white,
        inset: (x: 12pt, top: 10pt, bottom: 8pt),
      )[
        #grid(
          columns: (16pt, 1fr),
          gutter: 8pt,
          align: top,
          theme.gold-badge(i + 1, cfg),
          stack(spacing: 7pt,
            text(size: 9pt, font: cfg.heading-font, fill: cfg.primary, weight: "bold")[#q],
            theme.writing-lines(3, cfg),
          ),
        )
      ]
      if i < 3 { v(0.1in) }
    }

    #v(1fr)

    // Bottom two-panel: Gratitude + Affirmation
    #theme.gold-rule(cfg)
    #v(8pt)
    #grid(
      columns: (1fr, 1fr),
      gutter: 0.2in,
      // Gratitude list
      stack(spacing: 5pt,
        theme.section-label("Gratitude (3 things)", cfg),
        v(4pt),
        ..range(3).map(n => {
          let items = (
            grid(
              columns: (9pt, 1fr),
              gutter: 6pt,
              align: horizon,
              theme.checkbox(cfg),
              box(height: 0.22in)[
                #place(bottom)[
                  #line(length: 100%, stroke: 0.4pt + cfg.line-col)
                ]
              ],
            ),
            v(0.08in),
          )
          items
        }).flatten(),
      ),
      // Affirmation card
      box(
        fill: cfg.primary,
        radius: 5pt,
        inset: (x: 12pt, y: 10pt),
        height: 100%,
      )[
        #theme.section-label("Tonight's Affirmation", cfg)
        #v(6pt)
        #theme.writing-lines(3, (
          primary: cfg.primary, secondary: cfg.secondary, bg: cfg.bg,
          dark: cfg.dark, muted: cfg.muted, mid: cfg.mid,
          family: cfg.family,
          line-col: white.transparentize(25%),
          heading-font: cfg.heading-font, body-font: cfg.body-font,
        ))
      ],
    )
  ]

  theme.render-footer(cfg)
}
