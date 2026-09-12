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

// Shared fixture/score helpers (same shape as tools/calculate_pl_scores.py).
function normFixture(s) {
  return (s || '').trim().toLowerCase().replace(/\s+/g, ' ');
}
function parseScore(s) {
  const m = /^\s*(\d+)\s*-\s*(\d+)\s*$/.exec(s || '');
  return m ? [parseInt(m[1], 10), parseInt(m[2], 10)] : null;
}
function resultType([h, a]) {
  return h > a ? 'home' : a > h ? 'away' : 'draw';
}

// 5/3/1 scoring for a subset of selections.csv rows (e.g. one round), mirroring
// tools/calculate_pl_scores.py's score(). scoresMap: normFixture(fixture) -> [h, a].
function scoreRows(players, rows, scoresMap) {
  const table = {};
  for (const p of players) table[p] = { Player: p, '5': 0, '3': 0, '1': 0 };

  for (const row of rows) {
    const actual = scoresMap[normFixture(row.FIXTURE)];
    if (!actual) continue;
    const outcome = resultType(actual);

    const preds = {};
    for (const p of players) {
      const parsed = parseScore(row[p]);
      if (parsed) preds[p] = parsed;
    }
    const exactCounts = {};
    for (const p in preds) {
      const key = preds[p].join('-');
      exactCounts[key] = (exactCounts[key] || 0) + 1;
    }
    for (const p in preds) {
      const pred = preds[p];
      if (pred[0] === actual[0] && pred[1] === actual[1]) {
        if (exactCounts[pred.join('-')] === 1) table[p]['5']++;
        else table[p]['3']++;
      } else if (resultType(pred) === outcome) {
        table[p]['1']++;
      }
    }
  }

  return Object.values(table).map(r => ({
    Player: r.Player,
    Score: r['5'] * 5 + r['3'] * 3 + r['1'],
    'Correct Scores': r['5'] + r['3'],
    '5 Pointers': r['5'],
    '3 Pointers': r['3'],
    '1 Pointers': r['1'],
  }));
}
