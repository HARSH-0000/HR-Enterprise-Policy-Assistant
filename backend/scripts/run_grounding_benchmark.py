"""Run the fixed 40-question grounding verification ablation benchmark.

From repository root:
  python backend/scripts/run_grounding_benchmark.py --base-url http://localhost:8000

Runs identical questions twice: verification OFF then ON. All other pipeline
stages remain enabled. Results are raw outputs; human review labels are blank.
"""
import argparse
import csv
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "backend" / "evaluation" / "hr_policy_40_questions.json"
OUT = ROOT / "backend" / "evaluation" / "results"


def call_chat(base_url, question, verify):
    payload = {
        "query": question,
        "chat_history": [],
        "verify_grounding": verify,
    }
    request = Request(
        base_url.rstrip("/") + "/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()

    with urlopen(args.base_url.rstrip("/") + "/health", timeout=10) as response:
        if response.status != 200:
            raise SystemExit("Backend health check failed.")

    questions = json.loads(DATASET.read_text(encoding="utf-8"))
    if len(questions) != 40:
        raise SystemExit(f"Expected 40 questions, found {len(questions)}.")

    OUT.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    rows = []

    for verify in (False, True):
        variant = "verification_on" if verify else "verification_off"
        print(f"\\nRunning {variant}")
        for item in questions:
            print(f"Q{item['id']:02d}/40 ...", end=" ", flush=True)
            row = {
                "question_id": item["id"],
                "question": item["question"],
                "variant": variant,
                "answer": "",
                "grounded_flag": "",
                "status": "",
                "sources_json": "[]",
                "request_error": "",
                # Fill these after comparing against the actual policy PDFs.
                "correct": "",
                "unsupported": "",
                "correct_abstention": "",
                "false_refusal": "",
                "review_notes": "",
            }
            try:
                result = call_chat(args.base_url, item["question"], verify)
                row.update({
                    "answer": result.get("response", ""),
                    "grounded_flag": result.get("grounded"),
                    "status": result.get("status", ""),
                    "sources_json": json.dumps(result.get("sources", []), ensure_ascii=False),
                })
                print("OK")
            except Exception as exc:
                row["request_error"] = str(exc)
                row["status"] = "request_error"
                print("FAILED")
            rows.append(row)
            time.sleep(args.delay)

    csv_path = OUT / f"grounding_ablation_{stamp}.csv"
    json_path = OUT / f"grounding_ablation_{stamp}.json"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\\nSaved: {csv_path}\\nSaved: {json_path}")
    print("Do not use the API grounded_flag as the gold unsupported-answer label.")
    print("Manually label unsupported/correct/abstention outcomes using the source policy PDFs.")


if __name__ == "__main__":
    main()
