Flow Overview
-------------
This document explains how the code streams Anthem's index file, parses the large JSON
incrementally, filters NY PPO entries, and writes a deduped URL list.

High-Level Flow
---------------
1. stream_mrf_lines (src/utils/streaming.py) downloads the gzipped JSON over HTTP and
   yields decompressed bytes incrementally.
2. iter_reporting_structures (src/utils/parsing.py) uses ijson to stream-parse the large
   JSON object and yields one reporting_structure item at a time.
3. extract_matching_in_network_urls (src/utils/filter.py) filters reporting_structure items
   by NY + PPO tokens using reporting_plans first, then falls back to in_network_files
   descriptions when plan fields are not informative.
4. dedupe_urls (src/utils/filter.py) normalizes URLs (strips query params) and keeps the
   first-seen URL per file.
5. main (src/main.py) wraps the full run with retries, writes output to a temp file, then
   atomically swaps it into output/final_url_list.
6. main (src/main.py) also writes run metrics to output/metrics.

Key Files
---------
- src/config.py
  - URL: Anthem table of contents URL.
  - REQUEST_HEADERS: HTTP headers for the stream request.
  - REQUEST_TIMEOUT: Request timeout in seconds.
  - OUTPUT_PATH: Output file path for the final URL list.
  - METRICS_PATH: Output file path for run metrics.
  - MAX_RUN_RETRIES / RUN_BACKOFF_SECONDS: Retry settings for full-run retries.

- src/utils/streaming.py
  - stream_mrf_lines(url, headers, timeout) -> Iterable[bytes]
  - Streams a gzip-compressed response and yields decompressed bytes.

- src/utils/parsing.py
  - StreamingBytesReader: wraps a bytes iterator as a file-like object.
  - iter_json_items(byte_iter, path) -> Iterator[Dict]
  - iter_reporting_structures(byte_iter) -> Iterator[Dict]

- src/utils/filter.py
  - extract_matching_in_network_urls(reporting_structure, ...) -> Iterator[str]
  - description_matches(entry, ...) -> bool
  - dedupe_urls(urls) -> Iterator[str]

- src/main.py
  - Iterates over reporting structures, filters NY PPO entries, dedupes URLs, writes output.
  - Writes run metrics to output/metrics and retries the full job on connection drops.

Output
------
- output/final_url_list
  - One URL per line.
  - URLs are deduped by normalized (query-stripped) form, but the original URL is written.
- output/metrics
  - Summary counts for parsed plans, matched plans, URL sources, unique URLs, and runtime.

How to Run
----------
1. Install dependencies:
   pip install -r requirements.txt
2. Run:
   python src/main.py

Notes
-----
- The index file is a single large JSON object. The parser does not load it into memory.
- Matching prioritizes reporting_plans, with a fallback to in_network_files descriptions.
- Full-run retries handle mid-stream connection drops; partial outputs are discarded.
