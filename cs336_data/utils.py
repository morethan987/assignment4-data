from fastwarc.warc import ArchiveIterator, WarcRecordType
from resiliparse.extract.html2text import extract_plain_text
from resiliparse.parse.encoding import bytes_to_str, detect_encoding


def extract_text_from_html_bytes(html_bytes: bytes) -> str | None:
    txt = bytes_to_str(html_bytes, detect_encoding(html_bytes))
    return extract_plain_text(txt)


if __name__ == "__main__":
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
