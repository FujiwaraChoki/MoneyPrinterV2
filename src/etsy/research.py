import json
import os
import re
from datetime import datetime, timezone

from etsy.contracts import VALID_CATEGORIES
from etsy.contracts import validate_research_artifact
from etsy.io import write_json


# Grounded niche seed data — proven Etsy digital planner niches with real market signals.
# search_volume: "high" = 10k+/mo, "medium" = 2–10k/mo, "low" = <2k/mo
# seasonal_peak: quarter(s) when search spikes; None = evergreen year-round
# pricing_usd: [min, max] typical listing price range
# aesthetic_family: which template family suits this niche best
_NICHE_SEED = [
    {
        "slug": "zero-based-budget-planner",
        "title": "Zero-Based Budget Planner",
        "category": "planner",
        "target_buyer": "adults overwhelmed by monthly finances",
        "problem_solved": "tracks every dollar to zero so nothing is wasted",
        "search_volume": "high",
        "pricing_usd": [4, 9],
        "seasonal_peak": ["Q1", "Q4"],
        "aesthetic_family": "clean-minimal",
    },
    {
        "slug": "debt-snowball-tracker",
        "title": "Debt Snowball Tracker",
        "category": "tracker",
        "target_buyer": "people paying off credit cards or student loans",
        "problem_solved": "visualises debt payoff order and motivates progress",
        "search_volume": "high",
        "pricing_usd": [3, 7],
        "seasonal_peak": ["Q1"],
        "aesthetic_family": "clean-minimal",
    },
    {
        "slug": "adhd-daily-planner",
        "title": "ADHD Daily Planner",
        "category": "planner",
        "target_buyer": "adults with ADHD seeking structure without overwhelm",
        "problem_solved": "short time-blocks, dopamine rewards, and visual priority cues",
        "search_volume": "high",
        "pricing_usd": [5, 12],
        "seasonal_peak": None,
        "aesthetic_family": "bold-playful",
    },
    {
        "slug": "adhd-focus-worksheet",
        "title": "ADHD Focus & Task Breakdown Worksheet",
        "category": "worksheet",
        "target_buyer": "neurodivergent adults and teens",
        "problem_solved": "breaks big tasks into micro-steps to reduce paralysis",
        "search_volume": "medium",
        "pricing_usd": [3, 8],
        "seasonal_peak": None,
        "aesthetic_family": "bold-playful",
    },
    {
        "slug": "wedding-planning-bundle",
        "title": "Wedding Planning Bundle",
        "category": "planner",
        "target_buyer": "engaged couples planning their own wedding",
        "problem_solved": "vendor tracking, budget, guest list, and timeline in one download",
        "search_volume": "high",
        "pricing_usd": [8, 18],
        "seasonal_peak": ["Q1", "Q2"],
        "aesthetic_family": "cottagecore",
    },
    {
        "slug": "small-business-client-tracker",
        "title": "Small Business Client & Project Tracker",
        "category": "tracker",
        "target_buyer": "freelancers, coaches, and solopreneurs",
        "problem_solved": "tracks client info, project status, and invoices without software",
        "search_volume": "medium",
        "pricing_usd": [5, 14],
        "seasonal_peak": ["Q1", "Q3"],
        "aesthetic_family": "clean-minimal",
    },
    {
        "slug": "social-media-content-calendar",
        "title": "Social Media Content Calendar",
        "category": "planner",
        "target_buyer": "small business owners and content creators",
        "problem_solved": "plans and batches posts across platforms to stay consistent",
        "search_volume": "high",
        "pricing_usd": [4, 10],
        "seasonal_peak": ["Q1", "Q4"],
        "aesthetic_family": "bold-playful",
    },
    {
        "slug": "weekly-meal-planner-grocery",
        "title": "Weekly Meal Planner + Grocery List",
        "category": "planner",
        "target_buyer": "busy families and health-conscious adults",
        "problem_solved": "eliminates 6pm decision fatigue and reduces grocery waste",
        "search_volume": "high",
        "pricing_usd": [3, 7],
        "seasonal_peak": None,
        "aesthetic_family": "cottagecore",
    },
    {
        "slug": "macro-nutrition-tracker",
        "title": "Macro & Nutrition Tracker",
        "category": "tracker",
        "target_buyer": "fitness-focused adults tracking protein and calories",
        "problem_solved": "daily macro logging without an app subscription",
        "search_volume": "medium",
        "pricing_usd": [4, 9],
        "seasonal_peak": ["Q1", "Q2"],
        "aesthetic_family": "clean-minimal",
    },
    {
        "slug": "teacher-lesson-planner",
        "title": "Teacher Lesson Planner Bundle",
        "category": "planner",
        "target_buyer": "K-12 classroom teachers",
        "problem_solved": "weekly lesson plans, grade tracking, and parent contact logs in one PDF",
        "search_volume": "high",
        "pricing_usd": [5, 12],
        "seasonal_peak": ["Q3"],
        "aesthetic_family": "bold-playful",
    },
    {
        "slug": "pregnancy-week-by-week-tracker",
        "title": "Pregnancy Week-by-Week Tracker",
        "category": "tracker",
        "target_buyer": "expectant parents and gift-givers",
        "problem_solved": "captures milestones, symptoms, and memory prompts through all 40 weeks",
        "search_volume": "medium",
        "pricing_usd": [5, 12],
        "seasonal_peak": None,
        "aesthetic_family": "cottagecore",
    },
    {
        "slug": "habit-tracker-30-day",
        "title": "30-Day Habit Tracker",
        "category": "tracker",
        "target_buyer": "adults building new routines",
        "problem_solved": "visual streak tracking with daily reflection prompts",
        "search_volume": "high",
        "pricing_usd": [3, 7],
        "seasonal_peak": ["Q1", "Q4"],
        "aesthetic_family": "clean-minimal",
    },
    {
        "slug": "morning-evening-routine-planner",
        "title": "Morning & Evening Routine Planner",
        "category": "planner",
        "target_buyer": "productivity-seekers wanting structured days",
        "problem_solved": "anchors daily energy with intentional morning and wind-down rituals",
        "search_volume": "medium",
        "pricing_usd": [4, 9],
        "seasonal_peak": ["Q1"],
        "aesthetic_family": "dark-luxury",
    },
    {
        "slug": "executive-weekly-planner",
        "title": "Executive Weekly Planner",
        "category": "planner",
        "target_buyer": "professionals and managers with high workloads",
        "problem_solved": "prioritises high-impact work and tracks meetings in a premium format",
        "search_volume": "medium",
        "pricing_usd": [5, 12],
        "seasonal_peak": ["Q1", "Q3"],
        "aesthetic_family": "dark-luxury",
    },
    {
        "slug": "savings-goal-tracker",
        "title": "Savings Goal Tracker",
        "category": "tracker",
        "target_buyer": "adults saving for a house, vacation, or emergency fund",
        "problem_solved": "visualises progress toward a specific savings target",
        "search_volume": "medium",
        "pricing_usd": [3, 7],
        "seasonal_peak": ["Q1"],
        "aesthetic_family": "clean-minimal",
    },
    {
        "slug": "homeschool-curriculum-planner",
        "title": "Homeschool Curriculum Planner",
        "category": "planner",
        "target_buyer": "homeschooling parents",
        "problem_solved": "organises subjects, schedules, and learning milestones for multiple children",
        "search_volume": "medium",
        "pricing_usd": [6, 14],
        "seasonal_peak": ["Q3"],
        "aesthetic_family": "cottagecore",
    },
    {
        "slug": "gratitude-journal-planner",
        "title": "Gratitude & Mindfulness Journal",
        "category": "worksheet",
        "target_buyer": "adults practising daily mindfulness or therapy homework",
        "problem_solved": "daily prompts to shift focus from stress to gratitude",
        "search_volume": "medium",
        "pricing_usd": [4, 10],
        "seasonal_peak": None,
        "aesthetic_family": "cottagecore",
    },
    {
        "slug": "book-reading-tracker",
        "title": "Reading Log & Book Tracker",
        "category": "tracker",
        "target_buyer": "avid readers and reading challenge participants",
        "problem_solved": "logs books read, ratings, quotes, and TBR list in one place",
        "search_volume": "medium",
        "pricing_usd": [3, 7],
        "seasonal_peak": None,
        "aesthetic_family": "dark-luxury",
    },
    {
        "slug": "garden-planting-planner",
        "title": "Garden Planting & Harvest Planner",
        "category": "planner",
        "target_buyer": "home gardeners and urban farmers",
        "problem_solved": "tracks what to plant when, watering schedules, and harvest yields",
        "search_volume": "medium",
        "pricing_usd": [4, 9],
        "seasonal_peak": ["Q1", "Q2"],
        "aesthetic_family": "cottagecore",
    },
    {
        "slug": "fitness-workout-log",
        "title": "Fitness & Workout Log",
        "category": "tracker",
        "target_buyer": "gym-goers and home workout enthusiasts",
        "problem_solved": "tracks sets, reps, personal records, and weekly progress",
        "search_volume": "high",
        "pricing_usd": [4, 9],
        "seasonal_peak": ["Q1", "Q2"],
        "aesthetic_family": "bold-playful",
    },
]


class ResearchAgent:
    def __init__(self, text_generator):
        self.text_generator = text_generator

    def run(self, run_dir: str) -> str:
        log_path = os.path.join(os.path.dirname(run_dir), "niche_log.json")
        used_niches = self._read_niche_log(log_path)

        # Step 1: select the best niche from seed data
        selection_raw = self.text_generator(self._build_selection_prompt(used_niches))
        selection = self._coerce_payload(selection_raw)
        selected_slug = str(selection.get("selected_slug", "")).strip()

        # Step 2: analyse competitor patterns for that niche
        seed_entry = self._find_seed_entry(selected_slug)
        analysis_raw = self.text_generator(self._build_analysis_prompt(seed_entry))
        analysis = self._coerce_payload(analysis_raw)

        # Step 3: distil into final research artifact
        raw_payload = self.text_generator(self._build_distil_prompt(seed_entry, analysis, used_niches))
        payload = self._coerce_payload(raw_payload)
        payload = self._normalize_payload(payload)

        payload["run_id"] = os.path.basename(run_dir)
        validate_research_artifact(payload)

        artifact_path = os.path.join(run_dir, "artifacts", "research.json")
        write_json(artifact_path, payload)

        self._append_to_niche_log(log_path, payload)
        return artifact_path

    def _niche_log_path(self, run_dir: str) -> str:
        return os.path.join(os.path.dirname(run_dir), "niche_log.json")

    def _find_seed_entry(self, selected_slug: str) -> dict:
        """Return the seed entry matching selected_slug, or the first entry as fallback."""
        for entry in _NICHE_SEED:
            if entry["slug"] == selected_slug:
                return entry
        return _NICHE_SEED[0]

    def _seasonal_filter(self) -> list[dict]:
        """Return seed niches relevant to the current quarter."""
        month = datetime.now().month
        quarter = f"Q{(month - 1) // 3 + 1}"
        return [
            e for e in _NICHE_SEED
            if e["seasonal_peak"] is None or quarter in e["seasonal_peak"]
        ]

    def _build_selection_prompt(self, used_niches: list[dict]) -> str:
        avoid_slugs = {e.get("slug", "") for e in used_niches[-20:]}
        candidates = [e for e in self._seasonal_filter() if e["slug"] not in avoid_slugs]
        if not candidates:
            candidates = _NICHE_SEED  # all niches if everything was recently used

        seed_json = json.dumps(
            [{"slug": e["slug"], "title": e["title"], "search_volume": e["search_volume"],
              "pricing_usd": e["pricing_usd"], "category": e["category"]} for e in candidates],
            indent=2,
        )
        return (
            "You are an Etsy market analyst. Choose the single best niche to produce RIGHT NOW "
            "based on current search demand, pricing potential, and competition level.\n\n"
            f"Available niches (current season, not recently used):\n{seed_json}\n\n"
            "Return strict JSON with one field: selected_slug — the slug of your top pick. "
            "Favour high search_volume niches. Return only the JSON object."
        )

    def _build_analysis_prompt(self, seed_entry: dict) -> str:
        return (
            f"You are an Etsy competitive analyst. Analyse the '{seed_entry['title']}' niche "
            f"for digital printables.\n\n"
            f"Target buyer: {seed_entry['target_buyer']}\n"
            f"Core problem solved: {seed_entry['problem_solved']}\n"
            f"Typical price range: ${seed_entry['pricing_usd'][0]}–${seed_entry['pricing_usd'][1]}\n\n"
            "Describe what the top 5 listings in this niche look like. Return strict JSON with:\n"
            "- common_page_counts: array of typical page counts (e.g. [40, 60, 80, 100])\n"
            "- common_aesthetics: array of 3 aesthetic keywords (e.g. ['minimalist', 'clean', 'modern'])\n"
            "- underserved_angle: one sentence describing a gap competitors miss\n"
            "- buyer_pain_point: one sentence of the exact frustration the buyer feels\n"
            "Return only the JSON object."
        )

    def _build_distil_prompt(self, seed_entry: dict, analysis: dict, used_niches: list[dict]) -> str:
        avoid_clause = ""
        if used_niches:
            recent = used_niches[-20:]
            avoid_list = ", ".join(
                entry.get("title") or entry.get("slug", "")
                for entry in recent
                if entry.get("title") or entry.get("slug")
            )
            if avoid_list:
                avoid_clause = f" Do NOT repeat: {avoid_list}."

        underserved = analysis.get("underserved_angle", "")
        pain_point = analysis.get("buyer_pain_point", "")
        aesthetics = analysis.get("common_aesthetics", [])
        page_counts = analysis.get("common_page_counts", [60])
        min_pages = min(page_counts) if page_counts else 60

        return (
            "You are an Etsy digital product strategist." + avoid_clause + "\n\n"
            f"Niche: {seed_entry['title']}\n"
            f"Target buyer: {seed_entry['target_buyer']}\n"
            f"Underserved angle: {underserved}\n"
            f"Buyer pain point: {pain_point}\n"
            f"Winning aesthetics in this niche: {', '.join(aesthetics)}\n"
            f"Minimum competitive page count: {min_pages}\n\n"
            "Generate a ranked Etsy digital-product research result as strict JSON. "
            "Return an object with: category, opportunities (array of 3), and selected_opportunity.\n"
            f"category must be one of: planner, tracker, worksheet.\n"
            "Each opportunity: idea_slug, title, target_buyer, problem_solved, score (0–1).\n"
            "The best opportunity should exploit the underserved_angle.\n"
            "selected_opportunity must be the idea_slug string of your top pick."
        )

    def _build_prompt(self, used_niches: list[dict] = None) -> str:
        """Legacy single-step prompt kept for fallback compatibility."""
        avoid_clause = ""
        if used_niches:
            recent = used_niches[-20:]
            avoid_list = ", ".join(
                entry.get("title") or entry.get("slug", "")
                for entry in recent
                if entry.get("title") or entry.get("slug")
            )
            if avoid_list:
                avoid_clause = f" Do NOT repeat or closely overlap any of these recently used niches: {avoid_list}."
        return (
            "You are an Etsy digital product trend researcher. Identify what is trending right now among Etsy buyers."
            + avoid_clause +
            " Generate a ranked Etsy digital-product research result as strict JSON."
            " Return an object with category, opportunities, and selected_opportunity."
            " Use only planner, tracker, or worksheet categories."
            " Each opportunity must include idea_slug, title, target_buyer, problem_solved, and score."
            " selected_opportunity must be the chosen idea_slug string, not an object."
        )

    def _read_niche_log(self, log_path: str) -> list:
        if not os.path.exists(log_path):
            return []
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _append_to_niche_log(self, log_path: str, payload: dict) -> None:
        log = self._read_niche_log(log_path)
        selected_slug = payload.get("selected_opportunity", "")
        selected_title = ""
        for opp in payload.get("opportunities", []):
            if opp.get("idea_slug") == selected_slug:
                selected_title = opp.get("title", "")
                break
        log.append({
            "run_id": payload.get("run_id", ""),
            "slug": selected_slug,
            "title": selected_title,
            "used_at": datetime.now(timezone.utc).isoformat(),
        })
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)

    def _build_prompt(self, used_niches: list[dict] = None) -> str:
        avoid_clause = ""
        if used_niches:
            recent = used_niches[-20:]
            avoid_list = ", ".join(
                entry.get("title") or entry.get("slug", "")
                for entry in recent
                if entry.get("title") or entry.get("slug")
            )
            if avoid_list:
                avoid_clause = f" Do NOT repeat or closely overlap any of these recently used niches: {avoid_list}."
        return (
            "You are an Etsy digital product trend researcher. Identify what is trending right now among Etsy buyers."
            + avoid_clause +
            " Generate a ranked Etsy digital-product research result as strict JSON."
            " Return an object with category, opportunities, and selected_opportunity."
            " Use only planner, tracker, or worksheet categories."
            " Each opportunity must include idea_slug, title, target_buyer, problem_solved, and score."
            " selected_opportunity must be the chosen idea_slug string, not an object."
        )

    def _coerce_payload(self, raw_payload):
        if not isinstance(raw_payload, str):
            return dict(raw_payload)

        raw_text = raw_payload.strip()
        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw_text, re.DOTALL)
        if fenced_match:
            raw_text = fenced_match.group(1)
        return json.loads(raw_text)

    def _normalize_payload(self, payload: dict) -> dict:
        normalized = dict(payload)
        opportunities = self._extract_opportunities(normalized)
        normalized_opportunities = [
            self._normalize_opportunity(item) for item in opportunities
        ]

        if not normalized_opportunities:
            selected_candidate = self._extract_selected_candidate(normalized)
            if selected_candidate:
                normalized_opportunities = [self._normalize_opportunity(selected_candidate)]

        normalized["opportunities"] = normalized_opportunities

        selected_slug = self._normalize_selected_opportunity(
            self._extract_selected_candidate(normalized),
            normalized_opportunities,
        )
        normalized["selected_opportunity"] = selected_slug

        category = str(normalized.get("category", "")).strip().lower()
        if category not in VALID_CATEGORIES:
            category = self._infer_category(normalized_opportunities, self._extract_selected_candidate(normalized))
        normalized["category"] = category

        return normalized

    def _extract_opportunities(self, payload: dict) -> list:
        for field_name in (
            "opportunities",
            "ideas",
            "products",
            "recommendations",
            "ranked_opportunities",
            "niches",
        ):
            value = payload.get(field_name)
            if isinstance(value, list) and value:
                return value
        return []

    def _extract_selected_candidate(self, payload: dict):
        for field_name in (
            "selected_opportunity",
            "recommended_opportunity",
            "recommended_product",
            "top_pick",
            "best_match",
            "best_opportunity",
        ):
            value = payload.get(field_name)
            if value:
                return value
        return None

    def _normalize_selected_opportunity(self, selected_opportunity, opportunities: list[dict]) -> str:
        if isinstance(selected_opportunity, dict):
            selected_slug = self._normalize_opportunity(selected_opportunity).get("idea_slug", "")
        else:
            selected_slug = str(selected_opportunity or "").strip()

        idea_slugs = [item.get("idea_slug", "") for item in opportunities]
        if selected_slug and selected_slug not in idea_slugs:
            selected_slug = self._slugify(selected_slug)

        if selected_slug not in idea_slugs:
            selected_slug = self._match_selected_slug(selected_slug, opportunities)

        if selected_slug not in idea_slugs and opportunities:
            selected_slug = opportunities[0].get("idea_slug", "")

        return selected_slug

    def _match_selected_slug(self, selected_slug: str, opportunities: list[dict]) -> str:
        selected_tokens = self._slug_tokens(selected_slug)
        if not selected_tokens:
            return ""

        best_slug = ""
        best_score = 0
        for item in opportunities:
            candidate_tokens = self._slug_tokens(item.get("idea_slug", "")) | self._slug_tokens(item.get("title", ""))
            overlap = len(selected_tokens & candidate_tokens)
            if overlap > best_score:
                best_score = overlap
                best_slug = item.get("idea_slug", "")

        return best_slug if best_score > 0 else ""

    def _slug_tokens(self, value: str) -> set[str]:
        stop_words = {"a", "an", "and", "for", "of", "the", "to", "with"}
        return {token for token in self._slugify(value).split("-") if token and token not in stop_words}

    def _normalize_opportunity(self, item) -> dict:
        if not isinstance(item, dict):
            text = str(item).strip() or "idea"
            item = {
                "title": text,
                "target_buyer": text,
                "problem_solved": text,
            }

        idea_source = item.get("idea_slug") or item.get("niche") or item.get("title") or item.get("problem_solved") or "idea"
        title = str(item.get("title") or item.get("niche") or item.get("idea_slug") or "Untitled Opportunity").strip()
        target_buyer = str(item.get("target_buyer") or item.get("audience") or title).strip()
        problem_solved = str(
            item.get("problem_solved")
            or item.get("strategy")
            or item.get("niche")
            or title
        ).strip()

        score_value = item.get("score")
        if isinstance(score_value, (int, float)):
            score = float(score_value)
        else:
            rank = item.get("rank")
            score = 1.0 / float(rank) if isinstance(rank, (int, float)) and rank else 0.5

        return {
            "idea_slug": self._slugify(str(idea_source)),
            "title": title,
            "target_buyer": target_buyer,
            "problem_solved": problem_solved,
            "score": score,
        }

    def _infer_category(self, opportunities: list[dict], selected_opportunity) -> str:
        if isinstance(selected_opportunity, dict):
            selected_type = str(selected_opportunity.get("type", "")).strip().lower()
            if selected_type in VALID_CATEGORIES:
                return selected_type

        for item in opportunities:
            inferred_type = str(item.get("type", "")).strip().lower()
            if inferred_type in VALID_CATEGORIES:
                return inferred_type

        return "planner"

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "idea"