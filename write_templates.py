"""Write all Day Designer-inspired planner templates."""
import os

TDIR = "src/etsy/templates"

# ─── cover.html.j2 ───────────────────────────────────────────────────────────
cover = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{{ css }}</style>
<style>
/* ── Cover-specific ────────────────────────────────────────────── */
.covr-wrap {
    display: flex;
    flex-direction: column;
    height: 11in;
    overflow: hidden;
}
.covr-panel {
    background: var(--primary);
    flex-shrink: 0;
    height: 5.4in;
    display: flex;
    flex-direction: column;
    padding: 0.52in 0.78in 0.45in 0.78in;
}
.covr-brand-top {
    font-family: var(--body-font);
    font-size: 6.5pt;
    font-weight: 700;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.45);
    margin-bottom: 0.18in;
}
.covr-gold-bar {
    width: 0.4in;
    height: 2pt;
    background: var(--secondary);
    margin-bottom: 0.28in;
}
.covr-title {
    font-family: var(--heading-font);
    font-size: 44pt;
    font-weight: 700;
    color: white;
    line-height: 1.06;
    flex: 1;
    padding-right: 0.5in;
}
.covr-audience {
    font-family: var(--body-font);
    font-size: 10pt;
    color: rgba(255,255,255,0.62);
    letter-spacing: 0.04em;
    margin-bottom: 12pt;
}
.covr-badge {
    display: inline-block;
    border: 0.7pt solid rgba(255,255,255,0.32);
    padding: 4pt 11pt;
    font-family: var(--body-font);
    font-size: 6.5pt;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.65);
    align-self: flex-start;
}
.covr-body {
    flex: 1;
    background: white;
    padding: 0.3in 0.78in 0.22in 0.78in;
    overflow: hidden;
}
.covr-inside-label {
    font-family: var(--body-font);
    font-size: 6.5pt;
    font-weight: 700;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 6pt;
}
.covr-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.07in 0.22in;
    margin-top: 0.12in;
}
.covr-item {
    width: calc(49% - 0.11in);
    display: flex;
    align-items: flex-start;
    gap: 8pt;
}
.covr-dot {
    width: 4.5pt;
    height: 4.5pt;
    border-radius: 50%;
    background: var(--secondary);
    flex-shrink: 0;
    margin-top: 4pt;
}
.covr-item-name {
    font-family: var(--body-font);
    font-size: 8.5pt;
    font-weight: 700;
    color: var(--dark);
    margin-bottom: 1.5pt;
    line-height: 1.2;
}
.covr-item-desc {
    font-family: var(--body-font);
    font-size: 7.5pt;
    color: var(--mid);
    line-height: 1.3;
}
.covr-footer {
    flex-shrink: 0;
    height: 0.44in;
    background: var(--background);
    border-top: 0.5pt solid var(--line);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0.78in;
}
.covr-footer-brand {
    font-family: var(--heading-font);
    font-size: 9.5pt;
    font-weight: 400;
    color: var(--dark);
    letter-spacing: 0.03em;
}
.covr-footer-meta {
    font-family: var(--body-font);
    font-size: 7pt;
    color: var(--muted);
    text-align: right;
    letter-spacing: 0.06em;
}
</style>
</head>
<body>
<div class="covr-wrap">
    <!-- Primary color hero panel -->
    <div class="covr-panel">
        <div class="covr-brand-top">Betwixt &amp; Between Co.</div>
        <div class="covr-gold-bar"></div>
        <div class="covr-title">{{ title }}</div>
        <div class="covr-audience">{{ audience }}</div>
        <div class="covr-badge">{{ page_count }}&nbsp; Pages &nbsp;&#183;&nbsp; Digital Download</div>
    </div>

    <!-- White body: What's Inside -->
    <div class="covr-body">
        <div class="covr-inside-label">What's Inside</div>
        <div class="gold-rule" style="width:0.45in; margin-bottom:0.06in;"></div>
        <div class="covr-grid">
            {% for s in sections %}
            <div class="covr-item">
                <div class="covr-dot"></div>
                <div>
                    <div class="covr-item-name">{{ s.name }}</div>
                    <div class="covr-item-desc">{{ s.purpose }}</div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Footer brand bar -->
    <div class="covr-footer">
        <div class="covr-footer-brand">Betwixt &amp; Between Co.</div>
        <div class="covr-footer-meta">{{ title }}&nbsp;&nbsp;&#183;&nbsp;&nbsp;Digital Download</div>
    </div>
</div>
</body>
</html>
"""

# ─── worksheet.html.j2 ───────────────────────────────────────────────────────
worksheet = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{{ css }}</style>
<style>
/* ── Worksheet-specific ── */
.ws-page {
    display: flex;
    flex-direction: column;
    height: 11in;
    overflow: hidden;
}
.ws-main {
    display: flex;
    gap: 0.22in;
    flex: 1;
    padding: 0.12in 0.65in 0;
    overflow: hidden;
}
.ws-left  { flex: 53; overflow: hidden; }
.ws-right { flex: 42; overflow: hidden; }
.ws-footer {
    flex-shrink: 0;
    padding: 0.1in 0.65in 0.1in;
    border-top: 0.7pt solid var(--line);
}
.sched-row {
    display: flex;
    align-items: flex-end;
    gap: 5pt;
    margin-bottom: 0.028in;
}
.sched-time {
    font-family: var(--body-font);
    font-size: 7pt;
    font-weight: 700;
    color: var(--muted);
    width: 0.42in;
    text-align: right;
    flex-shrink: 0;
    padding-bottom: 2pt;
    line-height: 1;
}
.sched-accent {
    width: 3pt;
    height: 100%;
    flex-shrink: 0;
    background: var(--secondary);
    margin-bottom: 2pt;
    align-self: flex-end;
    height: 10pt;
}
</style>
</head>
<body>
<div class="ws-page">

    <!-- Header -->
    <div class="header-bar">
        <div class="theme-label">{{ section_name }}</div>
        <div class="page-title">{{ title }}</div>
        <div class="page-num">{{ page_number }}&nbsp;/&nbsp;{{ page_count }}</div>
    </div>
    <div class="accent-strip"></div>

    <!-- Date + Energy row -->
    <div class="content-zone" style="padding-bottom:0.06in;">
        <div class="field-row">
            <span class="field-label">Date</span>
            <div class="field-line" style="max-width:1.55in;"></div>
            <span class="field-label" style="margin-left:0.16in;">Day</span>
            <div class="field-line" style="max-width:1.15in;"></div>
            <span class="field-label" style="margin-left:0.2in;">Energy</span>
            <div class="dot-row" style="margin-left:4pt; margin-bottom:2pt;">
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
            </div>
        </div>
    </div>
    <div class="gold-rule" style="margin:0 0.65in 0.06in;"></div>

    <!-- Main two-column area -->
    <div class="ws-main">

        <!-- LEFT: Priorities + To Do -->
        <div class="ws-left">
            <div class="section-heading">Today&#39;s Top 3</div>
            {% for i in range(1, 4) %}
            <div class="top3-row">
                <div class="priority-badge">{{ i }}</div>
                <div class="top3-check"></div>
                <div class="line" style="flex:1; margin-bottom:0;"></div>
            </div>
            {% endfor %}

            <div style="margin-top:0.13in;">
                <div class="section-heading">To Do</div>
                {% for _ in range(7) %}
                <div class="check-row">
                    <div class="check-box"></div>
                    <div class="line" style="flex:1; margin-bottom:0;"></div>
                </div>
                {% endfor %}
            </div>

            <div style="margin-top:0.13in;">
                <div class="section-heading">Brain Dump</div>
                {% for _ in range(4) %}
                <div class="line"></div>
                {% endfor %}
            </div>
        </div>

        <!-- RIGHT: Hourly schedule -->
        <div class="ws-right">
            <div class="section-heading">Schedule</div>
            {% set slots = ["6 AM","7 AM","8 AM","9 AM","10 AM","11 AM","12 PM","1 PM","2 PM","3 PM","4 PM","5 PM","6 PM","7 PM","8 PM"] %}
            {% for slot in slots %}
            <div class="sched-row">
                <span class="sched-time">{{ slot }}</span>
                <div class="sched-accent"></div>
                <div class="line" style="flex:1; margin-bottom:0;"></div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Three-column footer: Notes | Grateful | Evening -->
    <div class="ws-footer">
        <div class="footer-cols">
            <div class="footer-col">
                <div class="section-heading">Notes</div>
                {% for _ in range(4) %}
                <div class="line-sm"></div>
                {% endfor %}
            </div>
            <div class="footer-col">
                <div class="section-heading">Grateful For</div>
                {% for _ in range(4) %}
                <div class="line-sm"></div>
                {% endfor %}
            </div>
            <div class="footer-col">
                <div class="section-heading">Evening Plans</div>
                {% for _ in range(4) %}
                <div class="line-sm"></div>
                {% endfor %}
            </div>
        </div>
    </div>

</div>
</body>
</html>
"""

# ─── schedule.html.j2 ────────────────────────────────────────────────────────
schedule = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{{ css }}</style>
<style>
/* ── Schedule-specific ── */
.sch-page {
    display: flex;
    flex-direction: column;
    height: 11in;
    overflow: hidden;
}
.sch-grid-wrap {
    flex: 1;
    padding: 0 0.65in;
    overflow: hidden;
}
.sch-footer {
    flex-shrink: 0;
    padding: 0.1in 0.65in 0.1in;
    border-top: 0.7pt solid var(--line);
}
.sch-row {
    display: flex;
    align-items: stretch;
    border-top: 0.4pt solid var(--line);
    min-height: 0.42in;
}
.sch-time {
    width: 0.52in;
    flex-shrink: 0;
    font-family: var(--body-font);
    font-size: 7pt;
    font-weight: 700;
    color: var(--muted);
    text-align: right;
    padding: 4pt 6pt 0 0;
    line-height: 1;
}
.sch-accent {
    width: 3.5pt;
    flex-shrink: 0;
    background: var(--secondary);
    opacity: 0.6;
}
.sch-write {
    flex: 1;
    padding: 3pt 4pt 0;
}
</style>
</head>
<body>
<div class="sch-page">

    <!-- Header -->
    <div class="header-bar">
        <div class="theme-label">{{ section_name }}</div>
        <div class="page-title">{{ title }}</div>
        <div class="page-num">{{ page_number }}&nbsp;/&nbsp;{{ page_count }}</div>
    </div>
    <div class="accent-strip"></div>

    <!-- Focus + Date row -->
    <div class="content-zone" style="padding-bottom:0.06in;">
        <div class="field-row">
            <span class="field-label">Today&#39;s Focus</span>
            <div class="field-line"></div>
        </div>
        <div class="field-row">
            <span class="field-label">Date</span>
            <div class="field-line" style="max-width:1.5in;"></div>
            <span class="field-label" style="margin-left:0.18in;">Energy</span>
            <div class="dot-row" style="margin-left:4pt; margin-bottom:2pt;">
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
            </div>
        </div>
    </div>
    <div class="gold-rule" style="margin:0 0.65in 0.04in;"></div>

    <!-- Full-day time grid -->
    <div class="sch-grid-wrap">
        {% set slots = body if body else ["5 AM","6 AM","7 AM","8 AM","9 AM","10 AM","11 AM","12 PM","1 PM","2 PM","3 PM","4 PM","5 PM","6 PM","7 PM","8 PM","9 PM","10 PM"] %}
        {% for slot in slots %}
        <div class="sch-row">
            <div class="sch-time">{{ slot }}</div>
            <div class="sch-accent"></div>
            <div class="sch-write"></div>
        </div>
        {% endfor %}
    </div>

    <!-- Footer: Morning intentions | Evening wins -->
    <div class="sch-footer">
        <div class="footer-cols">
            <div class="footer-col">
                <div class="section-heading">Morning Intentions</div>
                {% for _ in range(3) %}
                <div class="line-sm"></div>
                {% endfor %}
            </div>
            <div class="footer-col">
                <div class="section-heading">Evening Wins</div>
                {% for _ in range(3) %}
                <div class="line-sm"></div>
                {% endfor %}
            </div>
            <div class="footer-col">
                <div class="section-heading">Notes &amp; Follow-Ups</div>
                {% for _ in range(3) %}
                <div class="line-sm"></div>
                {% endfor %}
            </div>
        </div>
    </div>

</div>
</body>
</html>
"""

# ─── tracker.html.j2 ─────────────────────────────────────────────────────────
tracker = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{{ css }}</style>
<style>
/* ── Tracker-specific ── */
.trk-table { width: 100%; border-collapse: collapse; }
.trk-table th, .trk-table td { text-align: center; vertical-align: middle; padding: 0; }
.trk-table th {
    font-family: var(--body-font);
    font-size: 6pt;
    font-weight: 700;
    color: white;
    letter-spacing: 0.06em;
    padding: 5pt 0;
    background: var(--primary);
}
.th-habit { text-align: left !important; padding-left: 5pt; width: 1.45in; }
.td-habit {
    text-align: left;
    padding: 4.5pt 0 4.5pt 5pt;
    font-family: var(--body-font);
    font-size: 8pt;
    color: var(--dark);
    border-bottom: 0.4pt solid var(--line);
    width: 1.45in;
}
.td-day  { border-bottom: 0.4pt solid var(--line); padding: 3pt 1pt; }
.td-pct  { border-bottom: 0.4pt solid var(--line); font-family: var(--body-font); font-size: 7pt; color: var(--muted); padding: 3pt 2pt; width: 0.3in; }
.th-pct  { width: 0.3in; }
.trk-circle {
    width: 10pt;
    height: 10pt;
    border-radius: 50%;
    border: 1pt solid var(--secondary);
    display: inline-block;
}
</style>
</head>
<body>
<div class="page">

    <!-- Header -->
    <div class="header-bar">
        <div class="theme-label">{{ section_name }}</div>
        <div class="page-title">{{ title }}</div>
        <div class="page-num">{{ page_number }}&nbsp;/&nbsp;{{ page_count }}</div>
    </div>
    <div class="accent-strip"></div>

    <!-- Month / Year / Intention -->
    <div class="content-zone" style="padding-bottom:0.07in;">
        <div class="field-row">
            <span class="field-label">Month</span>
            <div class="field-line" style="max-width:1.4in;"></div>
            <span class="field-label" style="margin-left:0.22in;">Year</span>
            <div class="field-line" style="max-width:0.75in;"></div>
            <span class="field-label" style="margin-left:0.22in;">Intention</span>
            <div class="field-line"></div>
        </div>
    </div>
    <div class="gold-rule" style="margin:0 0.65in 0.08in;"></div>

    <!-- Habit grid -->
    <div class="content-zone" style="padding-top:0; padding-bottom:0.1in;">
        {% set habits = body if body else ["Habit 1","Habit 2","Habit 3","Habit 4","Habit 5","Habit 6","Habit 7"] %}
        <table class="trk-table">
            <thead>
                <tr>
                    <th class="th-habit">Habit</th>
                    {% for d in range(1, 32) %}<th style="width:0.195in;">{{ d }}</th>{% endfor %}
                    <th class="th-pct">%</th>
                </tr>
            </thead>
            <tbody>
                {% for habit in habits %}
                <tr>
                    <td class="td-habit">{{ habit }}</td>
                    {% for _ in range(31) %}
                    <td class="td-day"><div class="trk-circle"></div></td>
                    {% endfor %}
                    <td class="td-pct">&nbsp;</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="gold-rule" style="margin:0 0.65in 0.08in;"></div>

    <!-- Monthly reflection -->
    <div class="content-zone" style="padding-top:0;">
        <div class="card-tint">
            <div class="card-label-dark">Monthly Reflection</div>
            <div class="footer-cols">
                <div class="footer-col" style="border-left:none; padding-left:0;">
                    <div class="section-heading">What worked?</div>
                    {% for _ in range(3) %}
                    <div class="line-sm"></div>
                    {% endfor %}
                </div>
                <div class="footer-col">
                    <div class="section-heading">What to improve?</div>
                    {% for _ in range(3) %}
                    <div class="line-sm"></div>
                    {% endfor %}
                </div>
                <div class="footer-col">
                    <div class="section-heading">Next month&#39;s focus</div>
                    {% for _ in range(3) %}
                    <div class="line-sm"></div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

</div>
</body>
</html>
"""

# ─── reflection.html.j2 ──────────────────────────────────────────────────────
reflection = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{{ css }}</style>
</head>
<body>
<div class="page">

    <!-- Header -->
    <div class="header-bar">
        <div class="theme-label">{{ section_name }}</div>
        <div class="page-title">{{ title }}</div>
        <div class="page-num">{{ page_number }}&nbsp;/&nbsp;{{ page_count }}</div>
    </div>
    <div class="accent-strip"></div>

    <!-- Date + Mood + Overall -->
    <div class="content-zone" style="padding-bottom:0.06in;">
        <div class="field-row">
            <span class="field-label">Date</span>
            <div class="field-line" style="max-width:1.7in;"></div>
            <span class="field-label" style="margin-left:0.22in;">Mood</span>
            <div class="dot-row" style="margin-left:4pt; margin-bottom:2pt; gap:5pt;">
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
            </div>
            <span class="field-label" style="margin-left:0.28in;">Overall</span>
            <div class="dot-row" style="margin-left:4pt; margin-bottom:2pt; gap:5pt;">
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
                <div class="dot-circle"></div>
            </div>
        </div>
    </div>
    <div class="gold-rule" style="margin:0 0.65in 0.08in;"></div>

    <!-- Question cards with numbered gold badges -->
    <div class="content-zone" style="padding-top:0; padding-bottom:0.06in;">
        {% set questions = body if body else ["What went well today?","What challenged you?","What will you do differently?","What are you proud of?"] %}
        {% for q in questions %}
        <div style="display:flex; align-items:flex-start; gap:8pt; margin-bottom:0.1in;">
            <div class="priority-badge" style="margin-top:1pt; flex-shrink:0;">{{ loop.index }}</div>
            <div style="flex:1;">
                <div class="section-heading" style="margin-bottom:4pt;">{{ q }}</div>
                {% for _ in range(3) %}
                <div class="line"></div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="gold-rule" style="margin:0 0.65in 0.08in;"></div>

    <!-- Gratitude + Affirmation -->
    <div class="content-zone" style="padding-top:0;">
        <div class="footer-cols">
            <div class="footer-col" style="border-left:none; padding-left:0; flex:1.2;">
                <div class="section-heading">Gratitude</div>
                {% for _ in range(4) %}
                <div class="check-row">
                    <div class="check-box"></div>
                    <div class="line" style="flex:1; margin-bottom:0;"></div>
                </div>
                {% endfor %}
            </div>
            <div class="footer-col" style="flex:1.5;">
                <div class="section-heading">Tonight&#39;s Affirmation</div>
                <div class="card-filled" style="padding:0.1in 0.14in; margin-bottom:0; min-height:0.8in;">
                    <div class="line-white"></div>
                    <div class="line-white"></div>
                    <div class="line-white"></div>
                </div>
            </div>
        </div>
    </div>

</div>
</body>
</html>
"""

# ─── calendar.html.j2 ────────────────────────────────────────────────────────
calendar = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{{ css }}</style>
<style>
/* ── Calendar-specific ── */
.cal-page {
    display: flex;
    flex-direction: column;
    height: 11in;
    overflow: hidden;
}
.cal-body {
    flex: 1;
    padding: 0 0.65in 0;
    overflow: hidden;
}
.cal-footer {
    flex-shrink: 0;
    padding: 0.1in 0.65in 0.1in;
    border-top: 0.7pt solid var(--line);
}
</style>
</head>
<body>
<div class="cal-page">

    <!-- Header -->
    <div class="header-bar">
        <div class="theme-label">{{ section_name }}</div>
        <div class="page-title">{{ title }}</div>
        <div class="page-num">{{ page_number }}&nbsp;/&nbsp;{{ page_count }}</div>
    </div>
    <div class="accent-strip"></div>

    <!-- Month + Intention -->
    <div class="content-zone" style="padding-bottom:0.06in;">
        <div class="field-row">
            <span class="field-label">Month</span>
            <div class="field-line" style="max-width:1.6in;"></div>
            <span class="field-label" style="margin-left:0.22in;">Year</span>
            <div class="field-line" style="max-width:0.75in;"></div>
            <span class="field-label" style="margin-left:0.22in;">Monthly Intention</span>
            <div class="field-line"></div>
        </div>
    </div>
    <div class="gold-rule" style="margin:0 0.65in 0.06in;"></div>

    <!-- Calendar grid -->
    <div class="cal-body">
        <table class="cal-table">
            <thead>
                <tr>
                    <th>Sun</th>
                    <th>Mon</th>
                    <th>Tue</th>
                    <th>Wed</th>
                    <th>Thu</th>
                    <th>Fri</th>
                    <th>Sat</th>
                </tr>
            </thead>
            <tbody>
                {% for row in range(5) %}
                <tr>
                    {% for col in range(7) %}
                    {% set day = row * 7 + col + 1 %}
                    {% if day <= 31 %}
                    <td class="cal-cell">
                        <span class="cal-date-num">{{ day }}</span>
                        <div class="cal-write-line"></div>
                        <div class="cal-write-line"></div>
                        <div class="cal-write-line"></div>
                        <div class="cal-write-line"></div>
                    </td>
                    {% else %}
                    <td class="cal-cell cal-empty"></td>
                    {% endif %}
                    {% endfor %}
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Footer: Monthly Goals + Key Dates -->
    <div class="cal-footer">
        <div class="footer-cols">
            <div class="footer-col" style="border-left:none; padding-left:0;">
                <div class="section-heading">Monthly Goals</div>
                {% for _ in range(3) %}
                <div class="check-row">
                    <div class="check-box"></div>
                    <div class="line" style="flex:1; margin-bottom:0;"></div>
                </div>
                {% endfor %}
            </div>
            <div class="footer-col">
                <div class="section-heading">Key Dates</div>
                {% for _ in range(3) %}
                <div class="line-sm"></div>
                {% endfor %}
            </div>
            <div class="footer-col">
                <div class="section-heading">Notes</div>
                {% for _ in range(3) %}
                <div class="line-sm"></div>
                {% endfor %}
            </div>
        </div>
    </div>

</div>
</body>
</html>
"""

files = {
    "cover.html.j2":      cover,
    "worksheet.html.j2":  worksheet,
    "schedule.html.j2":   schedule,
    "tracker.html.j2":    tracker,
    "reflection.html.j2": reflection,
    "calendar.html.j2":   calendar,
}

for name, content in files.items():
    path = os.path.join(TDIR, name)
    with open(path, "w") as f:
        f.write(content)
    print(f"  ✓ {name}: {len(content):,} chars, {content.count(chr(10))} lines")

print("Done.")
