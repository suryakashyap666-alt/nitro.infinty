import React, { useEffect, useState } from 'react';
import {getBotImagePolicy, setBotImagePolicy  } from '../api';

export default function BotSettings({ bot, user, apiUrl, onClose }) {
  const [policy, setPolicy] = useState({
    contextUnderstandingEnabled: false,
    useUserHistoryUnderstanding: false,
    useWebAssistance: false,
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      try {
        const res = await getBotImagePolicy({ bot_id: bot.id, user_id: user.uid, apiUrl });
        if (!mounted) return;
        setPolicy(res || policy);
      } catch (e) {
        // ignore
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bot?.id]);

  function toggle(key) {
    setPolicy((p) => ({ ...p, [key]: !Boolean(p[key]) }));
  }

  async function save() {
    setSaving(true);
    try {
      await setBotImagePolicy({ bot_id: bot.id, user_id: user.uid, policy, apiUrl });
      onClose?.();
    } catch (e) {
      // ignore for now
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="profileOverlay open" onClick={onClose}>
      <div className="profilePanel" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 640 }}>
        <div className="profileHeader">
          <div>
            <div className="panelTitle">Bot Settings</div>
            <div className="mutedSmall">Configure context and web assistance for this bot</div>
          </div>
          <button className="ghostBtn" type="button" onClick={onClose}>Close</button>
        </div>

        <div style={{ padding: 14 }}>
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontWeight: 900 }}>{bot.name}</div>
            <div style={{ color: 'var(--muted)', fontSize: 13 }}>{bot.description}</div>
          </div>

          <div style={{ display: 'grid', gap: 10 }}>
            <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 800 }}>Context understanding</div>
                <div className="mutedSmall">Allow this bot to use context resolution and intent detection.</div>
              </div>
              <input type="checkbox" checked={policy.contextUnderstandingEnabled} onChange={() => toggle('contextUnderstandingEnabled')} />
            </label>

            <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 800 }}>Use user history</div>
                <div className="mutedSmall">Allow using persisted user history for better reference resolution (disabled for guest users).</div>
              </div>
              <input type="checkbox" checked={policy.useUserHistoryUnderstanding} onChange={() => toggle('useUserHistoryUnderstanding')} />
            </label>

            <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 800 }}>Web assistance</div>
                <div className="mutedSmall">Allow the bot to perform live web searches for time-sensitive queries.</div>
              </div>
              <input type="checkbox" checked={policy.useWebAssistance} onChange={() => toggle('useWebAssistance')} />
            </label>

            <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
              <button className="primaryBtn" type="button" onClick={save} disabled={saving || loading}>{saving ? 'Saving…' : 'Save'}</button>
              <button className="ghostBtn" type="button" onClick={onClose}>Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
