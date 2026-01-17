import gzip
from typing import Dict, Iterable

import requests


def stream_mrf_lines(
    url: str,
    headers: Dict[str, str],
    timeout: int = 60,
) -> Iterable[bytes]:
    """
    Stream lines from a gzip-compressed MRF file at the index file URL.
    """
    with requests.Session() as session:
        session.trust_env = False
        session.headers.update(headers)
        with session.get(
            url,
            stream=True,
            timeout=timeout,
            allow_redirects=True,
        ) as response:
            response.raise_for_status()
            response.raw.decode_content = False
            with gzip.GzipFile(fileobj=response.raw) as gz:
                for line in gz:
                    yield line
