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
    return `<article class="card"><div class="card-top"><div><h3>${esc(job.title)}</h3><div class="company">${esc(job.company)}</div></div><span class="tag ${caution ? 'caution' : 'clear'}">${caution ? 'Check details' : 'No obvious signal'}</span></div><div class="details">${details}</div><p class="risk">${risk}</p><div class="card-foot"><small>Google Jobs · heuristic only</small>${evidence}</div></article>`;
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
