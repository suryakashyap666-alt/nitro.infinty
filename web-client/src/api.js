export async function sendChat({ user_id, message, apiUrl, guest_mode = false, bot_id, detected_language } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/chat' : '/chat';
  const payload = { user_id, message, guest_mode, bot_id };
  if (detected_language) payload.detected_language = detected_language;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Request failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function generateImage({ user_id, message, apiUrl, bot_id } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/image/generate' : '/image/generate';
  const fd = new FormData();
  fd.append('user_id', user_id || '');
  fd.append('message', message || '');
  if (bot_id) fd.append('bot_id', bot_id);

  const res = await fetch(url, { method: 'POST', body: fd });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Image generate failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function analyzeImage({ user_id, message, imageFile, apiUrl, bot_id } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/image/analyze' : '/image/analyze';
  const fd = new FormData();
  fd.append('user_id', user_id || '');
  fd.append('message', message || '');
  fd.append('image', imageFile);
  if (bot_id) fd.append('bot_id', bot_id);

  const res = await fetch(url, { method: 'POST', body: fd });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Image analyze failed: ${res.status} ${text}`);
  }
  return res.json();
}


export async function fetchHistory({ user_id, apiUrl }) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/history/' + encodeURIComponent(user_id) : '/history/' + encodeURIComponent(user_id);
  const res = await fetch(url, { method: 'GET' });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`History load failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function loginSaraswati({ accountId, password, apiUrl }) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/auth/saraswati' : '/auth/saraswati';
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account_id: accountId, password }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Saraswati login failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function verifySession({ token, apiUrl } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/auth/verify' : '/auth/verify';
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(url, { method: 'GET', headers });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Session verification failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function fetchBotsList({ query = '', apiUrl } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/bots' : '/bots';
  const u = query ? `${url}?query=${encodeURIComponent(query)}` : url;
  const res = await fetch(u, { method: 'GET' });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Bots list failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function botsCreateChatStep({ user_id, creator, message, apiUrl, state = {} } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/bots/create-chat' : '/bots/create-chat';
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id, creator, message, state }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Bot draft failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function finalizeBot({ user_id, creator, botDraft, apiUrl, bot_id } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/bots' : '/bots';
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id, creator, bot_id, bot: botDraft }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Finalize bot failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function submitTask({ user_id, task_type, payload = {}, apiUrl } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/tasks/submit' : '/tasks/submit';
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id, task_type, payload }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Task submit failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function getTask({ task_id, apiUrl } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/tasks/' + encodeURIComponent(task_id) : '/tasks/' + encodeURIComponent(task_id);
  const res = await fetch(url, { method: 'GET' });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Get task failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function addImageHistory({ user_id, action, apiUrl } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/image/history' : '/image/history';
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id, action }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Add image history failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function fetchImageHistory({ user_id, apiUrl } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/image/history/' + encodeURIComponent(user_id) : '/image/history/' + encodeURIComponent(user_id);
  const res = await fetch(url, { method: 'GET' });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Fetch image history failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function getBotImagePolicy({ bot_id, user_id, apiUrl } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + `/bots/${encodeURIComponent(bot_id)}/image-policy?user_id=${encodeURIComponent(user_id)}` : `/bots/${encodeURIComponent(bot_id)}/image-policy?user_id=${encodeURIComponent(user_id)}`;
  const res = await fetch(url, { method: 'GET' });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Get bot image policy failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function setBotImagePolicy({ bot_id, user_id, policy, apiUrl } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + `/bots/${encodeURIComponent(bot_id)}/image-policy` : `/bots/${encodeURIComponent(bot_id)}/image-policy`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id, policy }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Set bot image policy failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function recordImageFeedback({ image_key, feedback, apiUrl } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/image/feedback' : '/image/feedback';
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_key, feedback }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Record feedback failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function getImageFeedbackStats({ image_key, apiUrl } = {}) {
  const url = apiUrl ? apiUrl.replace(/\/$/, '') + '/image/feedback/' + encodeURIComponent(image_key) : '/image/feedback/' + encodeURIComponent(image_key);
  const res = await fetch(url, { method: 'GET' });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Get feedback stats failed: ${res.status} ${text}`);
  }
  return res.json();
}


