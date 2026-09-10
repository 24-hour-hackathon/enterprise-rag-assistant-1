import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional

CATEGORY_NAMES = {
    "direct": "Direct Question",
    "semantic_paraphrase": "Semantic Paraphrase",
    "unsupported": "Unsupported Question",
    "out_of_domain": "Out-of-Domain",
    "empty_invalid": "Empty / Invalid Input",
    "source_citation": "Source Citation",
    "source_citation_verification": "Source Citation",
    "reindex_consistency": "Re-index Consistency",
}

class BackendUnavailableError(Exception):
    """Raised when live RAG backend cannot be reached."""
    pass

def check_backend_alive(backend_url: str = "http://127.0.0.1:8000") -> bool:
    """
    Checks if the live backend is reachable.
    """
    clean_url = backend_url.rstrip("/")
    # Try /health endpoint first (instant lightweight response)
    try:
        req = urllib.request.Request(f"{clean_url}/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        pass

    # Try root / docs
    try:
        req = urllib.request.Request(f"{clean_url}/docs", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        pass

    return False

def call_live_backend(question: str, backend_url: str = "http://127.0.0.1:8000", timeout: float = 30.0) -> Dict[str, Any]:
    """
    Calls the LIVE FastAPI RAG backend at POST /api/chat.
    Never uses mock answers or hardcoded keyword replies.
    """
    endpoint = f"{backend_url.rstrip('/')}/api/chat"
    headers = {"Content-Type": "application/json"}
    payload = json.dumps({"question": question}).encode("utf-8")

    req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_sources = data.get("sources", [])
            sources_list = []
            for s in raw_sources:
                if isinstance(s, dict):
                    doc_name = s.get("document") or s.get("filename") or ""
                    if doc_name:
                        sources_list.append(doc_name)
                elif isinstance(s, str):
                    sources_list.append(s)

            return {
                "answer": data.get("answer", ""),
                "has_answer": bool(data.get("has_answer", True)),
                "sources": sources_list,
                "retrieved_sources": sources_list
            }
    except urllib.error.HTTPError as e:
        if e.code in [400, 422]:
            return {
                "answer": "Please provide a valid question. The input was empty or invalid.",
                "has_answer": False,
                "sources": [],
                "retrieved_sources": []
            }
        raise RuntimeError(f"HTTP Error {e.code} querying live RAG endpoint {endpoint}: {e.read().decode('utf-8', errors='ignore')}") from e
    except (urllib.error.URLError, ConnectionRefusedError, TimeoutError) as e:
        raise BackendUnavailableError(f"Live RAG backend unavailable at {backend_url}") from e
    except Exception as e:
        raise RuntimeError(f"Error querying live RAG endpoint {endpoint}: {e}") from e

def mock_rag_pipeline(question: str) -> Dict[str, Any]:
    """
    Offline simulator for unit testing and local validation.
    Used ONLY when --mode mock is explicitly specified.
    """
    cleaned = (question or "").strip().lower()

    # 1. Empty or Invalid Input
    if not cleaned or all(c in "!@#$%^&*()_+{}[]:;`~<>,.?/\\|=- \t\r\n" for c in cleaned):
        return {
            "answer": "Please provide a valid question. The input was empty or invalid.",
            "has_answer": False,
            "sources": [],
            "retrieved_sources": []
        }

    # 2. Out-of-Domain Queries (Baking, Geography, Sports)
    if any(q in cleaned for q in ["france", "cookies", "fifa", "world cup", "recipe", "capital city"]):
        return {
            "answer": "I am sorry, but I can only answer questions related to internal company documentation and policies.",
            "has_answer": False,
            "sources": [],
            "retrieved_sources": []
        }

    # 3. Unsupported Queries (Confidential salary, Pets in office, Intern stock options)
    if any(q in cleaned for q in ["salary", "pet", "dog", "stock option", "intern equity", "salary of the ceo"]):
        return {
            "answer": "I am sorry, but this information is not available in the company documentation.",
            "has_answer": False,
            "sources": [],
            "retrieved_sources": []
        }

    # 4. Subramanya Employee ID
    if "subramanya" in cleaned and ("id" in cleaned or "employee id" in cleaned):
        return {
            "answer": "Subramanya's employee ID is EMP1024 [Source: Employee_Handbook.pdf].",
            "has_answer": True,
            "sources": ["Employee_Handbook.pdf"],
            "retrieved_sources": ["Employee_Handbook.pdf"]
        }

    # 5. Subramanya Vacation / Annual Leave
    if "subramanya" in cleaned and any(w in cleaned for w in ["vacation", "annual leave", "days off"]):
        return {
            "answer": "Subramanya is entitled to 18 days of annual leave / vacation per calendar year [Source: Employee_Handbook.pdf].",
            "has_answer": True,
            "sources": ["Employee_Handbook.pdf"],
            "retrieved_sources": ["Employee_Handbook.pdf"]
        }

    # 6. Casual Leave Policy
    if any(q in cleaned for q in ["casual leave", "casual days off", "leave days", "leave entitlement"]):
        return {
            "answer": "Employees are entitled to 12 days of casual leave per calendar year [Source: Leave_Policy.pdf].",
            "has_answer": True,
            "sources": ["Leave_Policy.pdf"],
            "retrieved_sources": ["Leave_Policy.pdf"]
        }

    # 7. Standard Working Hours
    if any(q in cleaned for q in ["working hours", "work commitment", "scheduled work", "hours are expected"]):
        return {
            "answer": "The standard schedule requires 40 hours per week [Source: Employee_Handbook.pdf].",
            "has_answer": True,
            "sources": ["Employee_Handbook.pdf"],
            "retrieved_sources": ["Employee_Handbook.pdf"]
        }

    # 8. Password Policy
    if any(q in cleaned for q in ["password", "login passwords", "change their login", "mandatory password"]):
        return {
            "answer": "Passwords must be updated every 90 days [Source: IT_Security.pdf].",
            "has_answer": True,
            "sources": ["IT_Security.pdf"],
            "retrieved_sources": ["IT_Security.pdf"]
        }

    # 9. Dinner Expense Policy
    if any(q in cleaned for q in ["expense", "reimbursement", "dinner"]):
        return {
            "answer": "Dinner expense reimbursement requires an itemized receipt submitted within policy guidelines [Source: Expense_Policy.pdf].",
            "has_answer": True,
            "sources": ["Expense_Policy.pdf"],
            "retrieved_sources": ["Expense_Policy.pdf"]
        }

    # Default fallback for unknown supported queries
    return {
        "answer": "Refer to general company guidelines.",
        "has_answer": True,
        "sources": ["Unknown.pdf"],
        "retrieved_sources": ["Unknown.pdf"]
    }

def run_evaluation(
    dataset_path: str = "eval_dataset.json",
    rag_func: Optional[Callable[[str], Dict[str, Any]]] = None,
    mode: str = "mock",
    backend_url: str = "http://127.0.0.1:8000",
    export_path: Optional[str] = "eval_results.json"
) -> Dict[str, Any]:
    """
    Executes the benchmark evaluation suite against the Live backend or Mock double.

    Args:
        dataset_path: Path to evaluation test cases JSON
        rag_func: Optional custom callable taking question -> dict
        mode: "live" or "mock"
        backend_url: URL for live FastAPI RAG backend
        export_path: Output file for dashboard consumption

    Returns:
        Structured evaluation metrics and per-question test records
    """
    mode_normalized = mode.strip().upper()

    # Load evaluation dataset
    try:
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except FileNotFoundError:
        return {"error": f"Dataset file '{dataset_path}' not found."}

    # Determine query function
    if rag_func is not None:
        target_fn = rag_func
    elif mode_normalized == "LIVE":
        # Pre-flight check: Fail clearly if live backend is unreachable
        if not check_backend_alive(backend_url):
            print(f"Live RAG backend unavailable at {backend_url}")
            sys.exit(1)
        target_fn = lambda q: call_live_backend(q, backend_url=backend_url)
    else:
        target_fn = mock_rag_pipeline

    results: List[Dict[str, Any]] = []
    retrieval_correct = 0
    unsupported_correct = 0
    citation_present = 0
    grounded_correct = 0
    total_unanswerable = 0
    total_latency = 0.0
    latencies: List[float] = []

    category_stats: Dict[str, Dict[str, Any]] = {}
    consistency_groups: Dict[str, List[Dict[str, Any]]] = {}

    for item in dataset:
        q_id = item.get("id")
        raw_category = item.get("category", "direct")
        category_label = CATEGORY_NAMES.get(raw_category, raw_category.title())
        question = item.get("question", "")
        expected_src = item.get("expected_source", "")
        expected_behavior = item.get("expected_behavior", "")
        expected_keywords = item.get("expected_keywords", [])
        is_unanswerable = bool(item.get("is_unanswerable", False))
        expected_has_answer = item.get("expected_has_answer", not is_unanswerable)
        consistency_group = item.get("consistency_group")

        # Execute query with high-resolution latency timer
        t_start = time.perf_counter()
        try:
            output = target_fn(question)
        except BackendUnavailableError:
            print(f"Live RAG backend unavailable at {backend_url}")
            sys.exit(1)
        t_end = time.perf_counter()
        latency_sec = round(t_end - t_start, 4)
        total_latency += latency_sec
        latencies.append(latency_sec)

        actual_answer = output.get("answer", "")
        has_answer = bool(output.get("has_answer", True))
        sources = output.get("sources", output.get("retrieved_sources", []))

        failure_reasons = []

        # 1. Check has_answer compliance
        if has_answer != expected_has_answer:
            failure_reasons.append(f"Expected has_answer={expected_has_answer}, got {has_answer}")

        # 2. Check Retrieval Accuracy & Sources
        retrieval_pass = False
        if is_unanswerable:
            total_unanswerable += 1
            # For unsupported/out-of-domain, sources must be empty
            if len(sources) == 0:
                retrieval_pass = True
            else:
                retrieval_pass = False
                failure_reasons.append(f"Expected sources=[], got {sources}")
        else:
            # For supported queries, relevant sources must be returned
            if len(sources) > 0:
                if expected_src and expected_src != "NOT AVAILABLE":
                    retrieval_pass = (expected_src in sources)
                    if not retrieval_pass:
                        failure_reasons.append(f"Expected source '{expected_src}' in sources, got {sources}")
                else:
                    retrieval_pass = True
            else:
                retrieval_pass = False
                failure_reasons.append("Supported question returned empty sources")

        if retrieval_pass:
            retrieval_correct += 1

        # 3. Check Unsupported / Hallucination Detection
        unsupported_pass = True
        if is_unanswerable:
            unsupported_pass = (has_answer is False) and (len(sources) == 0)
            if unsupported_pass:
                unsupported_correct += 1

        # 4. Check Citation Coverage
        has_citation = False
        if not is_unanswerable:
            if len(sources) > 0:
                if expected_src and expected_src != "NOT AVAILABLE":
                    has_citation = (expected_src in sources or expected_src.lower() in actual_answer.lower())
                else:
                    has_citation = True
            if has_citation:
                citation_present += 1
            else:
                failure_reasons.append("Citation missing from sources or answer text")
        else:
            has_citation = (len(sources) == 0)

        # 5. Check Keywords / Factuality (for answerable questions)
        keyword_pass = True
        if not is_unanswerable and expected_keywords:
            keyword_pass = any(kw.lower() in actual_answer.lower() for kw in expected_keywords)
            if not keyword_pass:
                failure_reasons.append(f"Expected keyword(s) {expected_keywords} not found in actual answer")

        # 6. Evaluate Grounded Status & Source Presence
        if is_unanswerable:
            if not has_answer and len(sources) == 0:
                grounded_status = "INVALID_INPUT" if raw_category == "empty_invalid" else "REFUSAL"
                is_grounded = True
            else:
                grounded_status = "UNGROUNDED"
                is_grounded = False
            source_presence = "ABSENT" if len(sources) == 0 else "MISMATCH"
        else:
            if has_answer and retrieval_pass and keyword_pass:
                grounded_status = "GROUNDED"
                is_grounded = True
            else:
                grounded_status = "UNGROUNDED"
                is_grounded = False
            source_presence = "PRESENT" if len(sources) > 0 else "ABSENT"

        if is_grounded:
            grounded_correct += 1

        # 7. Overall Pass / Fail
        overall_pass = len(failure_reasons) == 0
        overall_status = "PASS" if overall_pass else "FAIL"
        failure_msg = "; ".join(failure_reasons) if failure_reasons else ""

        record = {
            # UI display fields (for pandas DataFrame and Pavi's dashboard)
            "Category": category_label,
            "Question": question if question.strip() else f"[EMPTY/BLANK: '{question}']",
            "Expected Behavior": expected_behavior,
            "Actual Answer": actual_answer,
            "has_answer": has_answer,
            "Sources": ", ".join(sources) if sources else "None",
            "Retrieved Source": ", ".join(sources) if sources else "None",
            "Latency": f"{latency_sec:.4f}s",
            "Latency (s)": f"{latency_sec:.4f}",
            "Pass/Fail": overall_status,
            "Status": overall_status,
            "Failure reason": failure_msg,
            "Grounded Status": grounded_status,
            "Source Presence": source_presence,
            "Retrieval Check": "PASS" if retrieval_pass else "FAIL",
            "Citation Check": "PASS" if has_citation else "FAIL",

            # Programmatic / API fields
            "id": q_id,
            "category_raw": raw_category,
            "latency_sec": latency_sec,
            "expected_behavior": expected_behavior,
            "actual_result": actual_answer,
            "is_unanswerable": is_unanswerable,
            "expected_source": expected_src,
            "consistency_group": consistency_group
        }
        results.append(record)

        # Track Category Breakdown
        if category_label not in category_stats:
            category_stats[category_label] = {"total": 0, "passed": 0, "total_latency": 0.0}
        category_stats[category_label]["total"] += 1
        if overall_pass:
            category_stats[category_label]["passed"] += 1
        category_stats[category_label]["total_latency"] += latency_sec

        # Track Consistency Groups
        if consistency_group:
            if consistency_group not in consistency_groups:
                consistency_groups[consistency_group] = []
            consistency_groups[consistency_group].append(record)

    total_q = len(dataset)
    answerable_count = total_q - total_unanswerable
    correct_count = sum(1 for r in results if r["Status"] == "PASS")
    failed_count = total_q - correct_count

    # Evaluate Re-index Consistency
    consistency_passed = 0
    total_groups = len(consistency_groups)
    for grp_name, group_records in consistency_groups.items():
        if len(group_records) > 1:
            first_ans = group_records[0]["Actual Answer"]
            first_src = group_records[0]["Sources"]
            all_match = all(r["Actual Answer"] == first_ans and r["Sources"] == first_src for r in group_records)
            if all_match:
                consistency_passed += 1
        else:
            consistency_passed += 1

    consistency_rate = round((consistency_passed / max(total_groups, 1)) * 100, 1)

    category_breakdown = {}
    for cat, stat in category_stats.items():
        tot = stat["total"]
        pas = stat["passed"]
        avg_lat = round(stat["total_latency"] / max(tot, 1), 4)
        category_breakdown[cat] = {
            "total": tot,
            "passed": pas,
            "failed": tot - pas,
            "pass_rate": round((pas / max(tot, 1)) * 100, 1),
            "avg_latency_sec": avg_lat
        }

    avg_latency = round(total_latency / max(total_q, 1), 4)

    metrics: Dict[str, Any] = {
        "mode": mode_normalized,
        "backend_url": backend_url if mode_normalized == "LIVE" else "MOCK_SIMULATOR",
        "total_test_cases": total_q,
        "total_tested": total_q,
        "passed": correct_count,
        "correct_answers": correct_count,
        "failed": failed_count,
        "pass_rate": round((correct_count / max(total_q, 1)) * 100, 1),
        "retrieval_accuracy": round((retrieval_correct / max(total_q, 1)) * 100, 1),
        "unsupported_detection": round((unsupported_correct / max(total_unanswerable, 1)) * 100, 1),
        "citation_coverage": round((citation_present / max(answerable_count, 1)) * 100, 1),
        "average_latency": avg_latency,
        "avg_latency_sec": avg_latency,
        "grounded_answer_rate": round((grounded_correct / max(total_q, 1)) * 100, 1),
        "reindex_consistency_rate": consistency_rate,
        "category_breakdown": category_breakdown,
        "details": results
    }

    if export_path:
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=4)
        except IOError as e:
            print(f"Warning: Could not save export to {export_path}: {e}")

    return metrics

def load_evaluation_results(results_path: str = "eval_results.json") -> Dict[str, Any]:
    """
    Loads saved evaluation results from disk.
    """
    with open(results_path, "r", encoding="utf-8") as f:
        return json.load(f)

def print_evaluation_report(results: Dict[str, Any]) -> None:
    """
    Prints a clean terminal report formatted for user inspection.
    """
    print("=================================================================")
    print("       ENTERPRISE RAG BENCHMARK EVALUATION REPORT")
    print("=================================================================")
    print(f"MODE:                   {results.get('mode', 'UNKNOWN')}")
    print(f"TOTAL:                  {results.get('total_tested', 0)}")
    print(f"PASSED:                 {results.get('passed', 0)}")
    print(f"FAILED:                 {results.get('failed', 0)}")
    print(f"PASS RATE:              {results.get('pass_rate', 0.0)}%")
    print(f"RETRIEVAL ACCURACY:     {results.get('retrieval_accuracy', 0.0)}%")
    print(f"UNSUPPORTED DETECTION:  {results.get('unsupported_detection', 0.0)}%")
    print(f"CITATION COVERAGE:      {results.get('citation_coverage', 0.0)}%")
    print(f"AVERAGE LATENCY:        {results.get('average_latency', 0.0)}s")
    print(f"GROUNDED ANSWER RATE:   {results.get('grounded_answer_rate', 0.0)}%")
    print(f"RE-INDEX CONSISTENCY:   {results.get('reindex_consistency_rate', 0.0)}%")
    print("=================================================================")
    print("\n--- CATEGORY BREAKDOWN ---")
    for cat, stats in results.get("category_breakdown", {}).items():
        print(f" - {cat:26}: {stats['passed']}/{stats['total']} passed ({stats['pass_rate']}%) | avg {stats['avg_latency_sec']}s")
    print("=================================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enterprise RAG Evaluation Engine")
    parser.add_argument(
        "--mode",
        choices=["live", "mock"],
        default="mock",
        help="Evaluation mode: 'live' (queries FastAPI backend) or 'mock' (offline double)"
    )
    parser.add_argument(
        "--backend-url",
        default="http://127.0.0.1:8000",
        help="FastAPI backend URL (default: http://127.0.0.1:8000)"
    )
    parser.add_argument(
        "--dataset",
        default="eval_dataset.json",
        help="Path to evaluation dataset JSON"
    )
    parser.add_argument(
        "--output",
        default="eval_results.json",
        help="Output JSON path for evaluation results"
    )

    args = parser.parse_args()

    # If live mode requested, perform connectivity check
    if args.mode == "live":
        if not check_backend_alive(args.backend_url):
            print(f"Live RAG backend unavailable at {args.backend_url}")
            sys.exit(1)

    eval_results = run_evaluation(
        dataset_path=args.dataset,
        mode=args.mode,
        backend_url=args.backend_url,
        export_path=args.output
    )

    print_evaluation_report(eval_results)
    print(f"Evaluation completed. Output saved to {args.output}")