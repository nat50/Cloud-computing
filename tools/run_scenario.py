"""Run one test scenario on the live pipeline and record what the report needs.

  python tools/run_scenario.py burst --video data/traffic.mp4 --capacity 4 --label keda

C = --capacity = frames/s one pod handles (measure it with the `capacity` scenario first).
  smoke     1 fps for 60 s                          quick end-to-end check
  capacity  C fps for 3 min (use with 1 fixed pod)  measure C: set --capacity higher than one pod can do
  steady    0.5C 3 min, then 3C 5 min               scenario 1
  burst     0.5C 2 min, 5C 3 min, 0.5C 2 min        scenario 2, and fixed vs KEDA comparison
  idle      3C 2 min, then 10 min nothing           scenario 3: scale-down
  kill      3C 5 min, delete a pod every 30 s       scenario 4: no frame lost
  corrupt   C 5 min, 2% broken images               scenario 5: dead-letter

Writes reports/results/<run_id>_<scenario>_<label>/: run.json, pods.csv (every 5 s), producer.log.
Afterwards:  python tools/collect.py <that folder>
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from common import load_env  # noqa: E402

# scenario: (schedule as [(seconds, fps as multiple of C)], corrupt rate, seconds to keep recording after)
SCENARIOS = {
    "smoke":    ([(60, None)], 0, 60),
    "capacity": ([(180, 1)], 0, 30),
    "steady":   ([(180, 0.5), (300, 3)], 0, 180),
    "burst":    ([(120, 0.5), (180, 5), (120, 0.5)], 0, 180),
    "idle":     ([(120, 3)], 0, 600),
    "kill":     ([(300, 3)], 0, 180),
    "corrupt":  ([(300, 1)], 0.02, 180),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def kubectl(*args: str) -> str:
    return subprocess.run(["kubectl", *args], capture_output=True, text=True).stdout.strip()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scenario", choices=SCENARIOS)
    p.add_argument("--video", required=True)
    p.add_argument("--capacity", type=float, default=1, help="C, frames/s one pod handles")
    p.add_argument("--label", default="keda", help="e.g. keda, fixed1, fixed8")
    args = p.parse_args()
    load_env()
    ns = os.environ["NAMESPACE"]

    segments, corrupt, wait_after = SCENARIOS[args.scenario]
    schedule = [(sec, 1.0 if mult is None else mult * args.capacity) for sec, mult in segments]
    run_id = time.strftime("%Y%m%d-%H%M%S")
    out = ROOT / "reports" / "results" / f"{run_id}_{args.scenario}_{args.label}"
    out.mkdir(parents=True)
    meta = {"run_id": run_id, "scenario": args.scenario, "label": args.label, "capacity": args.capacity,
            "schedule": schedule, "corrupt_rate": corrupt, "start": now(),
            "image": kubectl("get", "deploy", "worker", "-n", ns, "-o",
                             "jsonpath={.spec.template.spec.containers[0].image}")}
    print(f"run {run_id}: {args.scenario} {schedule} -> {out}")

    stop = threading.Event()

    def sample_pods():  # desired and ready worker pods every 5 s
        with (out / "pods.csv").open("w") as f:
            f.write("ts,desired,ready\n")
            while not stop.is_set():
                d, r = (kubectl("get", "deploy", "worker", "-n", ns, "-o",
                                "jsonpath={.spec.replicas} {.status.readyReplicas}").split() + ["0", "0"])[:2]
                f.write(f"{now()},{d},{r}\n")
                f.flush()
                stop.wait(5)

    def kill_pods():  # scenario 4: delete a random running worker pod every 30 s
        while not stop.wait(30):
            pods = kubectl("get", "pods", "-n", ns, "-l", "app=worker", "-o", "name").split()
            if pods:
                pod = random.choice(pods)
                kubectl("delete", pod, "-n", ns, "--wait=false")
                print(f"{now()} deleted {pod}")

    threads = [threading.Thread(target=sample_pods)]
    if args.scenario == "kill":
        threads.append(threading.Thread(target=kill_pods))
    for t in threads:
        t.start()

    cmd = [sys.executable, str(ROOT / "src" / "producer.py"), "--video", args.video, "--run-id", run_id,
           "--schedule", ",".join(f"{s:g}:{f:g}" for s, f in schedule), "--corrupt-rate", str(corrupt)]
    with (out / "producer.log").open("w") as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    print(f"producer done, recording {wait_after}s more (backlog drain / scale-down)...")
    time.sleep(wait_after)
    stop.set()
    for t in threads:
        t.join()

    meta["end"] = now()
    (out / "run.json").write_text(json.dumps(meta, indent=2))
    print(f"next: python tools/collect.py {out.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
