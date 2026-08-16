import React, { useState } from 'react';
import { recordImageFeedback, getImageFeedbackStats } from '../api';

function formatTimestamp(ts) {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

function AnalysisCard({ analysis }) {
  if (!analysis) return null;

  const ai = Math.round((analysis.ai_probability ?? analysis.aiProbability ?? 0) * 100);
  const human = 100 - ai;
  const label = analysis.likely_label || analysis.likelyLabel || analysis.label || '';

  const indicators = analysis.indicators || {};

  const likelyBg = label.includes('human')
    ? 'rgba(120,255,190,0.12)'
    : label.includes('AI')
      ? 'rgba(255,120,220,0.10)'
      : 'rgba(150,180,255,0.10)';

  return (
    <div className="analysisCard" style={{ background: likelyBg }}>
      <div className="analysisTop">
        <div className="analysisTitle">Image Analysis</div>
        <div className="analysisLabel">{label || 'mixed/edited'}</div>
      </div>

      <div className="analysisBars">
        <div className="analysisBar">
          <div className="analysisBarLabel">AI-generated</div>
          <div className="analysisBarTrack">
            <div className="analysisBarFill ai" style={{ width: `${ai}%` }} />
          </div>
          <div className="analysisBarPct">{ai}%</div>
        </div>

        <div className="analysisBar">
          <div className="analysisBarLabel">Human-made</div>
          <div className="analysisBarTrack">
            <div className="analysisBarFill human" style={{ width: `${human}%` }} />
          </div>
          <div className="analysisBarPct">{human}%</div>
        </div>
      </div>

      <div className="analysisIndicators">
        {Object.entries(indicators)
          .slice(0, 5)
          .map(([k, v]) => (
            <div key={k} className="analysisIndicator">
              <span className="analysisIndicatorKey">{k}</span>
              <span className="analysisIndicatorVal">{Math.round(Number(v) * 100)}%</span>
            </div>
          ))}
      </div>

      <div className="analysisFooter">Safety heuristics + signature indicators (lightweight)</div>
    </div>
  );
}

function SourceCard({ source }) {
  return (
    <div className="sourceCard">
      <a href={source.url} target="_blank" rel="noreferrer" className="sourceCardTitle">
        {source.title || source.domain}
      </a>
      {source.snippet ? <div className="sourceCardSnippet">{source.snippet}</div> : null}
      <div className="sourceCardMeta">
        <span>{source.domain}</span>
        {source.trusted ? <span className="trustedBadge">Trusted</span> : null}
      </div>
    </div>
  );
}

function ImageMessage({ img }) {
  const action = img?.action || img;
  const dataUrl =
    action?.image?.data_url ||
    action?.image?.dataUrl ||
    action?.image?.url ||
    action?.image?.dataURI ||
    action?.image?.src;

  const analysis = action?.analysis || action?.imageAnalysis;
  const contentType = action?.image?.contentType || action?.image?.type;

  const prompt = action?.prompt || img?.prompt || '';
  const quality = action?.quality || action?.plan?.quality;
  const style = action?.style || action?.plan?.style;
  const [feedbackStats, setFeedbackStats] = useState(null);
  const [userFeedback, setUserFeedback] = useState(null);

  const imageKey = `${style}_${quality}`.replace(/\s+/g, '_');

  React.useEffect(() => {
    if (imageKey && imageKey !== '__') {
      getImageFeedbackStats({ image_key: imageKey, apiUrl: '' })
        .then((res) => setFeedbackStats(res?.stats || {}))
        .catch(() => {});
    }
  }, [imageKey]);

  if (!img) return null;

  const canRender = Boolean(dataUrl) && (String(contentType || '').includes('svg') || String(dataUrl).startsWith('data:image'));

  if (!canRender) {
    return (
      <div className="imageShell">
        <div className="mutedSmall">Image preview unavailable.</div>
      </div>
    );
  }

  return (
    <div className="imageShell">
      <div className="imageMeta">
        <div className="imageMetaLeft">
          <div className="imageMetaBadge">Image</div>
          <div className="imageMetaText">{style ? `${style}` : '—'} {quality ? `• ${quality}` : ''}</div>
        </div>
      </div>

      <img className="chatImage" src={dataUrl} alt={prompt ? `Generated image: ${prompt}` : 'Generated image'} />

      {analysis ? <AnalysisCard analysis={analysis} /> : null}

      {prompt ? <div className="imagePrompt">{prompt}</div> : null}

      <div className="imageActions">
        <button
          type="button"
          className="ghostBtn small"
          title="Copy image URL to clipboard"
          onClick={async () => {
            try {
              if (navigator.clipboard && dataUrl) {
                await navigator.clipboard.writeText(dataUrl);
                alert('Image URL copied to clipboard');
              }
            } catch (e) {
              try { alert('Failed to copy'); } catch {}
            }
          }}
        >
          📋 Copy
        </button>

        <button
          type="button"
          className="ghostBtn small"
          title="Like this image design"
          style={{ color: userFeedback === 'like' ? '#ff1493' : 'inherit' }}
          onClick={() => {
            recordImageFeedback({ image_key: imageKey, feedback: 'like', apiUrl: '' })
              .then((res) => {
                setFeedbackStats(res?.stats || {});
                setUserFeedback('like');
              })
              .catch(() => {});
          }}
        >
          ❤️ Like {feedbackStats?.likes ? `(${feedbackStats.likes})` : ''}
        </button>

        <button
          type="button"
          className="ghostBtn small"
          title="Dislike this image design"
          style={{ color: userFeedback === 'dislike' ? '#ff6b6b' : 'inherit' }}
          onClick={() => {
            recordImageFeedback({ image_key: imageKey, feedback: 'dislike', apiUrl: '' })
              .then((res) => {
                setFeedbackStats(res?.stats || {});
                setUserFeedback('dislike');
              })
              .catch(() => {});
          }}
        >
          👎 Dislike {feedbackStats?.dislikes ? `(${feedbackStats.dislikes})` : ''}
        </button>

        <button
          type="button"
          className="ghostBtn small"
          title="Regenerate similar image"
          onClick={() => {
            const el = document.querySelector('.aiInputText');
            if (el) {
              el.value = prompt;
              el.focus();
            }
          }}
        >
          🔄 Reload
        </button>

        <button
          type="button"
          className="ghostBtn small"
          onClick={() => {
            const w = window.open('about:blank', '_blank');
            if (w) {
              w.document.write(`<title>Nitro Infinity AI Image</title><img style='max-width:100%;height:auto' src='${dataUrl}'/>`);
              w.document.close();
            }
          }}
        >
          Fullscreen
        </button>

        <a
          className="ghostBtn small"
          download={prompt ? prompt.slice(0, 30).replace(/\s+/g, '_') : 'nitro_ai_image'}
          href={dataUrl}
        >
          Download
        </a>
      </div>
    </div>
  );
}

export default function Message({ msg }) {
  const isUser = msg.role === 'user';
  const [showMoreState, setShowMoreState] = React.useState(false);

  function extractShort(full) {
    if (!full) return '';
    const lines = String(full).split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    // prefer explicit markers
    for (const l of lines) {
      if (/^\s*(Result:|Answer:)\s*/i.test(l)) return l.replace(/^\s*(Result:|Answer:)\s*/i, '');
    }
    // fallback to first non-empty line
    return lines.length ? lines[0] : String(full).slice(0, 120);
  }

  return (
    <div className={isUser ? 'userRow' : 'assistantRow'}>
      {!isUser && <div className="assistantAvatar" aria-hidden="true">⚡</div>}

      <div className={isUser ? 'userBubble' : 'assistantBubble'}>
        {msg.imageAction || msg.image || (msg.action?.type === 'generate' || msg.action?.type === 'analyze') ? (
          <ImageMessage img={msg.imageAction || msg.image || msg.action || msg} />
        ) : (
          <>
            {/* Short answer + Show more toggle */}
            <div className="shortAnswerContainer">
              <div className="shortAnswer">{extractShort(msg.content)}</div>
              {String(msg.content || '').length > (extractShort(msg.content || '').length + 5) ? (
                <button className="showMoreBtn" type="button" onClick={() => setShowMoreState((s) => !s)}>
                  {showMoreState ? 'Show less' : 'Show more'}
                </button>
              ) : null}
            </div>

            <div className="fullAnswer" style={{ display: showMoreState ? 'block' : 'none', marginTop: 8 }}>
              <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{msg.content}</pre>
            </div>

            {Array.isArray(msg.sources) && msg.sources.length > 0 ? (
              <div className="sourceCardList">
                <div className="sourceCardHeading">Live search sources</div>
                {msg.sources.map((source, index) => (
                  <SourceCard key={`${source.url || source.domain}-${index}`} source={source} />
                ))}
              </div>
            ) : null}
          </>
        )}

        <div className="msgMeta">
          <span>{msg.agent ? msg.agent : isUser ? 'You' : 'Nitro Infinity AI'}</span>
          {msg.ts ? <span className="metaSep">•</span> : null}
          {msg.ts ? <span>{formatTimestamp(msg.ts)}</span> : null}
        </div>
      </div>

      {isUser && <div className="userAvatar" aria-hidden="true">🙂</div>}
    </div>
  );
}

