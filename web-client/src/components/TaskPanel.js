import React, { useEffect, useRef, useState } from 'react';
import { submitTask, getTask } from '../api';

function TaskPanel({ user, apiUrl, onTaskComplete }) {
  const [query, setQuery] = useState('');
  const [tasks, setTasks] = useState([]);
  const polls = useRef({});

  useEffect(() => {
    return () => {
      // clear polling on unmount
      Object.values(polls.current).forEach((id) => clearInterval(id));
      polls.current = {};
    };
  }, []);

  async function handleSubmit(e) {
    e && e.preventDefault && e.preventDefault();
    if (!query || !user) return;
    try {
      const payload = { query, language: 'en' };
      const res = await submitTask({ user_id: user.uid, task_type: 'web_search', payload, apiUrl });
      const tid = res?.task_id;
      if (!tid) throw new Error('No task id returned');
      const now = Date.now();
      const entry = {
        id: tid,
        query,
        status: 'queued',
        result: null,
        updated_at: now,
        progress: 0,
        started_at: now,
        history: [{ ts: now, progress: 0 }],
      };
      setTasks((t) => [entry, ...t]);

      // start polling
      const pollId = setInterval(async () => {
        try {
          const r = await getTask({ task_id: tid, apiUrl });
          if (r && r.ok && r.task) {
            const tstate = r.task;
            const progress = typeof tstate.progress === 'number' ? Math.max(0, Math.min(100, Math.round(tstate.progress))) : (tstate.status === 'completed' ? 100 : (tstate.status === 'failed' ? 0 : undefined));
            const started = tstate.started_at ? new Date(tstate.started_at).getTime() : undefined;
            const updated = Date.now();

            setTasks((cur) =>
              cur.map((it) => {
                if (it.id !== tid) return it;
                const history = Array.isArray(it.history) ? it.history.slice(-8) : [];
                if (typeof progress === 'number') {
                  history.push({ ts: updated, progress });
                  // keep last 8 samples
                  if (history.length > 8) history.splice(0, history.length - 8);
                }
                return { ...it, status: tstate.status || 'unknown', result: tstate.result || null, updated_at: updated, progress: progress, started_at: started || it.started_at, history };
              }),
            );

            if (tstate.status === 'completed' || tstate.status === 'failed') {
              clearInterval(polls.current[tid]);
              delete polls.current[tid];
              if (tstate.status === 'completed' && tstate.result && onTaskComplete) {
                try { onTaskComplete(tstate.result); } catch {}
              }
            }
          }
        } catch (err) {
          // ignore transient errors
        }
      }, 2000);

      polls.current[tid] = pollId;
      setQuery('');
    } catch (err) {
      // append a local transient task entry with error
      setTasks((t) => [{ id: 'err_' + Date.now(), query, status: 'error', result: String(err.message) }, ...t]);
    }
  }

  function estimateETA(task) {
    try {
      if (!task || !task.history || !task.started_at) return '—';
      const hist = Array.isArray(task.history) ? task.history.slice(-8) : [];
      if (!hist.length) return '—';

      // compute velocities between consecutive samples (progress/ms)
      const deltas = [];
      for (let i = 1; i < hist.length; i++) {
        const p0 = hist[i - 1];
        const p1 = hist[i];
        const dt = Math.max(1, p1.ts - p0.ts);
        const dp = p1.progress - p0.progress;
        deltas.push(dp / dt);
      }

      if (!deltas.length) return '—';

      // exponential moving average for smoothing
      const alpha = 0.4;
      let ema = deltas[0];
      for (let i = 1; i < deltas.length; i++) {
        ema = alpha * deltas[i] + (1 - alpha) * ema;
      }

      const last = hist[hist.length - 1];
      const progress = typeof last.progress === 'number' ? last.progress : undefined;
      if (typeof progress !== 'number') return '—';
      if (progress >= 100) return '0s';

      // velocity is progress per ms; convert to ms remaining
      const velocity = Math.max(ema, 0);
      if (velocity <= 0) return 'calculating…';
      const remainingProgress = Math.max(0, 100 - progress);
      const remainingMs = Math.round(remainingProgress / velocity);
      const s = Math.round(remainingMs / 1000);
      if (s < 60) return `${s}s`;
      const m = Math.round(s / 60);
      return `${m}m`;
    } catch {
      return '—';
    }
  }

  // optional: derive predicted percent when backend doesn't report progress
  function predictedPercent(task) {
    try {
      if (!task || !task.history || task.history.length < 2) return task.progress || 0;
      const hist = task.history.slice(-6);
      // compute avg velocity (dp/dt) over history
      let totalDp = 0;
      let totalDt = 0;
      for (let i = 1; i < hist.length; i++) {
        const p0 = hist[i - 1];
        const p1 = hist[i];
        const dt = Math.max(1, p1.ts - p0.ts);
        const dp = p1.progress - p0.progress;
        totalDp += dp;
        totalDt += dt;
      }
      if (totalDt <= 0) return task.progress || 0;
      const vel = totalDp / totalDt; // progress per ms
      const now = Date.now();
      const last = hist[hist.length - 1];
      const est = (last.progress || 0) + vel * Math.max(0, now - last.ts);
      return Math.max(0, Math.min(100, Math.round(est)));
    } catch {
      return task.progress || 0;
    }
  }

  return (
    <div className="taskPanel">
      <div className="panelTitle">Background Tasks</div>
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, marginTop: 8 }}>
        <input className="taskInput" placeholder="Background web-search query" value={query} onChange={(e) => setQuery(e.target.value)} />
        <button className="primaryBtn" type="submit" disabled={!query || !user}>Submit</button>
      </form>

      <div className="taskList">
        {tasks.length === 0 ? (
            <div className="panelEmpty" style={{ marginTop: 10 }}>No background tasks yet.</div>
          ) : (
            tasks.map((t) => (
              <div key={t.id} className="taskItem">
                <div className="taskRow">
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ fontWeight: 900 }}>{t.query}</div>
                      <div style={{ color: 'var(--muted)', fontSize: 12 }}>{t.id}</div>
                    </div>
                    <div className="taskMeta">
                      {t.status}
                      {typeof (t.progress) === 'number' ? ` • ${t.progress}%` : ` • ${predictedPercent(t)}%`}
                      {(t.history && t.history.length > 0) ? ` • ETA ${estimateETA(t)}` : ''}
                      {(t.status !== 'completed' && t.status !== 'failed') ? (
                        <span style={{ marginLeft: 8 }}><span className="taskSpinner" aria-hidden="true" /></span>
                      ) : null}
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <div className="progressBar">
                        <div className="progressFill" style={{ width: `${t.progress || 0}%` }} />
                      </div>
                    </div>
                  </div>
                  <div>
                    {t.status === 'completed' && t.result ? (
                      <button className="ghostBtn" type="button" onClick={() => onTaskComplete && onTaskComplete(t.result)}>Insert</button>
                    ) : null}
                  </div>
                </div>
                {t.status === 'completed' && t.result && (
                  <div className="taskResult">
                    <div className="sourceCardSnippet">{String(t.result.reply || JSON.stringify(t.result)).slice(0, 320)}</div>
                  </div>
                )}
              </div>
            ))
          )}
      </div>
    </div>
  );
}

export default TaskPanel;
