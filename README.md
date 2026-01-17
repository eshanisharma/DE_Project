## Initial exploration
- I wrote a small script "import gzip.py" in the exploration folder to download the first ~1000 lines of the table of contents file to understand the JSON structure, different fields and what they contain. I could not upload the exploration file to github due to size constraints.

## Answering key questions:
1. How do you handle the file size and format efficiently, when the uncompressed file will exceed memory limitations on most systems?
- The index is a single large JSON object, so I stream the gzip response and parse incrementally with a streaming JSON parser. I used the ijson library for implementing the streaming JSON parser. This avoids loading the full file into memory. I also implemented a simple retry logic with exponential backoff (upto 4 times) if the connection is lost mid process.

2. When you look at your output URL list, which segments of the URL are changing, which segments are repeating, and what might that mean?
- The hostname often repeats. Some examples of patterns are "anthembcbsin.mrf.bcbs.com" or "antm-pt-prod-dataz-nogbd-nophi-us-east1.s3.amazonaws.com"
- The path contains varying identifiers and part numbers. For example "2026-01_720_27Q2_in-network-rates_31_of_57.json.gz" or "2026-01_720_27Q2_in-network-rates_09_of_57.json.gz". This suggests the in-network files are sharded into multiple parts for the same network. They also seem to have a date (YYYY-MM) associated with the file (2026-01) which makes sense since the MRF file is for 2026-01.
- There are also some signed query parameters which are added for access to the files.

3. Is the 'description' field helpful? Is it complete? Does it change relative to 'location'? Is Highmark the same as Anthem?
- The description is sometimes helpful because it includes the network name and region. It allows us to identify some New York plans, but it is not guaranteed to be complete or consistent across all entries. 
- Location often shares a base path with varying part numbers and signed params, but can also change across hostnames.
- Highmark is a separate BCBS affiliate; its presence in Anthem’s index doesn’t mean “not Anthem,” it likely reflects BlueCard/affiliate networks included under Anthem’s reporting.

4. Anthem has an interactive MRF lookup system. This lookup can be used to gather additional information - but it requires you to input the EIN or name of an employer who offers an Anthem health plan: Anthem EIN lookup. How might you find a business likely to be in the Anthem NY PPO? How can you use this tool to confirm if your answer is complete?
- I can use reporting_plans to identify plan names/EINs that include "New York" and "PPO". Then I can query the lookup tool with those EINs or sponsor names to confirm that the returned MRF links align with my extracted URL list. This helps validate that the NY PPO URLs are complete and correctly filtered.

## Solution Summary, Timing, and Tradeoffs
--------------------------------------
Solution summary
- Stream the gzip index, stream-parse reporting_structure items, match NY PPO via reporting_plans with a description fallback, and write a deduped URL list.

Time to write
- Total time : Initial investigation - 30mins
               Coding time - 1 hour
               Validation and testing - 15 mins
               Documentation - 15 mins

Time to run:
- End-to-end runtime on my machine: ~37 mins

Tradeoffs
- Streaming JSON parsing avoids memory issues but cannot easily resume mid-file on connection drops; I added full-run retries instead.
- Matching primarily on reporting_plans aligns with the schema, while description-based fallback helps when plan fields are generic.
- URL dedupe strips query params to collapse signed variants, while the output preserves the original signed URL for downloadability.
- With more time to study healthcare plan nomenclature and MRF conventions, I would refine the matching rules to be more precise and less token-based.


## Additional Notes
---------------
Performance characteristics
- The pipeline is streaming end-to-end (network, gzip, JSON parsing), so memory stays bounded and runtime is dominated by network throughput and JSON tokenization.
- Deduping is O(n) with a hash set; memory grows with the number of unique URLs, which is manageable compared to full file size.

Testing approach
- Unit tests for filtering rules (plan-based and description fallback) with small JSON fixtures.
- Integration test against a small wrapped sample (as done with the first reporting_structure item).

Production Considerations
- Containerize the job and run it on a cloud platform(aws step functions) with a scheduler (e.g., cron, Airflow) with environment-based config.
- Add structured logging, metrics (records processed, runtime, error rates), and alerting.
- Persist intermediate checkpoints or use HTTP range requests to support resume on large files.
- Store outputs in durable storage (e.g., object storage) with versioning and metadata.
- Add tests for parsing/filtering rules and validate against known fixtures or snapshots.

Potential next iterations
- Make token lists configurable by state/network and emit multiple state outputs in one pass.
- Improve resume capabilities using HTTP range requests or checkpointing within the JSON stream.
- Add a lightweight validation step that checks a sample of URLs for reachability.
