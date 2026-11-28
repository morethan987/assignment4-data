import nltk


def _download():
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)


def gopher_filter(text: str) -> bool:
    # if no lines
    lines = text.splitlines()
    if not lines:
        return False

    # over 30% lines end with ...
    ellipsis_lines = sum(1 for line in lines if line.rstrip().endswith("..."))
    if ellipsis_lines / len(lines) > 0.3:
        return False

    # filter pure punctuation
    _download()
    tokens: list[str] = nltk.word_tokenize(text)
    words = [token for token in tokens if any(ch.isalnum() for ch in token)]

    # word count < 50 or > 100,000
    num_words = len(words)
    if num_words < 50 or num_words > 100_000:
        return False

    # averaged word length should in [3, 10]
    mean_word_length = sum(len(word) for word in words) / num_words
    if mean_word_length < 3 or mean_word_length > 10:
        return False

    # the portion that contains at least one alpha word >= 80%
    alpha_words = sum(1 for word in words if any(ch.isalpha() for ch in word))
    return not alpha_words / num_words < 0.8


def inspect_gopher_on_warc(
    warc_path: str = "local-shared-data/CC/example.warc.gz",
    num_samples: int = 20,
    seed: int = 42,
) -> None:
    import random

    from fastwarc.warc import ArchiveIterator, WarcRecordType

    from cs336_data.utils import extract_text_from_html_bytes

    random.seed(seed)
    pool_size = max(num_samples * 5, 100)
    reservoir: list[tuple[str, str, bytes]] = []
    seen = 0

    print(f"Scanning {warc_path} and reservoir-sampling {pool_size} HTML records...")
    with open(warc_path, "rb") as f:
        for record in ArchiveIterator(f, record_types=WarcRecordType.response, parse_http=True):
            if "text/html" not in (record.http_content_type or ""):
                continue
            seen += 1
            item = (
                record.record_id,
                record.headers.get("WARC-Target-URI") or "",
                record.reader.read(),
            )
            if seen <= pool_size:
                reservoir.append(item)
            else:
                j = random.randint(0, seen - 1)
                if j < pool_size:
                    reservoir[j] = item

    extracted: list[tuple[str, str, str]] = []
    for rec_id, uri, html_bytes in reservoir:
        text = extract_text_from_html_bytes(html_bytes)
        if text and text.strip():
            extracted.append((rec_id, uri, text))

    if not extracted:
        print("No valid text extracted from sampled HTML records.")
        return

    samples = random.sample(extracted, min(num_samples, len(extracted)))
    passed_count = 0

    print("\n" + "=" * 80)
    print(f"Evaluating Gopher quality filter on {len(samples)} random WARC examples:")
    print("=" * 80)

    for idx, (rec_id, uri, text) in enumerate(samples, 1):
        passed = gopher_filter(text)
        if passed:
            passed_count += 1

        lines = text.splitlines()
        ellipsis_cnt = sum(1 for line in lines if line.rstrip().endswith("..."))
        ellipsis_ratio = ellipsis_cnt / len(lines) if lines else 1.0

        tokens = nltk.word_tokenize(text)
        words = [t for t in tokens if any(ch.isalnum() for ch in t)]
        num_words = len(words)
        mean_len = sum(len(w) for w in words) / num_words if num_words else 0.0
        alpha_ratio = sum(1 for w in words if any(ch.isalpha() for ch in w)) / num_words if num_words else 0.0

        reasons: list[str] = []
        if ellipsis_ratio > 0.3:
            reasons.append(f"ellipsis={ellipsis_ratio:.1%} > 30%")
        if num_words < 50 or num_words > 100_000:
            reasons.append(f"words={num_words} out of [50, 100000]")
        if num_words > 0 and (mean_len < 3 or mean_len > 10):
            reasons.append(f"mean_len={mean_len:.2f} out of [3, 10]")
        if num_words > 0 and alpha_ratio < 0.8:
            reasons.append(f"alpha_ratio={alpha_ratio:.1%} < 80%")

        status = "PASS" if passed else f"FAIL ({'; '.join(reasons)})"
        preview = " ".join(text[:500].split())

        print(f"\n[{idx}/{len(samples)}] {status}")
        print(f"URI: {uri} | Record ID: {rec_id}")
        print(
            f"Stats: words={num_words}, mean_len={mean_len:.2f}, "
            f"alpha={alpha_ratio:.1%}, ellipsis={ellipsis_cnt}/{len(lines)} ({ellipsis_ratio:.1%})"
        )
        print(f"Snippet: {preview}")

    print("\n" + "=" * 80)
    print(f"Summary: {passed_count}/{len(samples)} passed Gopher filter.")


if __name__ == "__main__":
    inspect_gopher_on_warc()
