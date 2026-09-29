# CampusOS AI — Demo Script

One uninterrupted run, **Wi-Fi visibly off**, following `MVP_SCOPE.md` "Definition of Done".
Target length: 3–4 minutes. Nothing here is staged — every step is a live action.

---

## Before recording

```powershell
python tests\test_pipeline.py      # must print PIPELINE OK
python tests\test_egress.py        # must print 0 outbound connections
python tests\test_asr.py           # must print ASR OK
```

Then:
1. Put 2–3 real course PDFs on the desktop, ready to drag in.
2. Start the LLM: `powershell -File scripts\start_llm.ps1`
3. Start the app: `python -m backend`
4. **Turn Wi-Fi off in Windows settings, on camera.** This is the single most persuasive
   five seconds in the video — do it in shot, not before recording.
5. Have one question ready that your PDFs genuinely do NOT answer. Pick something from the
   same subject, not "who won the world cup" — a plausible near-miss is the convincing probe.

---

## The run

### 1 · Offline, on camera (15 s)
Show the Wi-Fi toggle going off. Show the airplane icon in the system tray.
> "Everything from here runs on this laptop. Nothing leaves it. Watch."

### 2 · Ingest (20 s)
Drag a PDF in. Show the chunk count appearing.
> "This is my own course material. The model has never seen it."

### 3 · Ask by voice (30 s)
Hold the mic button. Ask a real question aloud. Show the transcript appear.
> "It transcribes locally — and it shows me what it heard before it answers, so I can correct it."

### 4 · The cited answer (30 s) — **the trust moment**
Answer appears with citation chips. **Click one.** The source page text opens.
> "Every claim points at a page. I can check it. That is the difference between this and a
> chatbot that sounds confident."

### 5 · Refusal (25 s) — **the credibility moment**
Ask the out-of-corpus question.
> "It says it doesn't know, and shows me what it found nearby instead. It does not make
> something up. For a student who is still learning the topic, a confident wrong answer is
> the most dangerous possible output."

Do not rush this step. It is the one most competitors will not have.

### 6 · Hinglish (20 s)
Switch the language selector. Re-ask. Same answer, Hinglish, citations intact.
> "My material is in English. I think in Hinglish. The citations survive the switch."

### 7 · The quiz loop (60 s) — **the differentiator**
Press **Quiz me**. Answer the questions — **get some wrong on purpose.**
Show the score, then the named weak topic.
> "It doesn't just answer questions. It finds out what I don't know."

Click the weak topic. It jumps back into a grounded explanation of exactly that.
> "And then it teaches me that, from my own material, with the page reference. That loop is
> the product — the chat is just one step inside it."

### 8 · The honest slide (20 s)
Show `benchmarks/RESULTS.md`.
> "These are measured on this Intel laptop. The Snapdragon column is empty, because I don't
> have that hardware and I'm not going to invent numbers. The QNN path is in the code and the
> benchmark harness runs unmodified on ARM64 — so the day the hardware exists, that column
> fills in with real measurements."

---

## What NOT to do

- Do not claim NPU acceleration. You have not measured it. Saying so out loud is a
  *strength* — graders who know the hardware will notice everyone else's silence.
- Do not hide the refusal. It is a feature, not a gap.
- Do not re-record until the answer is perfect. A slightly imperfect real answer beats a
  cherry-picked one, and the citation is what carries the credibility anyway.
- Do not skip turning off Wi-Fi on camera.

## If something breaks mid-take

Keep recording and say what happened. A recovered failure with a clear error message
demonstrates §18 error handling better than a clean run does.
