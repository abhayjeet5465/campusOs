const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

async function api(path, opts) {
  const r = await fetch('/api' + path, opts);
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.detail || r.statusText);
  return body;
}

/* ---------- health ---------- */
async function health() {
  try {
    const h = await api('/health');
    $('#health').innerHTML =
      'LLM ' + (h.llm ? '<b style="color:var(--good)">ready</b>' : '<b style="color:var(--bad)">not running</b>') +
      ' · speech ' + (h.asr ? 'ready' : 'unavailable') +
      ' · EP ' + esc(h.embed_provider) +
      ' · ' + h.documents + ' docs / ' + h.chunks + ' chunks';
  } catch { $('#health').textContent = 'backend unreachable'; }
}

/* ---------- library ---------- */
async function loadDocs() {
  const docs = await api('/documents');
  $('#docs').innerHTML = docs.map(d =>
    `<li><span><b>${esc(d.name)}</b><small>${d.pages} pages · ${d.chunks} chunks</small></span>
     <button data-del="${d.id}" aria-label="Delete ${esc(d.name)}">Delete</button></li>`).join('')
    || '<li><small>No documents yet.</small></li>';
  $('#scope').innerHTML = '<option value="">All documents</option>' +
    docs.map(d => `<option value="${d.id}">${esc(d.name)}</option>`).join('');
}

$('#docs').onclick = async e => {
  const id = e.target.dataset.del;
  if (!id || !confirm('Delete this document and everything derived from it?')) return;
  await api('/documents/' + id, { method: 'DELETE' });
  loadDocs(); health();
};

$('#file').onchange = async e => {
  for (const f of e.target.files) {
    $('#ingest').textContent = `Ingesting ${f.name}…`;
    const fd = new FormData(); fd.append('file', f);
    try {
      const d = await api('/documents', { method: 'POST', body: fd });
      $('#ingest').innerHTML = `✓ ${esc(d.name)} — ${d.pages} pages, ${d.chunks} chunks`;
    } catch (err) {
      $('#ingest').innerHTML = `<span class="err">✗ ${esc(f.name)}: ${esc(err.message)}</span>`;
    }
  }
  e.target.value = ''; loadDocs(); health();
};

/* ---------- ask ---------- */
function renderCitations(text, cites) {
  // Turn validated [doc, p.N] markers into clickable buttons.
  // The server already dropped any citation the model invented.
  return esc(text).replace(/\[([^\[\]]+?),\s*p\.?\s*(\d+)\]/gi, (m, name, page) => {
    const c = cites.find(c => c.name.toLowerCase() === name.trim().toLowerCase() && c.page == page);
    return c
      ? `<button class="cite" data-doc="${c.doc_id}" data-page="${c.page}">${esc(name)} p.${page}</button>`
      : m;
  });
}

function renderFinal(r) {
  const nearby = (r.nearby || []).map(n =>
    `<li>${esc(n.name)} p.${n.page} (score ${n.score}) — ${esc(n.preview)}…</li>`).join('');
  $('#answer').className = 'answer' + (r.grounded ? '' : ' refused');
  $('#answer').innerHTML =
    `<div class="body">${renderCitations(r.answer, r.citations || [])}</div>` +
    (r.grounded
      ? `<div class="srcs">Retrieved from: ${(r.sources || []).map(s => `${esc(s.name)} p.${s.page} (${s.score})`).join(' · ')}</div>`
      : (nearby ? `<div class="srcs">Closest material found:<ul>${nearby}</ul></div>` : ''));
}

async function ask(question) {
  if (!question.trim()) return;
  const translating = $('#lang').value !== 'en';
  $('#answer').className = 'answer';
  $('#answer').innerHTML = `<div class="note">${translating ? 'Answering, then re-explaining…' : 'Thinking…'}</div>`;

  // Streamed rather than awaited: a full answer takes ~13 s on this hardware, and a blank
  // panel that long reads as a hang. Tokens are shown raw; the citation chips are rendered
  // only from the final validated payload, never from partial text.
  let body = null;
  try {
    const res = await fetch('/api/ask/stream', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question, lang: $('#lang').value, depth: $('#depth').value,
        doc_id: $('#scope').value || null
      })
    });
    if (!res.ok || !res.body) throw new Error('Could not reach the backend');

    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = '', acc = '';

    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });

      // SSE frames are separated by a blank line; keep any partial frame in the buffer.
      const frames = buf.split('\n\n');
      buf = frames.pop();
      for (const frame of frames) {
        const ev = (frame.match(/^event: (.*)$/m) || [])[1];
        const raw = (frame.match(/^data: (.*)$/m) || [])[1];
        if (!ev || raw === undefined) continue;
        const data = JSON.parse(raw);
        if (ev === 'token') {
          acc += data;
          if (!body) {
            $('#answer').innerHTML = '<div class="body"></div>';
            body = $('#answer .body');
          }
          body.textContent = acc;
        } else if (ev === 'refusal' || ev === 'done') {
          renderFinal(data);
          return;
        } else if (ev === 'error') {
          throw new Error(data.detail);
        }
      }
    }
    if (translating) $('#answer').innerHTML = '<div class="note">Re-explaining…</div>';
  } catch (err) {
    $('#answer').innerHTML = `<div class="err">${esc(err.message)}</div>`;
  }
}

$('#send').onclick = () => ask($('#q').value);
$('#q').onkeydown = e => { if (e.key === 'Enter') ask($('#q').value); };

document.body.addEventListener('click', async e => {
  const b = e.target.closest('.cite'); if (!b) return;
  const r = await api(`/documents/${b.dataset.doc}/page/${b.dataset.page}`);
  $('#page-h').textContent = `Page ${r.page}`;
  $('#ptext').textContent = r.text;
  $('#page').hidden = false; $('#pclose').focus();
});
$('#pclose').onclick = () => { $('#page').hidden = true; };
document.addEventListener('keydown', e => { if (e.key === 'Escape') $('#page').hidden = true; });

/* ---------- voice (push-to-talk) ---------- */
let rec, chunks = [];
async function startRec() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    rec = new MediaRecorder(stream); chunks = [];
    rec.ondataavailable = e => chunks.push(e.data);
    rec.onstop = async () => {
      stream.getTracks().forEach(t => t.stop());
      const fd = new FormData(); fd.append('file', new Blob(chunks), 'audio.webm');
      $('#transcript').textContent = 'Transcribing…';
      try {
        const t = await api('/transcribe', { method: 'POST', body: fd });
        // Transcript is shown for confirmation, never auto-submitted (TRD 8).
        $('#q').value = t.text;
        $('#transcript').innerHTML =
          `Heard: “${esc(t.text)}” — check it, then press Ask. <small>${esc(t.backend || '')}</small>`;
        $('#q').focus();
      } catch (err) {
        $('#transcript').innerHTML = `<span class="err">${esc(err.message)}</span>`;
      }
    };
    rec.start();
    $('#mic').classList.add('rec'); $('#mic').textContent = '⏺ Recording… release';
  } catch {
    $('#transcript').innerHTML =
      '<span class="err">Microphone unavailable — type your question instead.</span>';
  }
}
function stopRec() {
  if (rec && rec.state === 'recording') rec.stop();
  $('#mic').classList.remove('rec'); $('#mic').textContent = '🎙 Hold to talk';
}
$('#mic').addEventListener('pointerdown', startRec);
addEventListener('pointerup', stopRec);
// Keyboard path: voice must never be the only way in (PRD 15).
$('#mic').addEventListener('keydown', e => {
  if ((e.key === ' ' || e.key === 'Enter') && !e.repeat) { e.preventDefault(); startRec(); }
});
$('#mic').addEventListener('keyup', e => { if (e.key === ' ' || e.key === 'Enter') stopRec(); });

/* ---------- quiz ---------- */
let quizId = null;
$('#genquiz').onclick = async () => {
  $('#quiz').innerHTML = '<div class="note">Writing questions from your material…</div>';
  try {
    const r = await api('/quiz', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_id: $('#scope').value || null, n: +$('#nq').value })
    });
    quizId = r.quiz_id;
    $('#quiz').innerHTML = r.questions.map(q =>
      `<div class="q"><p>${q.id + 1}. ${esc(q.question)}</p>` +
      q.options.map((o, i) =>
        `<label><input type="radio" name="q${q.id}" value="${i}"> ${esc(o)}</label>`).join('') +
      `<small style="color:var(--dim)">Topic: ${esc(q.topic)} · from ${esc(q.source.name)} p.${q.source.page}</small></div>`
    ).join('') + '<button id="submitq" class="primary">Submit answers</button>';
  } catch (err) {
    $('#quiz').innerHTML = `<div class="err">${esc(err.message)}</div>`;
  }
};

$('#quiz').addEventListener('click', async e => {
  if (e.target.id !== 'submitq') return;
  const answers = {};
  document.querySelectorAll('#quiz input[type=radio]:checked')
    .forEach(i => answers[i.name.slice(1)] = +i.value);
  const r = await api(`/quiz/${quizId}/submit`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers })
  });
  const weak = r.weak_topics.length
    ? '<div class="weak"><h3>Weakest topics:</h3>' +
      r.weak_topics.map(w =>
        `<button data-weak="${esc(w.topic)}">${esc(w.topic)} — explain this to me</button>`).join('') +
      '</div>'
    : '<div class="weak"><h3>No weak topics — everything correct.</h3></div>';
  $('#quiz').innerHTML = `<div class="score">Score: ${r.correct}/${r.total}</div>` + weak +
    r.results.map(q =>
      `<div class="q"><p>${q.id + 1}. ${esc(q.question)}</p>
       <div class="res ${q.correct ? 'ok' : 'no'}">
         ${q.correct
           ? '✓ Correct'
           : `✗ You chose: ${esc(q.options[q.chosen] ?? 'nothing')}<br>Correct: ${esc(q.options[q.answer])}`}
         <br>${esc(q.explanation)}
         <br><button class="cite" data-doc="${q.source.doc_id}" data-page="${q.source.page}">${esc(q.source.name)} p.${q.source.page}</button>
       </div></div>`).join('');
});

// Weak topic -> back into a grounded explanation (FR-14). The loop closes here.
$('#quiz').addEventListener('click', e => {
  const t = e.target.dataset.weak; if (!t) return;
  $('#q').value = `Explain ${t} in detail`;
  $('#q').scrollIntoView({ behavior: 'smooth', block: 'center' });
  ask($('#q').value);
});

loadDocs(); health(); setInterval(health, 15000);
