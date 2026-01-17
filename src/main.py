from pathlib import Path
import time
import sys
from typing import Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config import (
    MAX_RUN_RETRIES,
    METRICS_PATH,
    OUTPUT_PATH,
    REQUEST_HEADERS,
    REQUEST_TIMEOUT,
    RUN_BACKOFF_SECONDS,
    URL,
)
from src.utils.filter import (
    dedupe_urls,
    extract_matching_in_network_urls,
)
from src.utils.parsing import iter_reporting_structures
from src.utils.streaming import stream_mrf_lines


def iter_ny_ppo_urls(byte_iter: Iterable[bytes], metrics: dict) -> Iterator[str]:
    for reporting_structure in iter_reporting_structures(byte_iter):
        yield from extract_matching_in_network_urls(
            reporting_structure,
            metrics=metrics,
        )


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, MAX_RUN_RETRIES + 1):
        try:
            start_time = time.monotonic()
            metrics = {
                "total_reporting_plans_parsed": 0,
                "ny_ppo_reporting_plans": 0,
                "urls_from_plan_matches": 0,
                "urls_from_description_matches": 0,
                "unique_urls_written": 0,
            }
            byte_iter = stream_mrf_lines(URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
            urls = dedupe_urls(iter_ny_ppo_urls(byte_iter, metrics))
            temp_path = OUTPUT_PATH.with_name(f"{OUTPUT_PATH.name}.tmp")
            with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
                for url in urls:
                    handle.write(url)
                    handle.write("\n")
                    metrics["unique_urls_written"] += 1
            temp_path.replace(OUTPUT_PATH)
            elapsed = time.monotonic() - start_time
            metrics_text = (
                f"total_reporting_plans_parsed: {metrics['total_reporting_plans_parsed']}\n"
                f"ny_ppo_reporting_plans: {metrics['ny_ppo_reporting_plans']}\n"
                f"urls_from_plan_matches: {metrics['urls_from_plan_matches']}\n"
                f"urls_from_description_matches: {metrics['urls_from_description_matches']}\n"
                f"unique_urls_written: {metrics['unique_urls_written']}\n"
                f"total_run_time_seconds: {elapsed:.2f}\n"
            )
            METRICS_PATH.write_text(metrics_text, encoding="utf-8")
            return
        except Exception:
            if attempt == MAX_RUN_RETRIES:
                raise
            time.sleep(RUN_BACKOFF_SECONDS * (2 ** (attempt - 1)))


if __name__ == "__main__":
    main()
