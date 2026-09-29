# CampusOS AI — Product Requirements Document

**Date:** 2026-09-21 · **Phase:** 0 · **Scope:** MVP for the Snapdragon AI Lab Build & Present Challenge (deadline 2026-09-30)

---

## 1. Product name

**CampusOS AI**

## 2. One-line definition

> A private, offline study assistant that turns a student's own course material into a voice-driven learning loop — cited explanations in their own language, followed by quizzes that reveal what they actually don't know.

## 3. Problem statement

Indian college students preparing for exams face four problems at once, and existing tools solve at most two:

1. **Their material is specific and theirs.** The syllabus, the professor's slides, the previous year's question paper. A general chatbot has never seen any of it and will confidently answer from something else.
2. **They cannot verify answers.** A fluent wrong answer is indistinguishable from a right one when you are the one still learning the topic. This is exactly the population least equipped to catch hallucination.
3. **Explanation language ≠ material language.** Material is in English. Understanding often happens in Hindi or a Hindi-English mix. Students perform this translation in their heads, badly, under time pressure.
4. **They don't know what they don't know.** Re-reading feels like studying. It is the least effective way to find gaps, and it is what students default to because nothing tells them where the gaps are.

Connectivity adds a fifth: hostel and campus Wi-Fi is unreliable, and cloud AI stops working exactly during the late-night sessions when it is most needed.

## 4. Target users

**Primary:** Indian undergraduate students (17–24), engineering/science/commerce, preparing for semester exams from their own PDFs, on a mid-range Windows laptop, often on unreliable Wi-Fi.

**Secondary:** Postgraduate and competitive-exam aspirants with large private study corpora.

## 5. Personas

**Aarti — 2nd-year engineering, exam in 3 days.**
Has 6 PDFs: two lecture slide decks, a textbook chapter, three past papers. Studies 11 pm–2 am in a hostel with throttled Wi-Fi. Reads English fine but *understands* faster when explanation mixes in Hindi. Needs to know which of the 40 topics she is weak on, tonight — not a general essay on the subject.

**Rohit — final-year, project + placement prep.**
Owns dense reference PDFs. Will not paste proprietary course material or unpublished notes into a cloud service. Wants answers he can trace back to a page number, because he has been burned by a confidently wrong chatbot answer in a viva.

## 6. Core pain points

| Pain | Current workaround | Why it fails |
|---|---|---|
| Answers not from my syllabus | Paste chunks into ChatGPT | Context limits; loses structure; generic answers |
| Can't verify | Trust it, or re-read everything | Defeats the purpose |
| Wrong language register | Mentally translate | Slow, lossy, tiring at 1 am |
| Don't know my gaps | Re-read from page 1 | Feels productive, isn't |
| No internet | Stop studying | Total failure |
| Private material | Upload anyway, uneasily | Genuine exposure |

## 7. Product vision

Every student's laptop becomes a private tutor that has read *their* syllabus, speaks *their* language, shows *its* sources, and works with the Wi-Fi off — because the model runs on the machine in front of them, not in someone else's datacentre.

## 8. Product principles

1. **Grounded or silent.** If it is not in the student's material, say so. Never fill the gap with plausible text.
2. **Cite, always.** Every claim carries a page reference the student can open.
3. **Local by default.** No network call happens without the student seeing it. Offline is the normal case, not a degraded mode.
4. **Teach the gap, not the topic.** The output that matters is "you don't know X", not another wall of prose.
5. **Meet the student's language.** Including Hinglish, which is how they actually think.
6. **Honest about the machine.** Never claim acceleration or performance we have not measured.

## 9. MVP goals

| G | Goal | Measured by |
|---|---|---|
| G1 | Answer questions from the student's own PDFs with verifiable citations | Groundedness ≥ 90 % on the eval set |
| G2 | Refuse cleanly when material lacks the answer | 100 % refusal on out-of-corpus probes |
| G3 | Accept spoken questions locally | English WER acceptable for intent; push-to-talk works |
| G4 | Explain in English, Hindi, or Hinglish | Manual review of the eval set |
| G5 | Generate a quiz and identify a weak topic | End-to-end run produces a named weak topic |
| G6 | Run fully offline | Airplane-mode pass + zero-egress assertion |
| G7 | Present a credible Snapdragon optimisation path | Harness + documented QNN/GenieX path |

## 10. Explicit non-goals

Not a general chatbot · not a search engine · no accounts or login · no cloud sync · no collaboration · not an LMS · not a note-taking app · not a document editor · **not a "chat with PDF" tool** — chat is one step inside a loop that ends in a quiz, and the loop is the product.

## 11. Core user journeys

**J1 — First session (the demo path)**
Open CampusOS → drop in a PDF → ingest with visible progress → hold the mic button, ask aloud → transcript appears → cited answer appears → click a citation, land on the source page.

**J2 — Language switch**
Same answer, "Explain in Hinglish" → re-explained in mixed register, citations intact.

**J3 — The learning loop (the differentiator)**
"Quiz me on this chapter" → questions generated from retrieved chunks → student answers → score + per-question explanation with citations → **named weak topic** → one click back into a grounded explanation of exactly that topic.

**J4 — Honest failure**
Ask something outside the material → "I couldn't find this in your uploaded material" + what *was* found nearby → no invented answer.

**J5 — Offline**
Wi-Fi off. Everything in J1–J4 behaves identically.

## 12. User stories

- As a student, I upload my syllabus PDFs so answers come from *my* course, not the internet.
- As a student, I ask questions by voice so I can study hands-free at 1 am.
- As a student, I see page citations so I can verify before trusting.
- As a student, I get explanations in Hinglish so I understand faster.
- As a student, I am told when my material doesn't cover something, so I know to look elsewhere.
- As a student, I get quizzed so I discover gaps instead of re-reading.
- As a student, I learn my weak topic so my remaining study time goes to the right place.
- As a student, I study offline so bad Wi-Fi doesn't stop me.
- As a privacy-conscious student, my documents never leave my laptop.

## 13. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Upload one or more digital PDFs | MUST |
| FR-02 | Extract text with page numbers retained | MUST |
| FR-03 | Chunk page-aware; persist chunk + page + doc metadata | MUST |
| FR-04 | Embed chunks locally; store vectors locally | MUST |
| FR-05 | Top-k semantic retrieval over the student's corpus | MUST |
| FR-06 | Generate answers **only** from retrieved context | MUST |
| FR-07 | Render citations as `[doc, p.N]`, clickable to the page | MUST |
| FR-08 | Explicit refusal when retrieval is below a relevance threshold | MUST |
| FR-09 | Push-to-talk audio capture → local transcription | MUST |
| FR-10 | Output language selector: English / Hindi / Hinglish | MUST |
| FR-11 | Generate an MCQ/short-answer quiz from a selected document or topic | MUST |
| FR-12 | Evaluate answers; explain each with citations | MUST |
| FR-13 | Identify and name at least one weak topic from quiz results | MUST |
| FR-14 | Navigate from a weak topic back into grounded explanation | MUST |
| FR-15 | Delete a document and all derived data | MUST (privacy) |
| FR-16 | Answer-depth control (simpler / exam-ready) | SHOULD |
| FR-17 | Hindi speech input | SHOULD |
| FR-18 | Persist session/quiz history | SHOULD |
| FR-19 | TTS readback | COULD |
| FR-20 | Scanned-PDF OCR | COULD |

## 14. Non-functional requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | Runs on 8 GB RAM, x64 or ARM64 Windows 11 | Hard |
| NFR-02 | Total resident memory | < 4 GB |
| NFR-03 | First token after question | Measured & reported, not promised |
| NFR-04 | Ingest throughput | Measured & reported |
| NFR-05 | Zero network calls during normal operation | **Asserted in tests** |
| NFR-06 | Cold start to usable | Measured |
| NFR-07 | Portable to Snapdragon via runtime swap only | No application code change |
| NFR-08 | All models permissively licensed | Verified per model |

> NFR-03/04/06 deliberately state *"measured and reported"* rather than a number. Inventing a latency target before measuring on hardware we do not have would be exactly the fabrication the brief forbids.

## 15. Accessibility

Keyboard-operable end to end (voice input must not be the only path); visible focus states; WCAG AA contrast; transcripts always shown as text so audio is never the sole channel; font scaling respected; no colour-only status encoding; `prefers-reduced-motion` honoured.

## 16. Privacy requirements

Documents, vectors, transcripts, and quiz history stay in a local app-data directory. No telemetry. No analytics. No crash reporting. Audio is transcribed and the buffer discarded — never written to disk unless the student explicitly saves it. `FR-15` deletion is hard deletion, including vectors and derived chunks. Any future network feature must be opt-in and visibly indicated in the UI.

## 17. Offline requirements

After first-run model download, **every** MVP feature works with networking disabled. Verified by an automated airplane-mode test plus a no-egress assertion (`NFR-05`). The UI must not degrade, warn, or block when offline.

## 18. Error handling

| Condition | Behaviour |
|---|---|
| Encrypted / unreadable PDF | Named error, no crash, other docs unaffected |
| Scanned PDF (no text layer) | Detect, state "no extractable text — OCR not supported yet" |
| Oversized file | Reject above a size cap with a clear message |
| LLM backend unreachable | Explicit "local model not running" + how to start it |
| Mic unavailable / permission denied | Fall back to text input, state why |
| Retrieval below threshold | `FR-08` refusal path, not a guess |
| Model OOM | Fail gracefully, suggest the smaller model |

## 19. UX requirements

One screen, three zones: **Library** (documents) · **Ask** (voice/text + cited answer) · **Quiz** (loop + weak topics). No onboarding wizard, no account, no modal chrome. Ingest shows real progress. Citations are visually distinct and clickable. The language selector is always visible, not buried. Weak topics are the most prominent element after a quiz — the UI should make the gap impossible to ignore.

## 20. Roadmap

- **Post-MVP:** Hindi speech input · session history · answer-depth control · multi-doc study sets
- **Next:** TTS · OCR for scanned notes · flashcards · spaced repetition on weak topics
- **Later:** adaptive difficulty · teacher mode · handwritten notes · cross-device sync (local network only)

## 21. Success metrics

**Competition (primary):**

| Criterion | Evidence we will present |
|---|---|
| Technical Implementation | Working local RAG + ASR + LLM; QNN/GenieX path; benchmark harness |
| Use Case & Innovation | The closed study loop; the Hinglish-output insight |
| Deployment & Accessibility | 8 GB floor; offline proof; keyboard-accessible; single-command run |
| Presentation & Documentation | This doc set, generated from the real build |

**Product (measured on the eval set):** groundedness ≥ 90 % · out-of-corpus refusal 100 % · quiz factual correctness ≥ 85 % · offline test pass · full loop completes in one session without a crash.
