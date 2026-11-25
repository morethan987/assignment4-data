import difflib
import random
import re

from fastwarc.warc import ArchiveIterator, WarcRecordType

from cs336_data.utils import extract_text_from_html_bytes

_EMAIL_RE = re.compile(
    r"(?<![.\w%+-])"
    r"[A-Za-z0-9_%+-]+(?:\.[A-Za-z0-9_%+-]+)*"
    r"@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,}"
    r"(?![\w-])(?!\.\w)"
)

_PHONE_RE = re.compile(
    r"(?<![\w.])"
    r"(?:"
    r"(?:\+?1[-.\s]?)?\(\d{3}\)[-.\s]?\d{3}[-.\s]?\d{4}"
    r"|"
    r"(?:\+1[-.\s]?|1[-.\s])?\d{3}[-.\s]\d{3}[-.\s]\d{4}"
    r"|"
    r"(?:\+?1[-.\s]?)?\d{10}"
    r")"
    r"(?![\w])(?!\.\d)"
)

_OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
_IP_RE = re.compile(rf"(?<![\w.])(?:{_OCTET}\.){{3}}{_OCTET}(?![\w])(?!\.\d)")


def mask_emails(text: str) -> tuple[str, int]:
    return _EMAIL_RE.subn("|||EMAIL_ADDRESS|||", text)


def mask_phone_numbers(text: str) -> tuple[str, int]:
    return _PHONE_RE.subn("|||PHONE_NUMBER|||", text)


def mask_ips(text: str) -> tuple[str, int]:
    return _IP_RE.subn("|||IP_ADDRESS|||", text)


def test_mask():
    warc_path = "local-shared-data/CC/example.warc.gz"
    sample_size = 20
    max_pool = 200

    candidates: list[tuple[str, str, str, tuple[int, int, int]]] = []
    with open(warc_path, "rb") as f:
        for record in ArchiveIterator(f, record_types=WarcRecordType.response, parse_http=True):
            if len(candidates) >= max_pool:
                break
            if "text/html" not in (record.http_content_type or ""):
                continue

            raw_text = extract_text_from_html_bytes(record.reader.read())
            if not raw_text:
                continue

            masked_text, n_emails = mask_emails(raw_text)
            masked_text, n_phones = mask_phone_numbers(masked_text)
            masked_text, n_ips = mask_ips(masked_text)

            if n_emails + n_phones + n_ips > 0:
                uri = record.headers.get("WARC-Target-URI") or ""
                candidates.append((uri, raw_text, masked_text, (n_emails, n_phones, n_ips)))

    random.seed(42)
    samples = random.sample(candidates, min(sample_size, len(candidates)))
    print(f"Found {len(candidates)} pages with PII replacements; showing {len(samples)} random examples.\n")

    for idx, (uri, raw_text, masked_text, (n_emails, n_phones, n_ips)) in enumerate(samples, 1):
        print(f"=== [{idx}] {uri} ===")
        print(f"Counts -> emails: {n_emails}, phones: {n_phones}, ips: {n_ips}")

        raw_tokens = raw_text.split()
        masked_tokens = masked_text.split()
        matcher = difflib.SequenceMatcher(None, raw_tokens, masked_tokens)

        shown = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            orig_ctx = " ".join(raw_tokens[max(0, i1 - 5) : min(len(raw_tokens), i2 + 5)])
            mask_ctx = " ".join(masked_tokens[max(0, j1 - 5) : min(len(masked_tokens), j2 + 5)])
            print(f"  Original: {orig_ctx}")
            print(f"  Masked  : {mask_ctx}")
            print("-" * 40)
            shown += 1
            if shown >= 5:
                break
        print()


if __name__ == "__main__":
    test_mask()
