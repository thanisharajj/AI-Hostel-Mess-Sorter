import csv
import json
import re
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROMPT_FILE = BASE_DIR / "system_prompt.txt"
RESULTS_FILE = BASE_DIR / "results.csv"
URGENT_FILE = BASE_DIR / "urgent.csv"
SUMMARY_FILE = BASE_DIR / "summary.txt"

FIELDS = [
    "feedback_id", "feedback_text", "category", "sentiment",
    "urgent", "reason", "needs_manual_review",
]


def load_prompt():
    return PROMPT_FILE.read_text(encoding="utf-8")


def classify_feedback(client, model, system_prompt, feedback):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": feedback},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)


def fallback_result():
    return {
        "category": "other",
        "sentiment": "neutral",
        "urgent": False,
        "reason": "AI processing was unsuccessful; human verification is required.",
        "needs_manual_review": True,
    }


def safety_net(feedback, result):
    text = feedback.lower()
    safety_patterns = [
        r"\binsect\b", r"\bworm\b", r"\bglass\b", r"\bmetal\b",
        r"\bunsafe water\b", r"\bdirty water\b", r"\bfood poison",
        r"\bvomit", r"\bdiarr", r"\bstomach pain\b",
        r"பூச்சி", r"புழு", r"கண்ணாடி", r"விஷம்", r"வயிற்று வலி",
        r"வாந்தி", r"கெட்டுப்போன",
    ]
    if any(re.search(pattern, text) for pattern in safety_patterns):
        result["urgent"] = True
    return result


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            clean_row = {field: row.get(field, False if field in {"urgent", "needs_manual_review"} else "") for field in FIELDS}
            writer.writerow(clean_row)


def write_reports(results):
    write_csv(RESULTS_FILE, results)
    urgent_rows = [row for row in results if row.get("urgent") is True]
    write_csv(URGENT_FILE, urgent_rows)

    category_counts = Counter(row.get("category", "other") for row in results)
    sentiment_counts = Counter(row.get("sentiment", "neutral") for row in results)
    urgent_count = len(urgent_rows)
    manual_count = sum(bool(row.get("needs_manual_review", False)) for row in results)

    lines = [
        "HOSTEL MESS FEEDBACK SUMMARY",
        "================================",
        f"Total feedback: {len(results)}",
        f"Urgent feedback: {urgent_count}",
        f"Needs manual review: {manual_count}",
        "",
        "CATEGORY BREAKDOWN",
    ]
    lines.extend(f"- {category}: {count}" for category, count in sorted(category_counts.items()))
    lines.extend(["", "SENTIMENT BREAKDOWN"])
    lines.extend(f"- {sentiment}: {count}" for sentiment, count in sorted(sentiment_counts.items()))
    lines.extend([
        "",
        "Note: AI labels are suggestions. The mess committee/warden must review concerns and decide actions.",
    ])
    SUMMARY_FILE.write_text("\n".join(lines), encoding="utf-8")
