import React, { useEffect, useMemo, useRef, useState } from 'react';

import { botsCreateChatStep, finalizeBot } from '../api';

export default function BotCreateScreen({ user, onDone, onBackToMarketplace }) {
  const [conversation, setConversation] = useState([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [draft, setDraft] = useState({});

  const scrollerRef = useRef(null);

  const creatorUserId = user?.uid || 'guest_1';
  const creatorDisplayName = user?.displayName || user?.uid || 'Nitro Infinity AI';

  useEffect(() => {
    setConversation([
      {
        id: 'm0',
        role: 'ai',
        content:
          'Welcome to Nitro Bot Builder. Tell me what kind of bot you want to create (coding/bot creation/UI planning only).\n\nStart with:\n- Name: …\n- Description: …\n- Skills: …\n\nWhen you are done, say: The AI is now done',
        ts: new Date().toISOString(),
        agent: 'bot_builder',
      },
    ]);
  }, []);

  useEffect(() => {
    const el = scrollerRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [conversation.length, busy]);

  const canSend = useMemo(() => input.trim().length > 0 && !busy, [input, busy]);

  async function send() {
    if (!canSend) return;

    setError('');
    const userText = input;
    setInput('');

    setConversation((c) => [
      ...c,
      { id: 'u_' + Date.now(), role: 'user', content: userText, ts: new Date().toISOString() },
    ]);

    setBusy(true);
    try {
      const res = await botsCreateChatStep({
        user_id: creatorUserId,
        creator: creatorDisplayName,
        message: userText,
        apiUrl: undefined,
        state: draft,
      });

      if (res?.botDraft) setDraft(res.botDraft);

      setConversation((c) => [
        ...c,
        { id: 'a_' + Date.now(), role: 'ai', content: res?.reply || '', ts: new Date().toISOString(), agent: 'bot_builder' },
      ]);

      if (res?.done) {
        const finalRes = await finalizeBot({
          user_id: creatorUserId,
          creator: creatorDisplayName,
          botDraft: res.botDraft,
          apiUrl: undefined,
        });

        setConversation((c) => [
          ...c,
          {
            id: 'a_done_' + Date.now(),
            role: 'ai',
            content: finalRes?.bot?.name
              ? `Saved: ${finalRes.bot.name}. Added to Bots Marketplace. 🎉`
              : 'Saved bot to Bots Marketplace.',
            ts: new Date().toISOString(),
            agent: 'bot_builder',
          },
        ]);

        setTimeout(() => {
          onDone(finalRes?.bot || res.botDraft);
        }, 650);
      }
    } catch (e) {
      setError(e?.message || 'Bot creation failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="createBotScreen" role="main">
      <div className="createBotHeader">
        <button className="ghostBtn" type="button" onClick={onBackToMarketplace}>
          ← Marketplace
        </button>
        <div>
          <div className="panelTitle">Create Bot</div>
          <div className="mutedSmall">Coding, bot creation, and UI planning only.</div>
        </div>
        <div />
      </div>

      <div className="createBotBody">
        <div className="createBotScroll" ref={scrollerRef}>
          {conversation.map((m) => (
            <div key={m.id} className={m.role === 'user' ? 'userRow' : 'assistantRow'}>
              <div className={m.role === 'user' ? 'userAvatar' : 'assistantAvatar'} aria-hidden="true">
                {m.role === 'user' ? '🧑‍💻' : '🤖'}
              </div>
              <div className={m.role === 'user' ? 'userBubble' : 'assistantBubble'}>{m.content}</div>
            </div>
          ))}

          {busy ? (
            <div className="assistantRow">
              <div className="assistantAvatar" aria-hidden="true">🤖</div>
              <div className="assistantBubble">
                <div className="typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          ) : null}
        </div>

      <div className="createBotDraftPanel">
          <div className="panelTitle">Draft preview</div>
          <div className="draftRow">
            <div className="draftIcon" aria-hidden="true">{draft?.icon || '✨'}</div>
            <div>
              <div className="draftName">{draft?.name || 'Custom Bot'}</div>
              <div className="draftCategory">{draft?.category || 'coding'}</div>
            </div>
          </div>
          <div className="draftDesc">{draft?.description || 'Add a short description for your bot.'}</div>
          <div className="draftSkills">
            {(draft?.skills || []).slice(0, 10).map((s, i) => (
              <span key={s + '_' + i} className="skillPill">{s}</span>
            ))}
          </div>

          <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,.08)', display: 'grid', gap: 10 }}>
            <div style={{ fontSize: 13, opacity: 0.95 }}>
              <b>Education System Intelligence</b>
              <div className="mutedSmall" style={{ marginTop: 4 }}>
                Enable adaptive teaching, quizzes, worksheets, and study plans.
              </div>
              <label style={{ display: 'block', marginTop: 8, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={draft?.educationEnabled !== undefined ? Boolean(draft.educationEnabled) : false}
                  disabled={busy}
                  onChange={(e) => {
                    const next = e.target.checked;
                    setDraft((d) => ({
                      ...(d || {}),
                      educationEnabled: next,
                    }));
                  }}
                />{' '}
                {draft?.educationEnabled ? 'Enabled' : 'Disabled'}
              </label>
            </div>

            <div style={{ fontSize: 13, opacity: 0.95 }}>
              <b>Use Global Language System</b>


              <div className="mutedSmall" style={{ marginTop: 4 }}>
                Auto-detect user language and switch replies instantly.
              </div>
              <label style={{ display: 'block', marginTop: 8, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={draft?.useGlobalLanguageSystem !== undefined ? Boolean(draft.useGlobalLanguageSystem) : true}
                  disabled={busy}
                  onChange={(e) => {
                    const next = e.target.checked;
                    setDraft((d) => ({
                      ...(d || {}),
                      useGlobalLanguageSystem: next,
                    }));
                  }}
                />{' '}
                {draft?.useGlobalLanguageSystem ? 'Enabled' : 'Disabled'}
              </label>
            </div>

            {draft?.useGlobalLanguageSystem === false ? (
              <div style={{ display: 'grid', gap: 8 }}>
                <div style={{ fontSize: 13, opacity: 0.95 }}>
                  <b>Manual Language Selection</b>
                  <div className="mutedSmall" style={{ marginTop: 4 }}>
                    Bot will use only the selected languages; no auto language switching.
                  </div>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {[
                    { code: 'en', name: 'English' },
                    { code: 'hi', name: 'Hindi' },
                    { code: 'ja', name: 'Japanese' },
                    { code: 'ar', name: 'Arabic' },
                    { code: 'es', name: 'Spanish' },
                    { code: 'fr', name: 'French' },
                    { code: 'zh', name: 'Chinese' },
                    { code: 'ru', name: 'Russian' },
                    { code: 'bn', name: 'Bengali' },
                    { code: 'ta', name: 'Tamil' },
                    { code: 'ur', name: 'Urdu' },
                  ].map((l) => {
                    const selected = Array.isArray(draft?.selectedLanguages)
                      ? draft.selectedLanguages.includes(l.code)
                      : false;
                    return (
                      <label key={l.code} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, opacity: 0.95 }}>
                        <input
                          type="checkbox"
                          checked={selected}
                          disabled={busy}
                          onChange={(e) => {
                            const checked = e.target.checked;
                            setDraft((d) => {
                              const prev = Array.isArray(d?.selectedLanguages) ? d.selectedLanguages : [];
                              const next = checked ? Array.from(new Set([...prev, l.code])) : prev.filter((x) => x !== l.code);
                              return { ...(d || {}), selectedLanguages: next };
                            });
                          }}
                        />
                        {l.name}
                      </label>
                    );
                  })}
                </div>

                <div style={{ display: 'grid', gap: 6, fontSize: 13, opacity: 0.95 }}>
                  <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span><b>Preferred reply language</b></span>
                    <select
                      value={draft?.preferredLanguage || 'en'}
                      disabled={busy}
                      onChange={(e) => setDraft((d) => ({ ...(d || {}), preferredLanguage: e.target.value }))}
                      style={{ minWidth: 120, padding: 6, borderRadius: 6, border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.04)', color: 'inherit' }}
                    >
                      {[
                        { code: 'en', name: 'English' },
                        { code: 'hi', name: 'Hindi' },
                        { code: 'ja', name: 'Japanese' },
                        { code: 'ar', name: 'Arabic' },
                        { code: 'es', name: 'Spanish' },
                        { code: 'fr', name: 'French' },
                        { code: 'zh', name: 'Chinese' },
                        { code: 'ru', name: 'Russian' },
                        { code: 'bn', name: 'Bengali' },
                        { code: 'ta', name: 'Tamil' },
                        { code: 'ur', name: 'Urdu' },
                      ].map((l) => (
                        <option key={l.code} value={l.code}>{l.name}</option>
                      ))}
                    </select>
                  </label>
                </div>
              </div>
            ) : null}

            <div style={{ fontSize: 13, opacity: 0.95 }}>
              <b>Image Generation & Detection</b>
              <div className="mutedSmall" style={{ marginTop: 4 }}>
                Control whether this bot can generate images or perform image analysis/detection.
              </div>
              <label style={{ display: 'block', marginTop: 8, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={draft?.imageGenerationEnabled !== undefined ? Boolean(draft.imageGenerationEnabled) : true}
                  disabled={busy}
                  onChange={(e) => {
                    const next = e.target.checked;
                    setDraft((d) => ({ ...(d || {}), imageGenerationEnabled: next }));
                  }}
                />{' '}
                {draft?.imageGenerationEnabled ? 'Generation enabled' : 'Generation disabled'}
              </label>

              <label style={{ display: 'block', marginTop: 8, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={draft?.imageDetectionEnabled !== undefined ? Boolean(draft.imageDetectionEnabled) : true}
                  disabled={busy}
                  onChange={(e) => {
                    const next = e.target.checked;
                    setDraft((d) => ({ ...(d || {}), imageDetectionEnabled: next }));
                  }}
                />{' '}
                {draft?.imageDetectionEnabled ? 'Detection enabled' : 'Detection disabled'}
              </label>
            </div>
          </div>
        </div>
      </div>

      {error ? <div className="botsError" style={{ marginTop: 10 }}>{error}</div> : null}

      <div className="createBotInputDock">
        <textarea
          className="createBotInput"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={2}
          placeholder="Describe the bot you want to build… (Only coding/bot creation/UI planning)"
          disabled={busy}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />

        <button
          className={canSend ? 'createBotSendBtn' : 'createBotSendBtn disabled'}
          type="button"
          onClick={send}
          disabled={!canSend}
          aria-label="Send create bot message"
        >
          ⬆️
        </button>
      </div>
    </div>
  );
}

