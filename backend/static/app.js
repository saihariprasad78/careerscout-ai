const form = document.querySelector('#search-form');
const results = document.querySelector('#results');
const button = document.querySelector('#submit');

function esc(value = '') {
  return String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}

function render(data) {
  const cards = data.jobs.map(job => {
    const caution = job.risk.level === 'caution';
    const details = [job.location, job.posted_at, job.via].filter(Boolean).map(esc).join('<span></span>');
    const risk = job.risk.signals.map(esc).join(' ');
    const evidence = job.evidence_url
      ? `<a class="evidence" href="${esc(job.evidence_url)}" target="_blank" rel="noopener noreferrer">Open listing evidence ↗</a>`
      : '<small>No evidence link</small>';
    return `<article class="card"><div class="card-top"><div><h3>${esc(job.title)}</h3><div class="company">${esc(job.company)}</div></div><span class="tag ${caution ? 'caution' : 'clear'}">${caution ? 'Check details' : 'No obvious signal'}</span></div><div class="details">${details}</div><p class="risk">${risk}</p><div class="card-foot"><small>Google Jobs · heuristic only</small>${evidence}</div><button type="button" class="investigate-btn" data-company="${esc(job.company)}" data-title="${esc(job.title)}" data-location="${esc(job.location)}" aria-expanded="false">Investigate this job <b>↗</b></button><section class="dossier" hidden aria-live="polite"></section></article>`;
  }).join('');
  results.innerHTML = `<div class="results-head"><h2>${data.count} ${data.count === 1 ? 'listing' : 'listings'} found</h2><p>Evidence first · No fraud verdicts</p></div>${cards ? `<div class="cards">${cards}</div>` : '<div class="message">No listings came back for this search. Try a broader role or nearby city.</div>'}<div class="source-note"><span>!</span><span>${esc(data.disclaimer)}</span></div>`;
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  button.disabled = true;
  button.querySelector('span').textContent = 'Searching…';
  results.innerHTML = '<div class="message">Searching Google Jobs through SerpApi…</div>';
  const params = new URLSearchParams({role: document.querySelector('#role').value.trim(), location: document.querySelector('#location').value.trim()});
  try {
    const response = await fetch(`/api/jobs?${params}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Search could not be completed.');
    render(data);
  } catch (error) {
    results.innerHTML = `<div class="message">${esc(error.message)} Check your backend configuration and try again.</div>`;
  } finally {
    button.disabled = false;
    button.querySelector('span').textContent = 'Search jobs';
  }
});

results.addEventListener('click', async event => {
  const trigger = event.target.closest('.investigate-btn');
  if (!trigger) return;
  const card = trigger.closest('.card');
  const panel = card.querySelector('.dossier');
  if (trigger.dataset.loaded === 'true') {
    panel.hidden = !panel.hidden;
    trigger.setAttribute('aria-expanded', String(!panel.hidden));
    return;
  }
  trigger.disabled = true;
  trigger.textContent = 'Searching public evidence…';
  panel.hidden = false;
  panel.innerHTML = '<p class="dossier-loading">Searching Google once for public context…</p>';
  const params = new URLSearchParams({company: trigger.dataset.company, title: trigger.dataset.title, location: trigger.dataset.location});
  try {
    const response = await fetch(`/api/dossier?${params}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Evidence search could not be completed.');
    const sources = data.sources.map(source => `<article class="dossier-source"><h4><a href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">${esc(source.title)} ↗</a></h4>${source.source ? `<small>${esc(source.source)}</small>` : ''}<p>${esc(source.snippet)}</p><p class="supports">${esc(source.supports)}</p></article>`).join('');
    const list = items => items.map(item => `<li>${esc(item)}</li>`).join('');
    panel.innerHTML = `<h3>Evidence Dossier</h3><p class="dossier-intro">${data.result_count} linkable Google Search ${data.result_count === 1 ? 'result' : 'results'} · one search used for this dossier</p><h4>Public sources</h4>${sources || '<p>No matching linkable sources were returned. This does not mean the employer or role is illegitimate.</p>'}<div class="dossier-columns"><div><h4>Cautions</h4><ul>${list(data.cautions)}</ul></div><div><h4>Unknowns</h4><ul>${list(data.unknowns)}</ul></div></div><h4>Before you apply</h4><ul>${list(data.before_apply)}</ul><p class="dossier-disclaimer">${esc(data.disclaimer)}</p>`;
    trigger.dataset.loaded = 'true';
    trigger.setAttribute('aria-expanded', 'true');
  } catch (error) {
    panel.innerHTML = `<p class="message">${esc(error.message)}</p>`;
    trigger.setAttribute('aria-expanded', 'true');
  } finally {
    trigger.disabled = false;
    trigger.innerHTML = 'Investigate this job <b>↗</b>';
  }
});
