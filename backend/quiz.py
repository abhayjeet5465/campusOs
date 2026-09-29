"""Quiz generation, scoring, and weak-topic detection.

Each question carries its source chunk id at GENERATION time. That is what makes the
explanation grounded and the weak topic meaningful -- it cannot be retrofitted reliably.
"""
import uuid, collections
from . import store, llm

GEN_SYSTEM = """You write exam questions from a student's course material.

Return ONLY JSON: {"questions":[{"topic":"<2-4 word topic>","question":"...",
"options":["A text","B text","C text","D text"],"answer":0,"why":"one sentence, from the passage only"}]}

Rules: every question answerable from the passage alone; "answer" is the 0-based index of the
correct option; distractors plausible but clearly wrong to someone who read the passage;
"topic" names the concept tested, not the document."""


def generate(doc_id=None, n=5):
    samples = store.sample_chunks(doc_id, n)
    if not samples:
        raise ValueError("No material ingested yet — upload a PDF first.")
    questions = []
    for c in samples:
        try:
            data = llm.chat_json([
                {"role": "system", "content": GEN_SYSTEM},
                {"role": "user", "content": f"PASSAGE (from {c['name']}, page {c['page']}):\n{c['text']}\n\nWrite 1 question."}
            ], temperature=0.4, max_tokens=500)
        except ValueError:
            continue                                  # unparseable -> skip, don't fake a question
        for q in data.get("questions", [])[:1]:
            if not isinstance(q.get("options"), list) or len(q["options"]) < 2:
                continue
            if not isinstance(q.get("answer"), int) or not 0 <= q["answer"] < len(q["options"]):
                continue
            questions.append({
                "id": len(questions), "topic": q.get("topic", "General"),
                "question": q["question"], "options": q["options"], "answer": q["answer"],
                "why": q.get("why", ""), "chunk_id": c["id"],
                "source": {"doc_id": c["doc_id"], "name": c["name"], "page": c["page"]},
            })
    if not questions:
        raise ValueError("The model could not produce a valid quiz from this material. Try another document.")
    qid = uuid.uuid4().hex
    store.save_quiz(qid, doc_id, questions)
    return {"quiz_id": qid,
            "questions": [{k: v for k, v in q.items() if k not in ("answer", "why", "chunk_id")}
                          for q in questions]}


def submit(qid, answers):
    """answers: {question_id: chosen_index}. Returns score, grounded explanations, weak topics."""
    questions = store.get_quiz(qid)
    if questions is None:
        raise ValueError("Unknown quiz id")
    results, wrong = [], collections.Counter()
    for q in questions:
        chosen = answers.get(str(q["id"]), answers.get(q["id"]))
        correct = chosen is not None and int(chosen) == q["answer"]
        if not correct:
            wrong[q["topic"]] += 1
        results.append({
            "id": q["id"], "topic": q["topic"], "question": q["question"],
            "options": q["options"], "chosen": chosen, "answer": q["answer"],
            "correct": correct,
            # Explanation comes from the chunk the question was generated from, so it is
            # grounded by construction rather than by a second retrieval round.
            "explanation": q["why"], "source": q["source"],
        })
    score = sum(r["correct"] for r in results) / len(results) if results else 0.0
    # Rank by wrong count; a topic tested once and missed still counts -- with 5 questions
    # there is no statistical basis for demanding repeats, and silence would be worse.
    weak = [{"topic": t, "missed": n,
             "source": next(r["source"] for r in results if r["topic"] == t and not r["correct"])}
            for t, n in wrong.most_common(3)]
    store.save_attempt(qid, results, score, weak)
    return {"score": round(score, 3), "correct": sum(r["correct"] for r in results),
            "total": len(results), "results": results, "weak_topics": weak}


def demo():
    qs = [{"id": 0, "topic": "Ohm's Law", "question": "q", "options": ["a", "b"], "answer": 0,
           "why": "w", "chunk_id": 1, "source": {"doc_id": "d", "name": "n", "page": 3}},
          {"id": 1, "topic": "Ohm's Law", "question": "q2", "options": ["a", "b"], "answer": 1,
           "why": "w", "chunk_id": 2, "source": {"doc_id": "d", "name": "n", "page": 4}},
          {"id": 2, "topic": "Capacitors", "question": "q3", "options": ["a", "b"], "answer": 0,
           "why": "w", "chunk_id": 3, "source": {"doc_id": "d", "name": "n", "page": 5}}]
    store.get_quiz = lambda _: qs
    store.save_attempt = lambda *a: None
    out = submit("x", {"0": 1, "1": 0, "2": 0})     # both Ohm wrong, Capacitors right
    assert out["correct"] == 1 and out["total"] == 3, out
    assert out["weak_topics"][0]["topic"] == "Ohm's Law", out["weak_topics"]
    assert out["weak_topics"][0]["source"]["page"] == 3
    assert submit("x", {"0": 0, "1": 1, "2": 0})["weak_topics"] == [], "all correct -> no weak topic"
    print("quiz self-check ok")


if __name__ == "__main__":
    demo()
