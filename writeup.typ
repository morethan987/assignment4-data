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

== Language identification

+ Write a function that will take a Unicode string and identify the main language that is present in this string. Your function should return a pair, containing an identifier of the language and a score between 0 and 1 representing its confidence in that prediction.

  *Deliverable:* A function that performs language identification, giving its top language prediction and a score. Implement the adapter `[run_identify_language]` and make sure it passes both tests in `uv run pytest -k test_identify_language`. Note that these tests assume a particular string identifier for English ("en") and Chinese ("zh"), so your test adapter should perform any applicable re-mapping, if necessary.

  #response[Sucess. See `detect_lang` function in `./cs336_data/utils.py` file.]

+ The behavior of language models at inference time largely depends on the data they were trained on. As a result, issues in the data filtering pipeline can result in problems downstream. What issues do you think could arise from problems in the language identification procedure? In a higher-stakes scenario (such as when deploying a user-facing product), how would you go about mitigating these issues?

  *Deliverable:* A 2-5 sentence response.

  #response[
    Some text could be a mixture of different languages which may affect the model to generate the similar mixed text making the user confused. To mitigate this from a perspective of deploying, we can prompt the model to speak the same language with user's in system prompt or re-generate the answer if the languages is mismatched.
  ]

+ Run your language identification system on text extracted from the WARC files (via your previously-implemented text extraction function). Manually identify the language in 20 random examples and compare your labels with the classifier predictions. Report any classifier errors. What fraction of documents are English? Based on your observations, what would be a suitable classifier confidence threshold to use in filtering?

  *Deliverable:* A 2-5 sentence response.

  #response[
    Across 1,944 valid HTML documents randomly sampled from the 19,869 HTML records in the WARC file, 41.82% (813/1,944) are predicted to be English. Manually inspecting 20 random examples showed that all 20 classifier predictions (covering en, nl, de, fr, it, es, ru, te, hu, ja, and zh) matched the actual language of the extracted text, with no outright classification errors observed (note that example \#8 comes from a `.no` domain whose extracted text is in German). However, pages dominated by navigation menus, lists, phone numbers, or spam received noticeably lower confidence scores (e.g., Spanish \#5 at 0.3962, English business listing \#12 at 0.5736, and Chinese spam \#18 at 0.5775), whereas clean English prose pages scored between 0.78 and 0.94. Based on these observations, a confidence threshold around 0.6–0.7 (e.g., 0.65) is suitable for filtering, as it filters out noisy low-confidence boilerplate while retaining genuine English articles, avoiding the steep recall drop seen at $>= 0.8$ (17.85%) or $>= 0.9$ (7.05%).

    Run `uv run cs336_data/utils.py` to get the result.
  ]

== Personally identifiable information

+ Write a function to mask out emails. Your function will take a string as input, and replace all instances of email addresses with the string `|||EMAIL_ADDRESS|||`. To detect email addresses, you can look up regular expressions that do this reliably.

  *Deliverable*: A function that replaces all email addresses in a given string with the string `|||EMAIL_ADDRESS|||`, returning a pair containing both the new string and the number of instances that were masked. Implement the adapter `run_mask_emails` and make sure it passes all tests in `uv run pytest -k test_mask_emails`.

  #response[Success. See `_EMAIL_RE` in `cs336_data/mask_pii.py` file.]

+ Write a function to mask out phone numbers. Your function will take a string as input, and replace all instances of phone numbers with the string `|||PHONE_NUMBER|||`. Doing this reliably can be extremely challenging, as phone numbers might be written in an extremely diverse set of formats, but you should try to capture at least the most common phone number formats used in the United States, and be robust to minor syntactic deviations.

  *Deliverable*: A function that replaces phone numbers in a given string with the string `|||PHONE_NUMBER|||`, returning a pair containing both the new string and the number of instances that were masked. Implement the adapter `run_mask_phone_numbers` and make sure it passes `uv run pytest -k test_mask_phones`.

  #response[Success. See `_PHONE_RE` in `cs336_data/mask_pii.py` file.]

+ Write a function to mask out IP addresses. For this problem, it is enough to focus on IPv4 addresses (4 numbers up to 255 separated by points). Your function will take a string as input, and replace all instances of IP addresses with the string `|||IP_ADDRESS|||`.

  *Deliverable*: A function that replaces IPv4 addresses in a given string with the string `|||IP_ADDRESS|||`, returning a pair containing both the new string and the number of instances that were masked. Implement the adapter `run_mask_ips` and make sure it passes `uv run pytest -k test_mask_ips`.

  #response[Success. See `_IP_RE` in `cs336_data/mask_pii.py` file.]

+ What problems do you think might arise downstream in a language model when these filters are naively applied on the training set? How might you mitigate these issues?

  *Deliverable*: A 2-5 sentence response.

  #response[
    Naively replacing PII with fixed placeholder tokens may cause the model to frequently generate these tokens, since they become common patterns in the training data. It also removes potentially useful contextual information and may introduce artifacts into the training distribution. To mitigate these issues, we can use dedicated special tokens for different PII types, filter or down-weight heavily masked samples, and preserve the surrounding context whenever possible.
  ]

+ Run your PII masking functions on text extracted from the WARC files (via your previously-implemented text extraction function). Look through 20 random examples where a replacement was made; give some examples of false positives and false negatives.

  *Deliverable*: A 2-5 sentence response.

  #response[
    I observed several false negatives, particularly for international phone numbers that do not follow common US formatting conventions. For example, a Chinese webpage contained phone numbers such as `057163263666` and `0571-63280333`, which were not detected by our regex. Minor formatting variations, such as full-width parentheses and additional whitespace, can also cause missed matches. No obvious false positives were found in the inspected examples, although numeric identifiers could potentially be incorrectly classified as phone numbers.
  ]

== Harmful content

+ Write a function to detect NSFW content.

  *Deliverable:* A function that labels a given string as containing NSFW content or not, returning a pair containing both the label and a confidence score. Implement the adapter `[run_classify_nsfw]` and make sure it passes `uv run pytest -k test_classify_nsfw`. Note that this test is just a sanity check, taken from the Jigsaw dataset, but by no means asserts that your classifier is accurate, which you should validate.

  #response[Success. See `classify_nsfw` function in `cs336_data/harmful_content.py` file.]

+ Write a function to detect toxic speech.

  *Deliverable:* A function that labels a given string as consisting of toxic speech or not, returning a pair containing both the label and a confidence score. Implement the adapter `[run_classify_toxic_speech]` and make sure it passes `uv run pytest -k test_classify_toxic_speech`. Again, this test is just a sanity check, also taken from Jigsaw.

  #response[Success. See `classify_toxic_speech` function in `cs336_data/harmful_content.py` file.]

+ What problems do you think might arise downstream in a language model when these filters applied to create the training set? How might you mitigate these issues?

  *Deliverable:* A 2-5 sentence response.

  #response[
    Applying Jigsaw-trained NSFW and toxic speech filters can introduce dataset bias and degrade downstream language model coverage, as lexical/n-gram classifiers frequently false-positive on marginalized dialects (such as African American English), LGBTQ+ topics, medical or educational material, and sensitive historical or news discussions. Overly aggressive filtering can also reduce the model's ability to recognize or moderate harmful language in downstream safety tasks because it rarely sees those phenomena during pretraining. To mitigate these issues, we can use conservative high-confidence thresholds rather than blind binary filtering, filter by language before applying English-trained classifiers, and audit borderline predictions or downsample sensitive-but-benign domains instead of discarding them outright.
  ]

+ Run your harmful content filters on text extracted from the WARC files (via your previously-implemented text extraction function). Look through 20 random examples and compare the classifier predictions to your own judgments. Report any classifier errors. What fraction of documents are harmful? Based on your observations, what would be suitable classifier fidence threshold(s) to use in filtering?

  *Deliverable:* A 2-5 sentence response.

  #response[
    Run `uv run cs336_data/harmful_content.py` to get the results.

    Across 1,944 valid HTML documents extracted from `example.warc.gz`, the classifiers labeled 0.15% (3/1,944) as NSFW, 0.87% (17/1,944) as toxic, and 0.93% (18/1,944) as harmful overall. In the 20 randomly sampled documents, all 20 were predicted as `non-nsfw` and `non-toxic`, which matches manual inspection (0 classification errors): the samples consist of benign pages such as real estate listings, news, and directories, plus one Chinese lottery-spam page that is spam rather than NSFW or toxic speech, though the toxic classifier showed noticeably lower confidence on it (`0.5912`). Because many sampled pages are non-English while the Jigsaw models were trained on English comments, low-confidence predictions are more prone to noise out of domain. Based on the threshold sweep, a relatively high confidence threshold around `0.80`–`0.90` (which flags 0.36% of documents at `>= 0.80` and 0.21% at `>= 0.90`), ideally applied after English language filtering, is suitable to remove clearly harmful content while minimizing false positives on benign or multilingual pages.
  ]
