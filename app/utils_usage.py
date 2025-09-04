from langsmith import Client
import csv, os
from datetime import datetime

client_ls = Client()

CSV_FILE = "usage_log.csv"
DEFAULT_PROJECT = "TravelPlannerAI"

# CSV header 
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "mode", "input_tokens", "output_tokens", "total_tokens", "cost_usd"
        ])

def get_last_run_usage(project_name: str = DEFAULT_PROJECT):
    """
    Fetch the last run usage from LangSmith project.
    """
    runs = list(client_ls.list_runs(project_name=project_name, limit=1, order="desc"))
    if not runs:
        return {"input_tokens":0, "output_tokens":0, "total_tokens":0, "cost_usd":0.0}
    
    run = runs[0]
    meta = run.extra.get("usage_metadata", {})
    return {
        "input_tokens": meta.get("prompt_tokens", 0),
        "output_tokens": meta.get("completion_tokens", 0),
        "total_tokens": meta.get("total_tokens", 0),
        "cost_usd": meta.get("total_cost", 0.0)
    }

def log_usage(mode: str, project_name: str = DEFAULT_PROJECT):
    """
    Append usage (tokens + cost) into CSV.
    """
    usage = get_last_run_usage(project_name)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            mode,
            usage["input_tokens"],
            usage["output_tokens"],
            usage["total_tokens"],
            usage["cost_usd"]
        ])
