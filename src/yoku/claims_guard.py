"""Detect prohibited wording and product facts that contradict the product card."""

import re


def _flexible_phrase_pattern(phrase):
    return re.compile(r"\s+".join(re.escape(part) for part in phrase.split()), re.IGNORECASE)


def _context(text, start, end, radius=35):
    return text[max(0, start - radius):min(len(text), end + radius)]


def check_claims(script, product):
    errors = []
    checked = {
        "prohibited_claims": True,
        "package_weight_g": product["package_weight_g"],
        "servings": product["servings"],
        "dosage_g_per_drink": product["dosage_g_per_drink"],
        "drink_volume_ml": product["drink_volume_ml"],
        "country_of_origin": product["country_of_origin"],
    }
    for phrase in product["prohibited_claims"]:
        for match in _flexible_phrase_pattern(phrase).finditer(script):
            errors.append({
                "type": "prohibited_claim",
                "message": f"Запрещённая формулировка: {phrase}",
                "phrase": match.group(0),
                "position": match.start(),
                "context": _context(script, match.start(), match.end()),
            })

    checks = (
        (
            r"(?:"
            r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(?:г|грамм(?:а|ов)?)\s+(?:в\s+упаковке|смеси)"
            r"|упаковк(?:а|е|и)\s+(\d+(?:[.,]\d+)?)\s*(?:г|грамм(?:а|ов)?)"
            r"|масса\s+упаковки\s+(\d+(?:[.,]\d+)?)\s*(?:г|грамм(?:а|ов)?)"
            r")",
            "package_weight_g",
            "масса упаковки",
        ),
        (r"(?<!\d)(\d+)\s+порци(?:я|и|й)\b", "servings", "количество порций"),
        (r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(?:г|грамм(?:а|ов)?)\s+на\s+напиток", "dosage_g_per_drink", "дозировка"),
        (
            r"(?:"
            r"напиток\s+(?:объ[её]мом\s+)?(\d+(?:[.,]\d+)?)\s*(?:мл|миллилитр(?:а|ов)?)"
            r"|объ[её]м\s+напитка\s+(\d+(?:[.,]\d+)?)\s*(?:мл|миллилитр(?:а|ов)?)"
            r"|для\s+напитка\s+(\d+(?:[.,]\d+)?)\s*(?:мл|миллилитр(?:а|ов)?)"
            r")",
            "drink_volume_ml",
            "объём напитка",
        ),
    )
    for pattern, field, label in checks:
        expected = float(product[field])
        for match in re.finditer(pattern, script, re.IGNORECASE):
            actual_text = next(group for group in match.groups() if group is not None)
            actual = float(actual_text.replace(",", "."))
            if actual != expected:
                errors.append({
                    "type": "incorrect_fact", "field": field,
                    "message": f"Неверный факт ({label}): {match.group(0)}; ожидается {product[field]}.",
                    "position": match.start(), "context": _context(script, match.start(), match.end()),
                })

    country_pattern = re.compile(r"произведен(?:о|а|ы)?\s+в\s+([А-ЯЁA-Z][А-Яа-яЁёA-Za-z-]+)", re.IGNORECASE)
    expected_country = product["country_of_origin"].casefold()
    accepted_countries = {expected_country}
    if expected_country.endswith("ь"):
        accepted_countries.add(expected_country[:-1] + "е")
    for match in country_pattern.finditer(script):
        if match.group(1).casefold() not in accepted_countries:
            errors.append({
                "type": "incorrect_fact", "field": "country_of_origin",
                "message": f"Неверная страна производства: {match.group(1)}; ожидается {product['country_of_origin']}.",
                "position": match.start(), "context": _context(script, match.start(), match.end()),
            })
    return {"status": "FAIL" if errors else "PASS", "errors": errors, "warnings": [], "checked_facts": checked}


class ClaimsGuard:
    def check(self, script, product):
        return check_claims(script, product)
