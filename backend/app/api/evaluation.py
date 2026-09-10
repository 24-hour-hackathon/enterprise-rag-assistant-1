import os
import json
import logging
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmarks"])

# Potential paths to find/store evaluation files
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
EVAL_RESULTS_PATHS = [
    PROJECT_ROOT / "evaluation" / "eval_results.json",
    PROJECT_ROOT / "backend" / "data" / "eval_results.json",
    Path("C:/ALL Codings/ydk-repo/eval_results.json"),
]
EVAL_DATASET_PATHS = [
    PROJECT_ROOT / "evaluation" / "eval_dataset.json",
    Path("C:/ALL Codings/ydk-repo/eval_dataset.json"),
]


def _find_eval_results_file() -> Path | None:
    for path in EVAL_RESULTS_PATHS:
        if path.exists():
            return path
    return None


def _find_eval_dataset_file() -> Path | None:
    for path in EVAL_DATASET_PATHS:
        if path.exists():
            return path
    return None


@router.get(
    "/results",
    summary="Get latest evaluation benchmark results"
)
def get_evaluation_results() -> Dict[str, Any]:
    """
    Retrieve the latest computed evaluation results.
    Never invents or mocks numbers; returns 404 if no evaluation has been run yet.
    """
    results_file = _find_eval_results_file()
    if not results_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation results unavailable. Please run the evaluation suite first."
        )

    try:
        with open(results_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error reading evaluation results from {results_file}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read evaluation results: {str(e)}"
        )


@router.post(
    "/run",
    summary="Run live evaluation benchmark suite"
)
def run_evaluation_suite() -> Dict[str, Any]:
    """
    Executes the live evaluation benchmark suite against the running FastAPI RAG backend.
    Saves and returns real performance and grounding metrics.
    """
    dataset_file = _find_eval_dataset_file()
    if not dataset_file:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Evaluation dataset file (eval_dataset.json) not found."
        )

    # Determine export destination
    export_path = PROJECT_ROOT / "evaluation" / "eval_results.json"
    os.makedirs(export_path.parent, exist_ok=True)

    try:
        # Import evaluation engine dynamically
        import sys
        eval_dir = str(PROJECT_ROOT / "evaluation")
        if eval_dir not in sys.path:
            sys.path.insert(0, eval_dir)
        
        from eval_engine import run_evaluation

        metrics = run_evaluation(
            dataset_path=str(dataset_file),
            mode="live",
            backend_url="http://127.0.0.1:8000",
            export_path=str(export_path)
        )

        # Also copy to ydk-repo if available
        try:
            ydk_export = Path("C:/ALL Codings/ydk-repo/eval_results.json")
            if ydk_export.parent.exists():
                with open(ydk_export, "w", encoding="utf-8") as f:
                    json.dump(metrics, f, indent=4)
        except Exception:
            pass

        return metrics

    except Exception as e:
        logger.error(f"Failed to execute live evaluation suite: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation execution failed: {str(e)}"
        )
