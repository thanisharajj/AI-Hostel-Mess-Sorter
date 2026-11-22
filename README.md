# MessMate – Hostel Mess Feedback Sorter

A Flask website that accepts typed feedback in English, Tamil, or Tanglish and uses Groq AI to classify it.

## Setup (Windows)

1. Install Python 3.10 or newer.
2. Open Command Prompt in this project folder.
3. Install packages:

   ```powershell
   py -m pip install -r requirements.txt
   ```

4. Set your own Groq API key in the terminal (do not share it):

   ```powershell
   $env:GROQ_API_KEY="YOUR_OWN_GROQ_API_KEY"
   $env:GROQ_MODEL="openai/gpt-oss-120b"
   ```

5. Start the website:

   ```powershell
   py app.py
   ```

6. Open http://127.0.0.1:5000 in your browser.

## Example tests

- `The chicken tastes good` – should be accepted as positive.
- `The rice is undercooked` – should be accepted as negative.
- `There is an insect in the sambar` – should be marked urgent.
- `hello how are you` – should be rejected as unrelated.
- `sambar` – should be rejected because it gives no opinion or concern.

## Reports

The website creates `results.csv`, `urgent.csv`, and `summary.txt` in this folder. Keep a backup if you need to preserve earlier reports; each new session writes reports based on the current website session.

## Important

- Your friend must use their own Groq API key.
- Never upload or send an API key in the ZIP or GitHub repository.
- AI labels are suggestions. Human staff must review urgent concerns and decide what action to take.
- This is a local demonstration app, not a public production deployment.
