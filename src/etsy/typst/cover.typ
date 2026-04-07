// cover.typ — family-specific cover layouts for Etsy printables

#let _cover-title(doc) = doc.at("title_theme", default: doc.at("title", default: "Planner"))

#let _section-name(s) = {
  if type(s) == dictionary { s.at("name", default: "Section") } else { str(s) }
}

#let _section-purpose(s) = {
  if type(s) == dictionary { s.at("purpose", default: "") } else { "" }
}

#let _displayed-sections(sections) = sections.slice(0, calc.min(sections.len(), 6))

#let _render-clean-cover(title, audience, sections, pg-count, cfg, theme) = {
  block(
    width: 100%,
    height: 6.05in,
    fill: cfg.primary,
    clip: true,
    inset: 0pt,
  )[
    #block(width: 100%, height: 4.5in)[
      #v(1fr)
      #pad(x: 0.7in)[
        #set align(center)
        #line(length: 2.4in, stroke: 0.8pt + cfg.secondary)
        #v(0.22in)
        #text(size: 34pt, font: cfg.heading-font, fill: white, weight: "bold")[#title]
        #v(0.18in)
        #text(size: 11pt, font: cfg.body-font, fill: cfg.secondary, tracking: 0.12em)[
          #upper("Designed for " + audience)
        ]
        #v(0.22in)
        #box(
          fill: rgb("#1A3A0A"),
          radius: 4pt,
          inset: (x: 14pt, y: 6pt),
        )[
          #text(size: 9pt, font: cfg.body-font, fill: white)[
            #str(pg-count) pages  ·  Instant Digital Download
          ]
        ]
        #v(0.22in)
        #line(length: 2.4in, stroke: 0.8pt + cfg.secondary)
      ]
      #v(1fr)
    ]

    #rect(width: 100%, height: 5pt, fill: cfg.secondary)
    #pad(x: 0.6in, top: 0.18in)[
      #set align(center)
      #theme.section-label("What's Inside", cfg)
    ]
    #pad(x: 0.6in, top: 0.14in)[
      #let displayed = _displayed-sections(sections)
      #grid(
        columns: (1fr, 1fr),
        gutter: (0.14in, 0.1in),
        ..displayed.map(s => {
          let name = _section-name(s)
          let purpose = _section-purpose(s)
          pad(y: 2pt)[
            #grid(
              columns: (10pt, 1fr),
              gutter: 6pt,
              align: top,
              text(size: 10pt, fill: cfg.secondary, font: cfg.body-font)[›],
              stack(spacing: 2pt,
                text(size: 10pt, font: cfg.heading-font, fill: white, weight: "bold")[#name],
                if purpose != "" {
                  text(size: 8pt, font: cfg.body-font, fill: rgb("#B8D4A8"))[#purpose]
                },
              ),
            )
          ]
        })
      )
    ]
  ]

  block(
    width: 100%,
    height: 11in - 6.05in,
    fill: cfg.bg,
    clip: true,
    inset: 0pt,
  )[
    #pad(x: 0.6in, top: 0.32in)[
      #box(
        width: 100%,
        stroke: 0.7pt + cfg.line-col,
        radius: 6pt,
        inset: (x: 14pt, y: 12pt),
        fill: white,
      )[
        #set align(center)
        #text(size: 9pt, font: cfg.body-font, fill: cfg.muted)[
          Print at home  ·  A4 & Letter compatible  ·  Personal planning use
        ]
      ]

      #v(0.2in)
      #line(length: 100%, stroke: 0.5pt + cfg.secondary)
      #v(6pt)
      #grid(
        columns: (1fr, auto),
        align: (left, right),
        text(size: 8pt, fill: cfg.muted, font: cfg.body-font)[
          Digital file only – no physical product will ship.
        ],
        text(size: 8pt, fill: cfg.muted, font: cfg.body-font)[
          Thank you for your purchase!
        ],
      )
    ]
  ]
}

#let _render-cottagecore-cover(title, audience, sections, pg-count, cfg, theme) = {
  let displayed = _displayed-sections(sections)
  block(
    width: 100%,
    height: 11in,
    fill: cfg.primary.transparentize(20%),
    inset: 0pt,
    clip: true,
  )[
    #pad(x: 0.75in, top: 0.7in, bottom: 0.6in)[
      #box(
        width: 100%,
        fill: cfg.bg,
        stroke: 0.7pt + cfg.secondary,
        radius: 18pt,
      )[
        #pad(x: 0.42in, top: 0.38in, bottom: 0.34in)[
          #set align(center)
          #text(size: 8pt, font: cfg.body-font, fill: cfg.secondary, tracking: 0.22em, style: "italic")[
            Gathered Inside
          ]
          #v(0.14in)
          #text(size: 28pt, font: cfg.heading-font, fill: cfg.primary, style: "italic")[#title]
          #v(0.12in)
          #text(size: 9.5pt, font: cfg.body-font, fill: cfg.muted)[#audience]
          #v(0.18in)
          #box(fill: cfg.secondary, radius: 12pt, inset: (x: 14pt, y: 6pt))[
            #text(size: 8.5pt, font: cfg.body-font, fill: white)[
              #str(pg-count) pages  ·  Printable ritual planner
            ]
          ]
          #v(0.22in)
          #line(length: 100%, stroke: 0.8pt + cfg.secondary)
          #v(0.18in)
          #grid(
            columns: (1fr, 1fr),
            gutter: 0.16in,
            ..displayed.map(s => {
              let name = _section-name(s)
              let purpose = _section-purpose(s)
              box(
                fill: white,
                stroke: 0.5pt + cfg.line-col,
                radius: 10pt,
                inset: (x: 12pt, y: 10pt),
              )[
                #stack(spacing: 4pt,
                  text(size: 9.5pt, font: cfg.heading-font, fill: cfg.primary, style: "italic")[#name],
                  if purpose != "" {
                    text(size: 7.5pt, font: cfg.body-font, fill: cfg.muted)[#purpose]
                  },
                )
              ]
            })
          )
        ]
      ]

      #v(0.22in)
      #set align(center)
      #text(size: 8.5pt, font: cfg.body-font, fill: cfg.muted, style: "italic")[
        Soft structure for thoughtful planning.
      ]
    ]
  ]
}

#let _render-bold-cover(title, audience, sections, pg-count, cfg, theme) = {
  let displayed = _displayed-sections(sections)
  block(
    width: 100%,
    height: 11in,
    fill: cfg.bg,
    inset: 0pt,
    clip: true,
  )[
    #rect(width: 100%, height: 0.34in, fill: cfg.secondary)
    #pad(x: 0.55in, top: 0.34in)[
      #box(fill: cfg.primary, radius: 16pt, width: 100%)[
        #pad(x: 0.34in, top: 0.3in, bottom: 0.28in)[
          #grid(
            columns: (1fr, auto),
            gutter: 0.18in,
            stack(spacing: 6pt,
              text(size: 9pt, font: cfg.body-font, fill: cfg.secondary, weight: "bold", tracking: 0.18em)[
                WHAT YOU GET
              ],
              text(size: 28pt, font: cfg.heading-font, fill: white, weight: "black")[#upper(title)],
              text(size: 9pt, font: cfg.body-font, fill: white)[#audience],
            ),
            box(fill: cfg.secondary, radius: 8pt, inset: (x: 12pt, y: 10pt))[
              #set align(center + horizon)
              #text(size: 9pt, font: cfg.body-font, fill: white, weight: "bold")[
                #str(pg-count)
              ]
              #linebreak()
              #text(size: 7pt, font: cfg.body-font, fill: white)[pages]
            ],
          )
        ]
      ]

      #v(0.22in)
      #grid(
        columns: (1fr, 1fr),
        gutter: 0.18in,
        ..displayed.map(s => {
          let name = _section-name(s)
          let purpose = _section-purpose(s)
          box(
            fill: cfg.tint,
            stroke: 1pt + cfg.primary,
            radius: 12pt,
            inset: (x: 12pt, y: 10pt),
          )[
            #stack(spacing: 4pt,
              text(size: 8pt, font: cfg.body-font, fill: cfg.primary, weight: "bold", tracking: 0.14em)[CARD],
              text(size: 11pt, font: cfg.heading-font, fill: cfg.dark, weight: "bold")[#name],
              if purpose != "" {
                text(size: 8pt, font: cfg.body-font, fill: cfg.muted)[#purpose]
              },
            )
          ]
        })
      )

      #v(0.24in)
      #box(width: 100%, fill: cfg.secondary, radius: 10pt, inset: (x: 16pt, y: 10pt))[
        #set align(center)
        #text(size: 9pt, font: cfg.body-font, fill: white, weight: "bold")[Print at home  ·  Instant digital download]
      ]
    ]
  ]
}

#let _render-dark-cover(title, audience, sections, pg-count, cfg, theme) = {
  let displayed = _displayed-sections(sections)
  block(
    width: 100%,
    height: 11in,
    fill: cfg.header-bg,
    inset: 0pt,
    clip: true,
  )[
    #pad(x: 0.8in, top: 0.85in, bottom: 0.7in)[
      #box(
        width: 100%,
        fill: cfg.bg,
        stroke: 1pt + cfg.secondary,
        radius: 10pt,
      )[
        #pad(x: 0.42in, top: 0.38in, bottom: 0.34in)[
          #text(size: 8pt, font: cfg.body-font, fill: cfg.secondary, tracking: 0.24em)[INCLUDED PAGES]
          #v(0.12in)
          #text(size: 28pt, font: cfg.heading-font, fill: cfg.header-bg, weight: "bold")[#title]
          #v(0.12in)
          #text(size: 9pt, font: cfg.body-font, fill: cfg.muted)[#audience]
          #v(0.18in)
          #line(length: 100%, stroke: 1pt + cfg.secondary)
          #v(0.14in)
          #stack(spacing: 8pt,
            ..displayed.enumerate().map(((i, s)) => {
              let name = _section-name(s)
              let purpose = _section-purpose(s)
              grid(
                columns: (16pt, 1fr),
                gutter: 10pt,
                align: top,
                theme.gold-badge(i + 1, cfg),
                stack(spacing: 2pt,
                  text(size: 9.5pt, font: cfg.heading-font, fill: cfg.header-bg, weight: "bold")[#name],
                  if purpose != "" {
                    text(size: 7.5pt, font: cfg.body-font, fill: cfg.muted)[#purpose]
                  },
                ),
              )
            }),
          )
          #v(0.18in)
          #box(fill: cfg.header-bg, radius: 6pt, inset: (x: 14pt, y: 8pt))[
            #set align(center)
            #text(size: 8.5pt, font: cfg.body-font, fill: cfg.secondary)[#str(pg-count) pages  ·  premium printable edition]
          ]
        ]
      ]
    ]
  ]
}

#let render-cover(doc, cfg, theme) = {
  let title    = _cover-title(doc)
  let audience = doc.at("audience", default: "busy adults")
  let sections = doc.at("sections", default: ())
  let pg-count = doc.at("page_count", default: 1)

  if cfg.family == "dark-luxury" {
    _render-dark-cover(title, audience, sections, pg-count, cfg, theme)
  } else if cfg.family == "cottagecore" {
    _render-cottagecore-cover(title, audience, sections, pg-count, cfg, theme)
  } else if cfg.family == "bold-playful" {
    _render-bold-cover(title, audience, sections, pg-count, cfg, theme)
  } else {
    _render-clean-cover(title, audience, sections, pg-count, cfg, theme)
  }
}
