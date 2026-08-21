// Shared helpers for the pl/ pages: theme toggle + a small CSV parser.
// None of our CSV fields contain embedded commas/quotes, so a plain split is fine.

function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  const icon = document.getElementById('theme-icon');
  if (icon) icon.textContent = t === 'dark' ? '☀️' : '🌙';
}
function toggleTheme() {
  const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  localStorage.setItem('pl-theme', next);
}
applyTheme(localStorage.getItem('pl-theme') || 'light');

function parseCsv(text) {
  const lines = text.split('\n').filter(l => l.trim().length > 0);
  if (!lines.length) return { header: [], rows: [] };
  const header = lines[0].split(',').map(s => s.trim());
  const rows = lines.slice(1).map(line => {
    const cells = line.split(',').map(s => s.trim());
    const row = {};
    header.forEach((h, i) => { row[h] = cells[i] ?? ''; });
    return row;
  });
  return { header, rows };
}

async function fetchCsv(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path}`);
  return parseCsv(await res.text());
}

async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path}`);
  return res.json();
}
