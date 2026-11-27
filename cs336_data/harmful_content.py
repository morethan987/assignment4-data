import random
from collections import Counter
from functools import cache

import fasttext
from fastwarc.warc import ArchiveIterator, WarcRecordType

from cs336_data.utils import extract_text_from_html_bytes


@cache
def _load_model(filename: str):
    model_dir = "local-shared-data/classifiers/"
    return fasttext.load_model(model_dir + filename)


def _predict_fasttext(filename: str, text: str) -> tuple[str, float]:
    model = _load_model(filename)
    cleaned_text = text.replace("\n", " ").replace("\r", " ")
    labels, probs = model.predict(cleaned_text)

    label, prob = labels[0], probs[0]
    label = label.removeprefix("__label__")
    return label, float(prob)


def classify_nsfw(text: str) -> tuple[str, float]:
    return _predict_fasttext("dolma_fasttext_nsfw_jigsaw_model.bin", text)


def classify_toxic_speech(text: str) -> tuple[str, float]:
    return _predict_fasttext("dolma_fasttext_hatespeech_jigsaw_model.bin", text)


def test_harmful_content():
    warc_path = "local-shared-data/CC/example.warc.gz"

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
        nsfw_label, nsfw_score = classify_nsfw(text)
        toxic_label, toxic_score = classify_toxic_speech(text)
        snippet = " ".join(text[:400].split())
        results.append((rec_id, uri, nsfw_label, nsfw_score, toxic_label, toxic_score, snippet))

    total = len(results)
    if total == 0:
        print("No valid HTML documents extracted.")
        return

    nsfw_counts = Counter(nl for _, _, nl, _, _, _, _ in results)
    toxic_counts = Counter(tl for _, _, _, _, tl, _, _ in results)

    is_pos = lambda lbl: not lbl.startswith("non")
    nsfw_pos = sum(1 for _, _, nl, _, _, _, _ in results if is_pos(nl))
    toxic_pos = sum(1 for _, _, _, _, tl, _, _ in results if is_pos(tl))
    harmful_any = sum(1 for _, _, nl, _, tl, _, _ in results if is_pos(nl) or is_pos(tl))

    print(f"\nValid sampled HTML documents: {total}")
    print(f"NSFW label counts:  {dict(nsfw_counts)}")
    print(f"Toxic label counts: {dict(toxic_counts)}")
    print(f"Estimated NSFW fraction:   {nsfw_pos} / {total} ({nsfw_pos / total:.2%})")
    print(f"Estimated Toxic fraction:  {toxic_pos} / {total} ({toxic_pos / total:.2%})")
    print(f"Estimated Harmful either:  {harmful_any} / {total} ({harmful_any / total:.2%})")

    for thresh in [0.5, 0.7, 0.8, 0.9, 0.95]:
        n_high = sum(1 for _, _, nl, ns, _, _, _ in results if is_pos(nl) and ns >= thresh)
        t_high = sum(1 for _, _, _, _, tl, ts, _ in results if is_pos(tl) and ts >= thresh)
        either_high = sum(
            1
            for _, _, nl, ns, tl, ts, _ in results
            if (is_pos(nl) and ns >= thresh) or (is_pos(tl) and ts >= thresh)
        )
        print(
            f"  score >= {thresh:.2f}: "
            f"nsfw={n_high} ({n_high / total:.2%}), "
            f"toxic={t_high} ({t_high / total:.2%}), "
            f"either={either_high} ({either_high / total:.2%})"
        )

    sample_size = min(20, total)
    samples = random.sample(results, sample_size)

    print("\n" + "=" * 80)
    print(f"Random {sample_size} examples for manual inspection:")
    print("=" * 80)
    for idx, (rec_id, uri, nl, ns, tl, ts, snippet) in enumerate(samples, 1):
        print(f"\n[{idx}/{sample_size}] NSFW: {nl} ({ns:.4f}) | Toxic: {tl} ({ts:.4f}) | URI: {uri}")
        print(f"Record ID: {rec_id}")
        print(f"Snippet: {snippet}")


if __name__ == "__main__":
    test_harmful_content()
