#import "@preview/ilm:2.1.1": *
#import "@preview/subpar:0.2.2"

#show: ilm.with(
  title: [CS336 Assignment 4],
  authors: "Morethan",
  date: datetime(year: 2026, month: 11, day: 22),
  abstract: [Language Modeling from Scratch - Filtering Language Modeling Data],
  bibliography: none,
  figure-index: (enabled: false),
  table-index: (enabled: false),
  listing-index: (enabled: false),
)
#set text(lang: "en")
#set page(paper: "a4", margin: (x: 1cm, y: 1cm))
#set enum(numbering: "(a)")

#let response(title: "Response", body) = block(
  stroke: 0.5pt + luma(180),
  inset: 10pt,
  radius: 4pt,
  width: 100%,
  breakable: true,
)[
  #if title != none [*#title:*\ ]
  #body
]

// presudo code block
#let algo-counter = counter("algorithm-line")

#let l(body, indent: 0) = {
  algo-counter.step()
  grid(
    columns: (2em, 1fr),
    gutter: 0.5em,
    align: (right + top, left + top),
    context text(fill: luma(100), size: 0.85em, algo-counter.display()), pad(left: indent * 1.5em, body),
  )
}

#let algorithm(title: none, body) = block(
  width: 100%,
  stroke: (y: 1.2pt + black),
  inset: (y: 0.6em),
  breakable: false,
  {
    algo-counter.update(0)
    set text(size: 0.9em)
    set block(spacing: 1em)
    set par(leading: 0.6em) // soft wrap

    if title != none {
      block(
        width: 100%,
        stroke: (bottom: 0.5pt + black),
        inset: (bottom: 0.5em),
        outset: (bottom: 0.2em),
        text(weight: "bold", size: 1.05em, title),
      )
    }

    set grid(row-gutter: 0.65em)
    body
  },
)


/////////////////////////////////////////////

= Filtering Common Crawl

== Looking at Common Crawl

+ Use the copy of the WARC file provided at the path above. Let's look at the first page in this file. This is a gzipped file, and you can browse its contents with:

  ```bash
  $ zcat local-shared-data/CC/example.warc.gz | less
  ```

  `less` lets you browse the file using keyboard arrows, Page Up, Page Down. To exit, press "q". Look at the very first web page. What is its URL? Is it still accessible? Can you tell what the page seems to be about by looking at the raw HTML?

  *Deliverable*: A 2-3 sentence response.

  #response[
    The URL of the first page is "http://020bld.cn.vauofnj.cn/html/991f998999.html". It's 404 not available now. It's a living tip of how to clean your clothes.
  ]

+ Let's now look at the corresponding WET file:

  ```bash
  $ zcat local-shared-data/CC/example.warc.wet.gz | less
  ```

  Note that the WET files contain HTTP headers (e.g., Content-Length) that are not part of the extracted text contents. If you look at the first example, you will see that it contains text that was extracted from the raw HTML you just saw.

  Notice that much of the extracted text is reminiscent of the HTML structure, and not actually the page's main content. Are there parts of the text you see that you think should have been filtered out by the extractor? Think about the quality of this text as training data: what might go wrong in training a model on text that looks like this? Conversely, what useful information can a model potentially extract from this page?

  *Deliverable*: A 3-4 sentence response.

  #response[
    Yes, there are some titles of navigation buttons which should be filtered out, as well as some adds. The content is broken, hard to read and little knowledge in it. The information can be extracted is only some short word combinations. For some QA page, the useful knowledge such as living tips can be extracted.
  ]

+ What makes a good training example is highly contextual. Describe an application domain for which this example might be useful to have in the training data, and one where it might not be.

  *Deliverable*: A 1-2 sentence response.

  #response[
    If you are going to train a chatbot, the living tips is helpful. But if you are going to train your model to do mathematical reasoning, it's useless.
  ]

+ Let's look at some more examples to get a better sense of what's in the Common Crawl. Look through 25 more WET records. For each record, very briefly comment on the document's language (if you can identify it), the domain name, what type of page it is, etc. How many examples does it take until you see what you'd deem a "high-quality" webpage?

  *Deliverable*: Brief annotations of 25 documents with the document's language, domain, type of page, and any other miscellaneous notes about the document. The number of examples it takes until you see a high-quality example.

  #response[
    Languages includes Chinese, English, Russian. Domain includes hiring, living tips, ads, notice and some sensitive topics. Nearly 50 pages util one high-quality page.
  ]

== HTML to text conversion

+ Write a function that extracts text from a byte string containing raw HTML. Use `resiliparse.extract.html2text.extract_plain_text` to perform the extraction. This function needs a string, so you will need to first decode the byte string into a Unicode string. Be aware that the input byte string might not be encoded in UTF-8, so your function should be able to detect the encoding in case UTF-8 fails. Resiliparse also offers `resiliparse.parse.encoding.detect_encoding()`, which might be useful.

  *Deliverable*: A function that takes a byte string containing HTML and returns a string containing the extracted text. Implement the adapter `[run_extract_text_from_html_bytes]` and make sure it passes `uv run pytest -k test_extract_text_from_html_bytes`.

  #response[
    Success. See `extract_text_from_html_bytes` function in `./cs336_data/utils.py` file.
  ]

+ Run your text extraction function on a single WARC file. Compare its output to the extracted text in the corresponding WET file. What differences and/or similarities do you notice? Which extraction seems better?

  *Deliverable*: 2-3 sentence response comparing and contrasting the text extracted by your own function versus the extracted text in the WET files.

  #response[
    The content from WET files is cleaner than my content. Some markdown syntax and empty lines are filtered out. Run `uv run cs336_data/utils.py` to get the output.
  ]
