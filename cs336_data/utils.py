import random
from collections import Counter
from functools import lru_cache

from fasttext import FastText
from fastwarc.warc import ArchiveIterator, WarcRecordType
from resiliparse.extract.html2text import extract_plain_text
from resiliparse.parse.encoding import bytes_to_str, detect_encoding


def extract_text_from_html_bytes(html_bytes: bytes) -> str | None:
    txt = bytes_to_str(html_bytes, detect_encoding(html_bytes))
    return extract_plain_text(txt)


def test_text_extract():
    max_cnt = 3
    warc_path = "local-shared-data/CC/example.warc.gz"
    wet_path = "local-shared-data/CC/example.warc.wet.gz"

    mine = {}
    uris = {}
    with open(warc_path, "rb") as f:
        for record in ArchiveIterator(f, record_types=WarcRecordType.response, parse_http=True):
            if len(mine) >= max_cnt:
                break
            if "text/html" not in (record.http_content_type or ""):
                continue
            mine[record.record_id] = extract_text_from_html_bytes(record.reader.read())
            uris[record.record_id] = record.headers.get("WARC-Target-URI", "")

    wet = {}
    with open(wet_path, "rb") as f:
        for record in ArchiveIterator(f, record_types=WarcRecordType.conversion):
            ref_id = record.headers.get("WARC-Refers-To")
            if ref_id in mine:
                wet[ref_id] = record.reader.read().decode("utf-8", "replace")
                if len(wet) == len(mine):
                    break

    for rec_id, my_text in mine.items():
        print(f"\n>>>>>>>>>> Record ID: {rec_id} | URI: {uris.get(rec_id)}")
        if my_text is not None:
            wet_text = wet.get(rec_id, "")
            print(f">>>>>>>>>> My length: {len(my_text)} | WET length: {len(wet_text)}")
            print(f">>>>>>>>>> My content:\n{my_text}\n")
            print(f">>>>>>>>>> WET content:\n{wet_text}\n")
        else:
            print("Empty content.")


@lru_cache(maxsize=2)
def _get_fasttext_model(model_path: str):
    return FastText.load_model(model_path)


def detect_lang(model_path: str, text: str) -> tuple[str, float]:
    if not text or not text.strip():
        return "unknown", 0.0
    model = _get_fasttext_model(model_path)
    # select 5000 characters, split lines, strip spaces
    clean = " ".join(line.strip() for line in text[:5000].splitlines() if line.strip())
    if not clean:
        return "unknown", 0.0
    out: tuple = model.predict(clean)
    label: str = out[0][0]
    score: float = float(out[1][0])
    return label.replace("__label__", ""), score


def test_lang_detection():
    warc_path = "local-shared-data/CC/example.warc.gz"
    model_path = "local-shared-data/classifiers/lid.176.bin"

    sample_target = 2000
    random.seed(42)

    reservoir = []  # [(record_id, uri, html_bytes), ...]
    seen = 0

    print("Scanning WARC and reservoir-sampling 2000 HTML records...")
    with open(warc_path, "rb") as f:
        for record in ArchiveIterator(f, record_types=WarcRecordType.response, parse_http=True):
            if "text/html" not in (record.http_content_type or ""):
                continue
            seen += 1
            if seen <= sample_target:
                reservoir.append(
                    (
                        record.record_id,
                        record.headers.get("WARC-Target-URI", ""),
                        record.reader.read(),
                    )
                )
            else:
                j = random.randint(0, seen - 1)
                if j < sample_target:
                    reservoir[j] = (
                        record.record_id,
                        record.headers.get("WARC-Target-URI", ""),
                        record.reader.read(),
                    )

            if seen % 5000 == 0:
                print(f"  scanned {seen} HTML records...")

    print(f"Total HTML records scanned: {seen}, sampled: {len(reservoir)}")

    results = []
    for rec_id, uri, html_bytes in reservoir:
        text = extract_text_from_html_bytes(html_bytes)
        if not text or not text.strip():
            continue
        lang, score = detect_lang(model_path, text)
        snippet = " ".join(text[:400].split())  # first 400 characters only
        results.append((rec_id, uri, lang, score, snippet))

    total = len(results)
    if total == 0:
        print("No valid HTML documents extracted.")
        return

    lang_counts = Counter(lang for _, _, lang, _, _ in results)
    en_count = lang_counts["en"]
    print(f"\nValid sampled HTML documents: {total}")
    print(f"Estimated English fraction: {en_count} / {total} ({en_count / total:.2%})")
    print("Top 10 predicted languages:", lang_counts.most_common(10))

    for thresh in [0.5, 0.7, 0.8, 0.9]:
        en_high = sum(1 for _, _, lang, score, _ in results if lang == "en" and score >= thresh)
        print(f"  English with score >= {thresh}: {en_high} ({en_high / total:.2%})")

    sample_size = min(20, total)
    samples = random.sample(results, sample_size)

    print("\n" + "=" * 80)
    print(f"Random {sample_size} examples for manual inspection:")
    print("=" * 80)
    for idx, (rec_id, uri, lang, score, snippet) in enumerate(samples, 1):
        print(f"\n[{idx}/{sample_size}] Pred: {lang} (score={score:.4f}) | URI: {uri}")
        print(f"Record ID: {rec_id}")
        print(f"Snippet: {snippet}")


if __name__ == "__main__":
    # test_text_extract()
    test_lang_detection()
