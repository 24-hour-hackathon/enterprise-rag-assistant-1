# Enterprise RAG Evaluation Interface & Integration Guide

This document defines the interface, CLI options, and data formats for the Evaluation Engine, designed for seamless integration with **Pavi's Evaluation Dashboard**.

---

## 1. CLI Execution Modes

The evaluation engine supports both **LIVE** backend testing and **MOCK** offline testing:

### A. Live Evaluation against Real Backend
Sends real HTTP `POST` requests to the running FastAPI service:
```bash
python eval_engine.py --mode live
```
- **Target Endpoint**: `POST http://127.0.0.1:8000/api/chat`
- **Request Body**:
  ```json
  {
    "question": "What is Subramanya's employee ID?"
  }
  ```
- **Expected Backend Response**:
  ```json
  {
    "answer": "Subramanya's employee ID is EMP1024 [Source: Employee_Handbook.pdf].",
    "has_answer": true,
    "sources": ["Employee_Handbook.pdf"]
  }
  ```
- **Backend Availability Guarantee**: If `http://127.0.0.1:8000` is unreachable, the runner fails immediately with:
  ```text
  Live RAG backend unavailable at http://127.0.0.1:8000
  ```
  It will **never** silently fall back to mock mode.

### B. Mock Evaluation (Offline / Unit Testing)
Runs offline against simulated responses for instant CI/CD and verification without network calls:
```bash
python eval_engine.py --mode mock
```

---

## 2. In-Memory Python API for Pavi's Dashboard

```python
from eval_engine import run_evaluation, load_evaluation_results

# 1. Run live evaluation
metrics = run_evaluation(mode="live", backend_url="http://127.0.0.1:8000")

# 2. Or run offline mock evaluation
metrics = run_evaluation(mode="mock")

# 3. Or load cached results from file
cached = load_evaluation_results("eval_results.json")

# Access top-level metrics
mode = metrics["mode"]                             # "LIVE" or "MOCK"
total = metrics["total_tested"]                    # 26
passed = metrics["passed"]                         # 26
failed = metrics["failed"]                         # 0
pass_rate = metrics["pass_rate"]                   # 100.0 (%)
retrieval_acc = metrics["retrieval_accuracy"]      # 100.0 (%)
unsupported_det = metrics["unsupported_detection"]  # 100.0 (%)
citation_cov = metrics["citation_coverage"]        # 100.0 (%)
avg_latency = metrics["average_latency"]           # float (seconds)
grounded_rate = metrics["grounded_answer_rate"]    # 100.0 (%)

# Render table in Pandas / Streamlit
import pandas as pd
df = pd.DataFrame(metrics["details"])
```

---

## 3. Evaluated Test Categories

The dataset in `eval_dataset.json` covers 26 test cases across 7 categories:

| Category Key | Display Category | Example Query | Expected Behavior |
|---|---|---|---|
| `direct` | **Direct Question** | `"What is Subramanya's employee ID?"` | Return `EMP1024`, `has_answer=true`, source citation |
| `semantic_paraphrase` | **Semantic Paraphrase** | `"How many vacation days does Subramanya get every year?"` | Identify `18 days` / annual leave under paraphrase |
| `unsupported` | **Unsupported Question** | `"What is Subramanya's salary?"` | Refuse query, `has_answer=false`, `sources=[]` |
| `out_of_domain` | **Out-of-Domain** | `"What is the recipe for chocolate chip cookies?"` | Refuse non-enterprise query, `has_answer=false`, `sources=[]` |
| `source_citation` | **Source Citation** | `"Which document governs weekly employee working hours?"` | Return `Employee_Handbook.pdf` in sources |
| `empty_invalid` | **Empty / Invalid Input** | `""` or `"!@#$%^&*()"` | Handle safely, `has_answer=false`, `sources=[]` |
| `reindex_consistency` | **Re-index Consistency** | Paired queries with matching `consistency_group` | Deterministic invariance across indexing runs |

---

## 4. `eval_results.json` Output Schema

```json
{
    "mode": "LIVE",
    "backend_url": "http://127.0.0.1:8000",
    "total_test_cases": 26,
    "total_tested": 26,
    "passed": 26,
    "correct_answers": 26,
    "failed": 0,
    "pass_rate": 100.0,
    "retrieval_accuracy": 100.0,
    "unsupported_detection": 100.0,
    "citation_coverage": 100.0,
    "average_latency": 0.0452,
    "avg_latency_sec": 0.0452,
    "grounded_answer_rate": 100.0,
    "reindex_consistency_rate": 100.0,
    "category_breakdown": {
        "Direct Question": {
            "total": 5,
            "passed": 5,
            "failed": 0,
            "pass_rate": 100.0,
            "avg_latency_sec": 0.0421
        }
    },
    "details": [
        {
            "Category": "Direct Question",
            "Question": "What is Subramanya's employee ID?",
            "Expected Behavior": "Return employee ID EMP1024 with has_answer=true and Employee_Handbook.pdf citation",
            "Actual Answer": "Subramanya's employee ID is EMP1024 [Source: Employee_Handbook.pdf].",
            "has_answer": true,
            "Sources": "Employee_Handbook.pdf",
            "Retrieved Source": "Employee_Handbook.pdf",
            "Latency": "0.0421s",
            "Latency (s)": "0.0421",
            "Pass/Fail": "PASS",
            "Status": "PASS",
            "Failure reason": "",
            "Grounded Status": "GROUNDED",
            "Source Presence": "PRESENT",
            "Retrieval Check": "PASS",
            "Citation Check": "PASS",
            "id": 1,
            "category_raw": "direct",
            "latency_sec": 0.0421,
            "is_unanswerable": false,
            "expected_source": "Employee_Handbook.pdf",
            "consistency_group": null
        }
    ]
}
```

---

## 5. Dashboard Table Compatibility

`pd.DataFrame(metrics["details"])` exposes both UI columns and programmatic fields:

- **Display Columns**: `Category`, `Question`, `Expected Behavior`, `Actual Answer`, `has_answer`, `Sources`, `Latency`, `Pass/Fail`, `Failure reason`, `Grounded Status`, `Source Presence`
- **Legacy Styler Columns**: `Retrieval Check`, `Citation Check`, `Status` (allows `df.style.map` or `df.style.applymap` in `dashboard.py` without errors)
- **Programmatic Keys**: `id`, `category_raw`, `latency_sec`, `is_unanswerable`, `expected_source`, `consistency_group`
