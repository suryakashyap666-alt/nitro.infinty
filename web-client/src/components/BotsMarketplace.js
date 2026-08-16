import React, { useEffect, useMemo, useState } from 'react';

import { fetchBotsList } from '../api';

function BotCard({ bot, onSelectBot }) {
  const skills = bot.skills || [];

  const supportedLanguages = Array.isArray(bot.supportedLanguages) ? bot.supportedLanguages : [];
  const voiceSupport = bot.voiceSupport !== undefined ? Boolean(bot.voiceSupport) : false;
  const autoDetectLanguage = bot.autoDetectLanguage !== undefined ? Boolean(bot.autoDetectLanguage) : false;

  return (
    <div className="botCard" role="article" aria-label={bot.name} onClick={() => onSelectBot?.(bot)} style={{ cursor: onSelectBot ? 'pointer' : undefined }}>

      <div className="botCardTop">
        <div className="botIcon" aria-hidden="true">{bot.icon || '🤖'}</div>
        <div className="botCardTitleWrap">
          <div className="botName">{bot.name}</div>
          <div className="botCategory">Category: {bot.category || 'general'}</div>
        </div>
        <div className="botRatings">
          <div className="botRatingValue">{Number(bot.ratings || 0).toFixed(1)}</div>
          <div className="botRatingLabel">★ rating</div>
        </div>
      </div>

      <div className="botSkillsRow">
        {skills.slice(0, 6).map((s, i) => (
          <span key={s + '_' + i} className="skillPill">{s}</span>
        ))}
      </div>

      <div className="botDesc">{bot.description}</div>

      <div className="botLangMeta" style={{ marginTop: 10, display: 'grid', gap: 6 }}>
        <div style={{ fontSize: 12, opacity: 0.95 }}>
          <b>Languages:</b>{' '}
          {supportedLanguages.length ? supportedLanguages.join(', ') : '—'}
        </div>
        <div style={{ fontSize: 12, opacity: 0.95 }}>
          <b>Voice:</b> {voiceSupport ? 'Supported' : 'Not available'}
        </div>
        <div style={{ fontSize: 12, opacity: 0.95 }}>
          <b>Auto-detect:</b> {autoDetectLanguage ? 'Yes' : 'No'}
        </div>
      </div>

      <div className="botFooter" style={{ marginTop: 10 }}>
        <span className="botCreator">Created by: {bot.creator || 'Nitro Infinity AI'}</span>
      </div>
    </div>
  );
}

function ScreenHeader({ title, subtitle }) {
  return (
    <div className="botsScreenHeader">
      <div className="botsHeaderGlow" aria-hidden="true" />
      <div className="botsHeaderText">
        <div className="botsTitle">{title}</div>
        {subtitle ? <div className="botsSubtitle">{subtitle}</div> : null}
      </div>
    </div>
  );
}

export default function BotsMarketplace({ user, onOpenCreateBot, onSelectBot }) {

  const [query, setQuery] = useState('');
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function loadBots(nextQuery) {
    setLoading(true);
    setError('');
    try {
      const res = await fetchBotsList({ apiUrl: undefined, query: nextQuery });
      setBots(Array.isArray(res?.bots) ? res.bots : []);
    } catch (e) {
      setError(e?.message || 'Failed to load bots');
      setBots([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadBots(query);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  const statusText = useMemo(() => {
    if (loading) return 'Scanning bots…';
    return `${bots.length} bots available`;
  }, [bots.length, loading]);

  return (
    <div className="botsScreen" role="main">
      <ScreenHeader title="AI Bots Marketplace" subtitle={statusText} />

      <div className="botsSearchWrap">
        <div className="botsSearchIcon" aria-hidden="true">🔎</div>
        <input
          className="botsSearchInput"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by math, coding, tutor, emotional, reasoning, exam…"
          aria-label="Search bots"
        />
        {query ? (
          <button className="botsClearBtn" type="button" onClick={() => setQuery('')} aria-label="Clear search">
            ✕
          </button>
        ) : null}
      </div>

      {error ? <div className="botsError">{error}</div> : null}

      <div className="botsList" role="list">
        {loading ? (
          <div className="botsLoading">Loading bots…</div>
        ) : (
          bots.map((bot) => (
            <div key={bot.name + '_' + bot.creator + '_' + bot.category} role="listitem">
              <BotCard bot={bot} />
            </div>
          ))
        )}
      </div>

      <button className="createBotFab" type="button" onClick={onOpenCreateBot} aria-label="Create Bot">
        <span className="createBotFabPlus" aria-hidden="true">+</span>
      </button>
    </div>
  );
}

