
import os
from pathlib import Path
from groq import Groq
from mess_sorter import classify_feedback, write_reports, load_prompt

os.chdir(Path(__file__).resolve().parent)

def main():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("GROQ_API_KEY environment variable is missing.")
        return

    client = Groq(api_key=api_key)
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    system_prompt = load_prompt()
    results = []

    print("\n===== MESS FEEDBACK SORTER =====")
    print("Type 'done' to finish.\n")

    while True:
        feedback = input("Enter feedback: ").strip()

        if feedback.lower() == "done":
            break

        if not feedback:
            continue

        try:
            result = classify_feedback(
                client, model, system_prompt, feedback
            )
            result["feedback"] = feedback
            result.setdefault("needs_manual_review", False)
            results.append(result)
            print("Feedback processed successfully!\n")

        except Exception as e:
            print("Error:", e)

    if results:
        write_reports(results)
        print("\nOutput files generated in this folder:")
        print("results.csv")
        print("urgent.csv")
        print("summary.txt")
    else:
        print("No feedback was processed.")

if __name__ == "__main__":
    main()
