"""Turn a finished run into numbers and charts. Run ~1 minute after the run, BEFORE deleting the cluster.

  python tools/collect.py reports/results/<run_dir>                 one run
  python tools/collect.py --compare reports/results/*_burst_*        fixed vs KEDA comparison chart

Adds to the run folder:
  summary.csv    published, processed, written twice, dead-lettered, lost (must be 0), latency p50/p95
  frames.csv     one row per frame (from BigQuery detections_dedup)
  backlog.csv    Pub/Sub undelivered messages per minute (from Cloud Monitoring)
  stats.json     pod-hours, cost, latency, and for burst: seconds until an extra pod was ready
  timeline.png   pods and backlog over time
  latency.png    publish -> result time of every frame
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from common import load_env  # noqa: E402

# GKE Autopilot us-central1: 1 vCPU (0.0445 USD/h) + 2 GiB (2 x 0.0049 USD/h) per pod
POD_HOUR_USD = 0.0445 + 2 * 0.0049

SUMMARY_SQL = """
WITH pub AS (SELECT DISTINCT frame_id FROM `{ds}.frames_published_v` WHERE frame_id LIKE @p),
     det AS (SELECT frame_id, COUNT(*) n FROM `{ds}.detections` WHERE frame_id LIKE @p GROUP BY frame_id),
     dead AS (SELECT DISTINCT frame_id FROM `{ds}.dead_letters_v` WHERE frame_id LIKE @p),
     lat AS (SELECT TIMESTAMP_DIFF(processed_at, published_at, MILLISECOND) ms
             FROM `{ds}.detections_dedup` WHERE frame_id LIKE @p)
SELECT (SELECT COUNT(*) FROM pub) published,
       (SELECT COUNT(*) FROM det) processed,
       (SELECT COUNTIF(n > 1) FROM det) written_twice,
       (SELECT COUNT(*) FROM dead) dead_lettered,
       (SELECT COUNT(*) FROM pub WHERE frame_id NOT IN (SELECT frame_id FROM det)
                                   AND frame_id NOT IN (SELECT frame_id FROM dead)) lost,
       (SELECT APPROX_QUANTILES(ms, 100)[OFFSET(50)] FROM lat) e2e_p50_ms,
       (SELECT APPROX_QUANTILES(ms, 100)[OFFSET(95)] FROM lat) e2e_p95_ms
"""
FRAMES_SQL = """
SELECT frame_id, worker_pod, delivery_attempt, num_objects, download_ms, infer_ms, published_at, processed_at,
       TIMESTAMP_DIFF(processed_at, published_at, MILLISECOND) e2e_ms
FROM `{ds}.detections_dedup` WHERE frame_id LIKE @p ORDER BY published_at
"""


def from_bigquery(run_id: str, out: Path) -> None:
    from google.cloud import bigquery

    client = bigquery.Client(project=os.environ["PROJECT_ID"])
    ds = f"{os.environ['PROJECT_ID']}.{os.environ['DATASET']}"
    cfg = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("p", "STRING", f"%-{run_id}-%")])
    summary = client.query(SUMMARY_SQL.format(ds=ds), job_config=cfg).to_dataframe()
    summary.to_csv(out / "summary.csv", index=False)
    print(summary.to_string(index=False))
    client.query(FRAMES_SQL.format(ds=ds), job_config=cfg).to_dataframe().to_csv(out / "frames.csv", index=False)


def from_monitoring(start: datetime, end: datetime, out: Path) -> None:
    from google.cloud import monitoring_v3

    series = monitoring_v3.MetricServiceClient().list_time_series(request={
        "name": f"projects/{os.environ['PROJECT_ID']}",
        "filter": 'metric.type="pubsub.googleapis.com/subscription/num_undelivered_messages" '
                  f'AND resource.labels.subscription_id="{os.environ["SUBSCRIPTION"]}"',
        "interval": monitoring_v3.TimeInterval(start_time=start, end_time=end),
        "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
    })
    rows = [(pt.interval.end_time.isoformat(), pt.value.int64_value) for ts in series for pt in ts.points]
    pd.DataFrame(sorted(rows), columns=["ts", "backlog"]).to_csv(out / "backlog.csv", index=False)


def read(path: Path, dates: list[str], cols: list[str]) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(path)
    for c in dates:
        df[c] = pd.to_datetime(df[c], utc=True, format="ISO8601")
    return df


def charts_and_stats(out: Path, meta: dict) -> dict:
    pods = read(out / "pods.csv", ["ts"], ["ts", "desired", "ready"])
    frames = read(out / "frames.csv", ["published_at", "processed_at"],
                  ["frame_id", "worker_pod", "delivery_attempt", "num_objects", "download_ms",
                   "infer_ms", "published_at", "processed_at", "e2e_ms"])
    backlog = read(out / "backlog.csv", ["ts"], ["ts", "backlog"])
    title = f"{meta['scenario']} / {meta['label']} / {meta['run_id']}"

    fig, ax = plt.subplots(figsize=(10, 4))
    if len(pods):
        ax.step(pods["ts"], pods["desired"], where="post", label="pods desired")
        ax.step(pods["ts"], pods["ready"], where="post", label="pods ready")
        ax.legend(loc="upper left")
    ax.set_ylabel("pods")
    if len(backlog):
        ax2 = ax.twinx()
        ax2.plot(backlog["ts"], backlog["backlog"], "o-", color="tab:orange", ms=3, label="backlog")
        ax2.set_ylabel("undelivered messages")
        ax2.legend(loc="upper right")
    ax.set_title(title)
    fig.autofmt_xdate()
    fig.savefig(out / "timeline.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    if len(frames):
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.scatter(frames["published_at"], frames["e2e_ms"] / 1000, s=3, alpha=0.4)
        ax.set_ylabel("publish -> result (s)")
        ax.set_title(title)
        fig.autofmt_xdate()
        fig.savefig(out / "latency.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    if len(pods):
        hours = pods["ts"].diff().dt.total_seconds().fillna(0) / 3600
        pod_hours = float((pods["desired"].shift().fillna(0) * hours).sum())
        max_pods = int(pods["desired"].max())
    else:
        pod_hours, max_pods = 0.0, 0
    stats = {"run_id": meta["run_id"], "scenario": meta["scenario"], "label": meta["label"],
             "max_pods": max_pods, "pod_hours": round(pod_hours, 3),
             "cost_usd": round(pod_hours * POD_HOUR_USD, 4)}
    if len(frames):
        stats["e2e_p95_s"] = round(frames["e2e_ms"].quantile(0.95) / 1000, 1)
        stats["infer_avg_ms"] = round(frames["infer_ms"].mean(), 1)
        stats["processed_per_s_max"] = int(frames.set_index("processed_at").resample("10s").size().max()) / 10
    if meta["scenario"] == "burst":  # load jumps after the first segment
        t = datetime.fromisoformat(meta["start"]) + timedelta(seconds=meta["schedule"][0][0])
        base = pods[pods["ts"] <= t]["ready"].max()
        extra = pods[(pods["ts"] > t) & (pods["ready"] > base)]
        stats["scale_up_s"] = round((extra["ts"].iloc[0] - t).total_seconds()) if len(extra) else None
    (out / "stats.json").write_text(json.dumps(stats, indent=2))
    return stats


def compare(dirs: list[Path]) -> None:
    stats = sorted((json.loads((d / "stats.json").read_text()) for d in dirs), key=lambda s: s["label"])
    labels = [s["label"] for s in stats]
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4))
    a.bar(labels, [s.get("e2e_p95_s", 0) for s in stats])
    a.set_title("latency p95 (s)")
    b.bar(labels, [s["cost_usd"] for s in stats], color="tab:orange")
    b.set_title("cost of the run (USD)")
    for ax in (a, b):
        ax.bar_label(ax.containers[0], fmt="%.3g")
    target = dirs[0].parent.parent / "figures" / f"compare_{stats[0]['scenario']}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=150, bbox_inches="tight")
    pd.DataFrame(stats).to_csv(target.with_suffix(".csv"), index=False)
    print(f"wrote {target} and .csv")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run_dirs", nargs="+", type=Path)
    p.add_argument("--compare", action="store_true")
    args = p.parse_args()
    if args.compare:
        return compare(args.run_dirs)

    load_env()
    out = args.run_dirs[0]
    meta = json.loads((out / "run.json").read_text())
    start = datetime.fromisoformat(meta["start"])
    from_bigquery(meta["run_id"], out)
    from_monitoring(start - timedelta(minutes=2), datetime.fromisoformat(meta["end"]) + timedelta(minutes=3), out)
    print(json.dumps(charts_and_stats(out, meta), indent=2))


if __name__ == "__main__":
    main()
