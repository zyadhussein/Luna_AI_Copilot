from database import SessionLocal
from ai.agent import run_agent
import json
import time
from datetime import datetime
from pathlib import Path

EVAL_CASES = [
    {
        "name": "pet_policy",
        "input": "Are dogs allowed?",
        "expected_status": "completed",
        "expected_tools": [
        "retrieve_policy"
        ],
        "must_contain": [
            "pets are not allowed",
            "approved by management",
        ],
    },
    {
        "name": "availability_and_quote",
        "input": (
            "Is apartment 1204 available from "
            "2026-12-20 to 2026-12-23 for 2 guests, "
            "and how much would it cost?"
        ),
        "expected_status": "completed",
        "expected_tools": [
        "check_availability",
        "calculate_quote"
        ],
        "must_contain": [
            "available",
            "1050",
        ],
    },
    {
        "name": "cancel_requires_confirmation",
        "input": "Cancel booking id 2.",
        "expected_status": "confirmation_required",
        "expected_tool": "cancel_booking",
    },
    {
        "name": "unknown_booking",
        "input": "Tell me the details of booking id 999999.",
        "expected_status": "completed",
        "expected_tools": ["get_booking"],
        "exact_tools": True,
    },
]
def evaluate_case(case, result):
    passed = True
    reasons = []

    if result.get("status") != case["expected_status"]:
        passed = False
        reasons.append(
            f"Expected status {case['expected_status']}, "
            f"got {result.get('status')}"
        )

    if "expected_tools" in case:
        actual_tools = [
            item["tool"]
            for item in result.get("tool_trace", [])
        ]

        expected_tools = case["expected_tools"]

        if case.get("exact_tools"):
            if actual_tools != expected_tools:
                passed = False
                reasons.append(
                    f"Expected exactly {expected_tools}, "
                    f"but tools used were {actual_tools}"
                )

        else:
            for expected_tool in expected_tools:
                if expected_tool not in actual_tools:
                    passed = False
                    reasons.append(
                        f"Expected tool {expected_tool}, "
                        f"but tools used were {actual_tools}"
                    )
    answer = result.get("answer", "").lower()

    if "must_contain" in case:
        for text in case["must_contain"]:
            if text.lower() not in answer:
                passed = False
                reasons.append(
                    f'Missing expected text: "{text}"'
                )

    if "must_contain_any" in case:
        if not any(
            text.lower() in answer
            for text in case["must_contain_any"]
        ):
            passed = False
            reasons.append(
                "Did not contain any acceptable expected phrase"
            )

    return passed, reasons
def run_evals():
    db = SessionLocal()

    passed_count = 0
    eval_results = []
    try:
        for case in EVAL_CASES:
            print(f"\nRunning: {case['name']}")

            start_time = time.perf_counter()

            result = run_agent(
                case["input"],
                db
            )

            latency_seconds = (
                time.perf_counter() - start_time
            )

            passed, reasons = evaluate_case(
                case,
                result
            )

            if passed:
                passed_count += 1
                print("PASS")
            else:
                print("FAIL")

                for reason in reasons:
                    print(f"  - {reason}")

            print("Result:", result)
            eval_results.append({
                "name": case["name"],
                "passed": passed,
                "latency_seconds": round(
                    latency_seconds,
                    3
                ),
                "tool_trace": result.get(
                    "tool_trace",
                    []
                ),
                "reasons": reasons,
                "result": result,
            })

    finally:
        db.close()

    total = len(EVAL_CASES)
    success_rate = (
        passed_count / total
    ) * 100
    average_latency = sum(
        item["latency_seconds"]
        for item in eval_results
    ) / total
    report = {
        "timestamp": datetime.now().isoformat(),
        "model": "google/gemma-4-e4b",
        "total_cases": total,
        "passed_cases": passed_count,
        "success_rate": success_rate,
        "average_latency_seconds": round(
            average_latency,
            3
        ),
        "cases": eval_results,
    }
    reports_dir = Path(
        "evals/reports"
    )

    reports_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    report_path = (
        reports_dir
        / f"eval_{timestamp}.json"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False
        )
    print("\n----------------------")
    print(
        f"Passed: {passed_count}/{total}"
    )
    print(
        f"Success rate: "
        f"{success_rate:.1f}%"
    )
    print(
        f"Average latency: "
        f"{average_latency:.2f}s"
    )
    print(
        f"Report saved to: "
        f"{report_path}"
    )


if __name__ == "__main__":
    run_evals()