const API_BASE = 'http://localhost:5000';

export async function queryRecipe(query, mode = 'auto', noveltyLevel = 'balanced') {
  const res = await fetch(`${API_BASE}/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      mode,
      novelty_level: noveltyLevel
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || 'Failed to fetch recipe');
  }
  return res.json();
}

export async function getMemory() {
  const res = await fetch(`${API_BASE}/api/memory`);
  return res.json();
}

export async function clearMemory() {
  const res = await fetch(`${API_BASE}/api/memory/clear`, { method: 'POST' });
  return res.json();
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}
