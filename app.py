import os
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from groq import Groq

from mess_sorter import (
    classify_feedback,
    safety_net,
    fallback_result,
    load_prompt,
    write_reports,
)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-local-secret")
BASE_DIR = Path(__file__).resolve().parent
results = []


@app.route("/")
def index():
    return render_template("index.html", results=results)


@app.route("/process", methods=["POST"])
def process():
    global results
    feedback = request.form.get("feedback", "").strip()

    if not feedback:
        flash("Please type your mess feedback before submitting.", "warning")
        return redirect(url_for("index"))

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        flash("Groq API key is not configured. Set GROQ_API_KEY first.", "danger")
        return redirect(url_for("index"))

    try:
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        client = Groq(api_key=api_key, max_retries=2, timeout=60)
        raw = classify_feedback(client, model, load_prompt(), feedback)

        if not isinstance(raw, dict):
            raise ValueError("The AI returned an invalid response.")

        is_mess_feedback = raw.get("is_mess_feedback")
        if not isinstance(is_mess_feedback, bool):
            raise ValueError("The AI did not return a valid feedback decision.")

        if not is_mess_feedback:
            flash("This does not appear to be meaningful hostel mess feedback. Please try again.", "warning")
            return redirect(url_for("index"))

        result = {
            "category": raw.get("category"),
            "sentiment": raw.get("sentiment"),
            "urgent": raw.get("urgent"),
            "reason": raw.get("reason"),
            "needs_manual_review": False,
        }

        allowed_categories = {
            "food_quality", "hygiene", "quantity", "service",
            "menu", "facilities", "appreciation", "other",
        }
        if result["category"] not in allowed_categories:
            raise ValueError("The AI returned an unsupported category.")
        if result["sentiment"] not in {"positive", "negative", "neutral"}:
            raise ValueError("The AI returned an unsupported sentiment.")
        if not isinstance(result["urgent"], bool):
            raise ValueError("The AI returned an invalid urgent value.")
        if not isinstance(result["reason"], str):
            raise ValueError("The AI returned an invalid reason.")

        result = safety_net(feedback, result)
        result.setdefault("needs_manual_review", False)

        item = {
            "feedback_id": f"WEB{len(results) + 1:03d}",
            "feedback_text": feedback,
            **result,
        }
        results.append(item)
        write_reports(results)
        flash("Your feedback has been analysed successfully.", "success")

    except Exception as error:
        print(f"Feedback processing error: {error}")
        flash("The AI could not process this feedback. Please try again or ask a staff member to review it.", "danger")

    return redirect(url_for("index"))


@app.route("/clear", methods=["POST"])
def clear():
    global results
    results = []
    flash("The results shown on this page have been cleared. Previously downloaded files are not deleted.", "info")
    return redirect(url_for("index"))


@app.route("/download/<filename>")
def download(filename):
    allowed = {"results.csv", "urgent.csv", "summary.txt"}
    if filename not in allowed:
        return "File not found", 404

    path = BASE_DIR / filename
    if not path.exists():
        return "Report has not been generated yet.", 404

    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
