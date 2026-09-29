# Evaluation set

Put **3–5 real course PDFs** in `eval/pdfs/`. Not lorem ipsum, not generated text — the
retrieval numbers are meaningless on synthetic material because synthetic material has
none of the layout noise, repeated headers, or inconsistent phrasing that real slide
decks and textbook chapters have.

Then write `eval/eval_set.json`:

```json
{
  "in_corpus": [
    {"question": "What is the time complexity of quicksort in the worst case?",
     "pages": [12, 13]}
  ],
  "out_of_corpus": [
    "Who won the 2019 cricket world cup?",
    "What is the boiling point of mercury?"
  ]
}
```

`pages` lists the page(s) that genuinely contain the answer — used to check retrieval hit
the right place, not just that it returned something confidently.

Target: 20–30 in-corpus questions, 10 out-of-corpus probes.

**Out-of-corpus probes should be plausible-sounding but genuinely absent** — questions from
the same subject area that the document does not cover. "Who won the world cup" is an easy
probe; "what is the space complexity of the algorithm on page 14" when the document never
states it is the hard one, and the hard one is what the gate has to survive.

Run: `python eval/run_eval.py`
