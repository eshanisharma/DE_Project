from src.utils.streaming import stream_mrf_lines

URL = "https://antm-pt-prod-dataz-nogbd-nophi-us-east1.s3.amazonaws.com/anthem/2026-01-01_anthem_index.json.gz"
OUT_PATH = "anthem_index_first_1000_lines.json"

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "identity",
    }

    with open(OUT_PATH, "wb") as out:
        for i, line in enumerate(stream_mrf_lines(URL, headers=headers, timeout=60)):
            if i >= 1000:
                break
            out.write(line)

if __name__ == "__main__":
    main()
