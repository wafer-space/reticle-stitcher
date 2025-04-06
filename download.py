"""
Parallel OAS Downloader

This script reads a manifest CSV (such as 'manifest-gfmpw-0.txt') that contains
commands of the form:

  curl -k 'https://some.url.com...' | base64 -d > output_file.oas

For each line that matches the above pattern, it extracts:
  1. The URL to download
  2. The output OAS filename

Then, it downloads all such OAS files in parallel, decoding each from base64,
and writes them to disk. It periodically prints status updates for each file.

Usage:
    python parallel_oas_downloader.py path/to/manifest-gfmpw-0.txt

Example:
    python parallel_oas_downloader.py manifest-gfmpw-0.txt

The script uses only the standard library (no external dependencies required).
It uses ThreadPoolExecutor from concurrent.futures for parallelism, and the
urllib + base64 libraries for downloading and decoding.

Tests are included as doctests in the functions below.

Author: Your Name
"""

import sys
import re
import csv
import base64
import urllib.request
import concurrent.futures
from typing import List, Tuple


def parse_line_for_download_info(line: str) -> Tuple[str, str] or None:
    """
    Given one line of the manifest CSV, extract the URL and output filename.

    The manifest lines often contain something like:
        ... curl -k 'https://some-domain/path/...' | base64 -d > output_file.oas ...

    If the line matches, return (url, output_filename).
    If it doesn't match, return None.

    >>> parse_line_for_download_info("curl -k 'https://example.com/xyz' | base64 -d > test_output.oas")
    ('https://example.com/xyz', 'test_output.oas')

    >>> parse_line_for_download_info("no match here") is None
    True
    """
    pattern = r"curl\s+-k\s+'([^']+)'.*>\s*(\S+)"
    match = re.search(pattern, line)
    if match:
        url = match.group(1).strip()
        out_file = match.group(2).strip()
        return url, out_file
    return None


def parse_manifest(manifest_path: str) -> List[Tuple[str, str]]:
    """
    Parse the manifest file. It is often a CSV with multiple columns,
    one of which contains 'curl -k ... | base64 -d > ...'.

    We will read each line, ignoring the CSV structure beyond looking
    for the pattern in question. If we find a matching command, we yield
    (url, out_file).

    Returns a list of (url, out_file) pairs.

    >>> import tempfile
    >>> with tempfile.NamedTemporaryFile('w', delete=False) as tf:
    ...     _ = tf.write('A1,001,stuff,curl -k \\'https://test.com/aaa\\' | base64 -d > output1.oas\\n')
    ...     _ = tf.write('B1,002,stuff,unrelated command\\n')
    ...     name = tf.name
    >>> items = parse_manifest(name)
    >>> len(items)
    1
    >>> items[0]
    ('https://test.com/aaa', 'output1.oas')
    """
    results = []
    with open(manifest_path, "r", encoding="utf-8", errors="ignore") as f:
        # We can't rely on normal CSV row-based parsing for the entire line
        # because there's often complicated text in one column. We'll just read line by line.
        for line in f:
            found = parse_line_for_download_info(line)
            if found is not None:
                results.append(found)
    return results


def download_and_decode_base64(url: str, out_file: str, chunk_size: int = 65536) -> None:
    """
    Download the data from 'url' in base64 form, decode on the fly,
    and write to 'out_file'. Prints periodic status messages.

    :param url: The remote URL to fetch (contains base64 data).
    :param out_file: The local file path to write the decoded OAS file.
    :param chunk_size: The number of bytes to read at a time before decoding.
    :return: None

    NOTE: If a large file is served in a non-base64 form, or if the server
    doesn't actually serve base64 data, this will fail. According to the
    manifest specification, the data is indeed base64-encoded.

    This function doesn't return anything but prints status to stdout.

    We do a chunkwise download and decode so we don't hold the entire
    base64-encoded file in memory at once.

    >>> import os
    >>> from unittest.mock import patch, MagicMock
    >>> mock_response = MagicMock()
    >>> encoded = base64.b64encode(b"Hello OAS").decode("ascii")
    >>> mock_response.read.side_effect = [encoded.encode("ascii"), b'']  # Single chunk
    >>> with patch('urllib.request.urlopen', return_value=mock_response):
    ...     out_path = 'test_out.oas'
    ...     download_and_decode_base64('http://test-url', out_path)
    ...     with open(out_path, 'rb') as fh:
    ...         print(fh.read())
    ...     os.remove(out_path)
    b'Hello OAS'
    """
    print(f"Starting download of {url} -> {out_file}")
    bytes_downloaded = 0

    with urllib.request.urlopen(url) as response, open(out_file, "wb") as f:
        decoder = base64.b64decode
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            decoded = decoder(chunk)
            f.write(decoded)
            bytes_downloaded += len(chunk)
            # Print a small status update
            print(f"[{out_file}] Downloaded {bytes_downloaded} bytes (base64 before decoding)...")

    print(f"Finished writing {out_file}")


def download_oas_files_in_parallel(
    download_list: List[Tuple[str, str]],
    max_workers: int = 4
) -> None:
    """
    Given a list of (url, out_file) pairs, download them all in parallel using
    ThreadPoolExecutor. Each download calls 'download_and_decode_base64'.

    :param download_list: A list of (url, filename)
    :param max_workers: number of parallel threads
    :return: None

    This function waits for all downloads to complete.
    """
    print(f"Starting parallel downloads for {len(download_list)} file(s) with {max_workers} workers...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {}
        for (url, out_file) in download_list:
            future = executor.submit(download_and_decode_base64, url, out_file)
            future_to_file[future] = out_file

        for future in concurrent.futures.as_completed(future_to_file):
            out_file = future_to_file[future]
            try:
                future.result()
            except Exception as exc:
                print(f"ERROR: Download failed for {out_file}. Reason: {exc}")
            else:
                print(f"SUCCESS: Finished download for {out_file}")


def main(manifest_path: str, max_workers: int = 4) -> None:
    """
    Main entry point: parse the manifest file, collect all the (url, out_file) pairs,
    and launch parallel downloads.

    :param manifest_path: path to the manifest CSV file
    :param max_workers: number of parallel threads
    :return: None
    """
    # 1. Parse the manifest for download info
    download_list = parse_manifest(manifest_path)
    if not download_list:
        print("No OAS downloads found in the manifest.")
        return

    # 2. Download in parallel
    download_oas_files_in_parallel(download_list, max_workers=max_workers)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parallel_oas_downloader.py <path-to-manifest> [max_workers]")
        sys.exit(1)

    manifest_file = sys.argv[1]
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    main(manifest_file, max_workers=workers)

