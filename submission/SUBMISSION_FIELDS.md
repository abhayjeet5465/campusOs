# Unstop Solution Submission Round — field-by-field

Competition: Snapdragon® AI Lab Build & Present Challenge
Rule this submission is written against: *"The proposed solution must be designed, developed,
or intended to be optimised for Snapdragon-powered HP PCs."*

---

## 1 · Project Title  *(max 500 characters)*

Paste this:

```
CampusOS AI — a private, offline study assistant for Snapdragon-powered HP PCs that turns a student's own course PDFs into a voice-driven learning loop: cited explanations in English, Hindi or Hinglish, followed by quizzes that name the topic they actually don't know.
```

*(258 characters.)* If you prefer something shorter for display:

```
CampusOS AI — Offline, cited, voice-driven study assistant for Snapdragon-powered HP PCs
```

## 2 · Brief Project Description  *(upload — pdf / doc / docx)*

Upload **`CampusOS_AI_Brief_Project_Description.pdf`** (4 pages).
The `.docx` is in the same folder if you want to edit anything first.

## 3 · GitHub Repository Link

```
https://github.com/abhayjeet5465/campusOs
```

**Check before submitting:** the repository must be **public**, or a judge cannot open it.

## 4 · Short Pitch Presentation in PDF

Upload **`CampusOS_AI_Pitch.pdf`** (9 slides).

## 5 · Short Pitch Presentation in PPT

Upload **`CampusOS_AI_Pitch.pptx`** (same 9 slides, with speaker notes).

## 6 · "You have a Snapdragon laptop."

**Answer: No.**

Do not be tempted to answer otherwise. The rule permits a solution *"intended to be optimised
for"* Snapdragon, which is exactly what this is, and every document here says so openly. A false
answer here would contradict the submission's own documents, which state plainly that no NPU has
been measured.

---

## Before you hit submit

| Check | Why |
|---|---|
| Repository is public | A private repo makes every claim unverifiable |
| All four files uploaded | Two PDFs, one PPTX, one repo link |
| Answered "No" to the Snapdragon laptop question | Consistency with the documents |
| Submitted **well before** the deadline | The rules state a submission cannot be changed once made |

**Still outstanding in the project itself** (not blockers for submission, but worth knowing):

- `eval/pdfs/` is empty. Until real course PDFs go in and `python eval/run_eval.py` is run, the
  groundedness and refusal percentages are unmeasured — the benchmark and offline numbers are
  real, these two are not yet.
- The demo video has not been recorded. `docs/DEMO.md` has the shot-by-shot script.
