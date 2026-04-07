// main.typ — root Typst document; receives JSON data via sys.inputs
// Usage: typst compile main.typ out.pdf --root . --input data='<json>'
#import "_base.typ"
#import "_base_dark.typ"
#import "_base_cottagecore.typ"
#import "_base_bold.typ"
#import "cover.typ": render-cover
#import "worksheet.typ": render-worksheet
#import "schedule.typ": render-schedule
#import "tracker.typ": render-tracker
#import "reflection.typ": render-reflection
#import "calendar.typ": render-calendar

// ── Parse input ──────────────────────────────────────────────────────────────
#let raw-data = sys.inputs.at("data", default: "{}")
#if raw-data == "{}" {
  panic("No 'data' input provided. Pass --input data='<json>'")
}
#let doc = json(bytes(raw-data))

#let product-spec  = doc.at("product_spec", default: (:))
#let design-system = doc.at("design_system", default: (:))
#let page-blueprint = doc.at("page_blueprint", default: (:))
#let pages          = page-blueprint.at("pages", default: ())

// Select config builder based on template_family
#let _family = design-system.at("template_family", default: "clean-minimal")
#let theme = if _family == "dark-luxury" {
  _base_dark
} else if _family == "cottagecore" {
  _base_cottagecore
} else if _family == "bold-playful" {
  _base_bold
} else {
  _base
}
#let cfg = theme.make-config(design-system)

// ── Document settings ────────────────────────────────────────────────────────
#set document(
  title: product-spec.at("title_theme", default: "Planner"),
)
#set page(
  paper: "us-letter",
  margin: 0pt,
)
#set block(spacing: 0pt)
#set par(spacing: 0pt, leading: 0.6em)
#set text(
  font: (cfg.body-font, "DM Sans 9pt", "Lato"),
  fallback: true,
)

// ── Cover ────────────────────────────────────────────────────────────────────
#render-cover(product-spec, cfg, theme)
#pagebreak()

// ── Content pages ────────────────────────────────────────────────────────────
#for (i, page) in pages.enumerate() {
  let pt = page.at("page_type", default: "worksheet")
  if pt == "cover" {
    // already rendered above
  } else if pt == "schedule" {
    render-schedule(page, product-spec, cfg, theme)
  } else if pt == "tracker" {
    render-tracker(page, product-spec, cfg, theme)
  } else if pt == "reflection" {
    render-reflection(page, product-spec, cfg, theme)
  } else if pt == "calendar" {
    render-calendar(page, product-spec, cfg, theme)
  } else {
    render-worksheet(page, product-spec, cfg, theme)
  }
  if i < pages.len() - 1 and pt != "cover" { pagebreak() }
}
