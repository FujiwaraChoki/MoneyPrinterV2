"""Generate a deterministic sample run of the Etsy planner pipeline."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import etsy.io as etsy_io
from etsy.mockups import MockupAgent
from etsy.render_weasyprint import WeasyPrintRenderer

PRODUCT_SPEC = {
    "run_id": "focus-planner",
    "product_type": "planner",
    "audience": "busy professionals",
    "title_theme": "Focus Planner",
    "page_count": 5,
    "page_size": "LETTER",
    "sections": [
        "Morning Priorities",
        "Time Blocking",
        "Habit Tracker",
        "Weekly Reflection",
        "Project Planning",
    ],
    "style_notes": {"accent_color": "#2D5986", "vibe": "clean professional"},
    "output_files": ["product/focus-planner.pdf"],
}

DESIGN = {
    "run_id": "focus-planner",
    "palette": {"primary": "#2D5986", "secondary": "#D9C6A5", "background": "#FFF9F5"},
    "typography": {"heading_font": "Georgia-Bold", "body_font": "Trebuchet"},
    "layout": {
        "template_name": "Productivity Planner",
        "header_style": "banner",
        "page_frame_style": "rounded-border",
    },
    "mockup_style": {"background_color": "#F0EDE8", "scene_style": "desk-flatlay"},
}

BLUEPRINT = {
    "run_id": "focus-planner",
    "pages": [
        {
            "page_number": 1,
            "page_type": "worksheet",
            "title": "Morning Priorities",
            "section_name": "Daily Intentions",
            "body": [
                "Write your #1 priority before checking email",
                "Block 90 min of deep work before noon",
                "Avoid multitasking — one focus at a time",
                "Mark energy level (1-5) after each block",
                "Celebrate one win before the day ends",
            ],
            "palette_hint": "primary",
            "subtitle": "Set your top 3 intentions for the day",
        },
        {
            "page_number": 2,
            "page_type": "schedule",
            "title": "Time Blocking",
            "section_name": "Daily Schedule",
            "body": [
                "7 AM  – Morning routine & review",
                "9 AM  – Deep work block #1",
                "12 PM – Lunch + short walk",
                "2 PM  – Meetings & collaboration",
                "5 PM  – Wind-down & tomorrow prep",
            ],
            "palette_hint": "secondary",
            "subtitle": "Plan your hours with intention",
        },
        {
            "page_number": 3,
            "page_type": "tracker",
            "title": "Habit Tracker",
            "section_name": "Weekly Habits",
            "body": [
                "Exercise 30 min",
                "Read 20 pages",
                "No phone before 8 AM",
                "8 cups water",
                "Gratitude note",
            ],
            "palette_hint": "primary",
            "subtitle": "7-day check-in for your core habits",
        },
        {
            "page_number": 4,
            "page_type": "reflection",
            "title": "Weekly Reflection",
            "section_name": "Sunday Review",
            "body": [
                "What went really well this week?",
                "Where did I lose focus or energy?",
                "What one habit would make next week better?",
                "Rate your week overall (1-10)",
                "Carry-forward items for next week",
            ],
            "palette_hint": "secondary",
            "subtitle": "Review, reset, and realign",
        },
        {
            "page_number": 5,
            "page_type": "worksheet",
            "title": "Project Planning",
            "section_name": "Project Breakdown",
            "body": [
                "Define the outcome in one sentence",
                "List the 3 blockers standing in your way",
                "Write the very next physical action",
                "Set a due date and accountability check-in",
                "Review progress every Friday",
            ],
            "palette_hint": "primary",
            "subtitle": "Break big goals into daily actions",
        },
    ],
}


def main():
    base_dir = tempfile.mkdtemp(prefix="etsy-sample-")
    run_dir = etsy_io.create_run_directory(base_dir, "focus-planner")
    etsy_io.initialize_run_status(run_dir)
    os.makedirs(os.path.join(run_dir, "product"), exist_ok=True)

    etsy_io.write_json(os.path.join(run_dir, "artifacts", "product_spec.json"), PRODUCT_SPEC)
    etsy_io.write_json(os.path.join(run_dir, "artifacts", "design_system.json"), DESIGN)
    etsy_io.write_json(os.path.join(run_dir, "artifacts", "page_blueprint.json"), BLUEPRINT)

    renderer = WeasyPrintRenderer()
    renderer.run(run_dir)
    print("✓ PDF + previews rendered")

    MockupAgent().run(run_dir)
    print("✓ 5 mockup scenes generated")

    pdf_path = os.path.join(run_dir, "product", "focus-planner.pdf")
    mockup_dir = os.path.join(run_dir, "mockups")
    print(f"\nRun dir:  {run_dir}")
    print(f"PDF:      {pdf_path}")
    print("Mockups:")
    for f in sorted(os.listdir(mockup_dir)):
        print(f"  {os.path.join(mockup_dir, f)}")
    return pdf_path, mockup_dir


if __name__ == "__main__":
    main()
