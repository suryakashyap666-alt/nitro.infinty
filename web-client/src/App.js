import React, { useEffect, useRef, useState } from 'react';
import './styles.css';
import { db, auth, saveChatEvent } from './firebaseConfig';

/**
 * Normalizes and inspects any Nitro AI graphic payload into a browser-safe Data URI.
 */
function normalizeAndInspectImagePayload(rawPayload, prompt = '') {
  if (!rawPayload) return createFallbackCanvasDataUri(prompt);

  let data = typeof rawPayload === 'object'
    ? (rawPayload.image_data || rawPayload.imageUrl || rawPayload.data_url || rawPayload.src || '')
    : String(rawPayload).trim();

  const mdMatch = data.match(/!\[.*?\]\((.*?)\)/);
  if (mdMatch) data = mdMatch[1].trim();

  data = data.replace(/^["']|["']$/g, '').trim();

  if (data.startsWith('<svg') || data.includes('<svg')) {
    try {
      const cleanSvg = data.match(/<svg[\s\S]*?<\/svg>/)?.[0] || data;
      return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(cleanSvg)))}`;
    } catch (e) {
      return `data:image/svg+xml;utf8,${encodeURIComponent(data)}`;
    }
  }

  if (data.startsWith('http://') || data.startsWith('https://')) return data;

  if (data.startsWith('data:image/')) {
    const [header, body] = data.split(',');
    if (body) return `${header},${body.replace(/\s+/g, '')}`;
    return data;
  }

  const cleanBase64 = data.replace(/\s+/g, '');
  if (cleanBase64.startsWith('iVBORw0KGgo')) return `data:image/png;base64,${cleanBase64}`;
  if (cleanBase64.startsWith('/9j/')) return `data:image/jpeg;base64,${cleanBase64}`;
  if (cleanBase64.startsWith('PHN2Zy') || cleanBase64.startsWith('PD94bW')) return `data:image/svg+xml;base64,${cleanBase64}`;

  return `data:image/png;base64,${cleanBase64}`;
}

function createFallbackCanvasDataUri(prompt = 'Nitro Graphic') {
  const safeText = prompt.slice(0, 40).replace(/[^a-zA-Z0-9 ]/g, '') || 'Nitro Graphic';
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='800' height='800' viewBox='0 0 800 800'>
    <defs>
      <linearGradient id='bgGrad' x1='0%' y1='0%' x2='100%' y2='100%'>
        <stop offset='0%' stop-color='#0f172a'/>
        <stop offset='100%' stop-color='#020617'/>
      </linearGradient>
    </defs>
    <rect width='100%' height='100%' fill='url(#bgGrad)'/>
    <circle cx='400' cy='400' r='180' fill='#0284c7' opacity='0.85'/>
    <text x='400' y='720' fill='#f8fafc' font-size='22' font-weight='700' font-family='sans-serif' text-anchor='middle'>⚡ NITRO AI: ${safeText}</text>
  </svg>`;
  return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`;
}

// Client-side math evaluator for instant step-by-step solving
function trySolveMath(text) {
  const clean = text.toLowerCase().replace(/^(solve|calculate|compute|what is)\s*/, '').trim();
  const linearMatch = clean.match(/^([+-]?\d*)\s*x\s*([+-]\s*\d+)?\s*=\s*([+-]?\d+)$/);
  if (linearMatch) {
    const a = parseFloat(linearMatch[1] === '' || linearMatch[1] === '+' ? '1' : linearMatch[1] === '-' ? '-1' : linearMatch[1]);
    const b = linearMatch[2] ? parseFloat(linearMatch[2].replace(/\s+/g, '')) : 0;
    const c = parseFloat(linearMatch[3]);
    const x = (c - b) / a;
    return `**Problem:** Solve \`${clean}\`\n\n**Step-by-step Solution:**\n1. Subtract \`${b}\` from both sides: \`${a}x = ${c - b}\`\n2. Divide both sides by \`${a}\`: \`x = ${x}\`\n\n**Final Answer:** \`x = ${x}\``;
  }
  return null;
}

function App() {
  const [messages, setMessages] = useState([]);
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [activeAgent, setActiveAgent] = useState('nitro-core');
  const [emotion, setEmotion] = useState('neutral');
  const [voiceActive, setVoiceActive] = useState(false);

  // Free Cloud Key stored in React environment or user input
  const [userApiKey, setUserApiKey] = useState(
    process.env.REACT_APP_NITRO_CLOUD_API_KEY || ''
  );

  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    document.title = 'Nitro Infinity AI (Spark Free Edition)';
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        type: 'text',
        text: 'Welcome to Nitro Infinity AI! Running 100% free on Firebase Spark. Ask questions, solve math equations, or generate graphics.',
        agent: 'nitro',
        ts: Date.now(),
      },
    ]);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinking]);

  const sendMessage = async (rawText) => {
    const text = (rawText || '').trim();
    if (!text) return;

    const userMessageId = `user-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: userMessageId, role: 'user', type: 'text', text, agent: activeAgent, ts: Date.now() },
    ]);
    setInputValue('');
    setThinking(true);
    setError(null);

    // Save to Firebase Spark Firestore Database
    const currentUid = auth?.currentUser?.uid || 'guest_user';
    saveChatEvent(currentUid, { role: 'user', content: text }).catch(() => {});

    const assistantMessageId = `assistant-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMessageId,
        role: 'assistant',
        type: 'text',
        text: '',
        imageData: null,
        prompt: null,
        agent: 'nitro',
        ts: Date.now(),
      },
    ]);

    // 1. Check for Image Generation Intent
    if (/^(make|generate|draw|create)\s+an?\s+(image|picture|graphic|art)/i.test(text)) {
      const prompt = text.replace(/^(make|generate|draw|create)\s+an?\s+(image|picture|graphic|art)\s*(of)?\s*/i, '');
      const uri = createFallbackCanvasDataUri(prompt);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, type: 'image', imageData: uri, prompt, text: '' }
            : msg
        )
      );
      saveChatEvent(currentUid, { role: 'assistant', type: 'image', prompt }).catch(() => {});
      setThinking(false);
      return;
    }

    // 2. Check for Math Expression
    const mathAnswer = trySolveMath(text);
    if (mathAnswer) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId ? { ...msg, text: mathAnswer } : msg
        )
      );
      saveChatEvent(currentUid, { role: 'assistant', content: mathAnswer }).catch(() => {});
      setThinking(false);
      return;
    }

    // 3. Conversational AI via 100% Free Open Model Endpoint
    try {
      const apiKey = userApiKey.trim();
      if (!apiKey) {
        throw new Error('Please enter your free key (starts with sk-or-v1-...) in the input box at the top right.');
      }

      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
          'HTTP-Referer': window.location.origin,
          'X-Title': 'Nitro Infinity AI',
        },
        body: JSON.stringify({
          model: 'meta-llama/llama-3.3-70b-instruct:free',
          messages: [
            {
              role: 'system',
              content: 'You are Nitro Infinity AI. You are natural, articulate, intelligent, friendly, and helpful. Never reply with robotic boilerplate.',
            },
            { role: 'user', content: text },
          ],
        }),
      });

      if (!response.ok) {
        throw new Error(`Cloud returned status ${response.status}. Verify your free API key.`);
      }

      const data = await response.json();
      const reply = data?.choices?.[0]?.message?.content || 'Nitro AI received your message.';

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId ? { ...msg, text: reply } : msg
        )
      );

      saveChatEvent(currentUid, { role: 'assistant', content: reply }).catch(() => {});
    } catch (err) {
      setError(err.message);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, text: `[Error: ${err.message}]` }
            : msg
        )
      );
    } finally {
      setThinking(false);
    }
  };

  const handleVoiceClick = () => {
    const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionCtor) {
      setError('Speech recognition not supported in this browser.');
      return;
    }

    if (voiceActive && recognitionRef.current) {
      recognitionRef.current.stop();
      setVoiceActive(false);
      return;
    }

    const recognition = new SpeechRecognitionCtor();
    recognition.lang = 'en-US';
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || '';
      if (transcript) setInputValue((prev) => (prev ? `${prev} ${transcript}` : transcript));
    };
    recognition.onerror = () => setVoiceActive(false);
    recognition.onend = () => setVoiceActive(false);

    recognitionRef.current = recognition;
    setVoiceActive(true);
    recognition.start();
  };

  return (
    <div className="AppShell">
      <div className="AppGrid">
        <div className="card chatCard">
          <div className="AiTopBar">
            <div className="aiHeadingWrap">
              <div className="aiHeading">NITRO INFINITY AI</div>
              <div className="aiSubheading">100% Free Firebase Spark Plan • Database & AI Studio Active</div>
            </div>
          </div>

          <div className="chatWrap">
            <div className="topBadges">
              <div className="badge">
                <span className="badgeLabel">Tier</span>
                <span className="badgeValue">Spark Free Plan ($0)</span>
              </div>
              <div className="badge">
                <span className="badgeLabel">Database</span>
                <span className="badgeValue">Firestore Active</span>
              </div>

              <input
                type="password"
                value={userApiKey}
                onChange={(e) => setUserApiKey(e.target.value)}
                placeholder="Paste free key (sk-or-v1-...)"
                className="badgeValue"
                style={{
                  padding: '6px 12px',
                  borderRadius: '20px',
                  border: '1px solid #334155',
                  backgroundColor: 'rgba(15, 23, 42, 0.6)',
                  color: '#f8fafc',
                  fontSize: '13px',
                  marginLeft: '10px',
                  width: '210px',
                  outline: 'none',
                }}
              />
            </div>

            <div className="messages" style={{ height: '500px', overflow: 'auto' }}>
              {messages.map((m) => {
                const isUser = m.role === 'user';
                const isImage = m.type === 'image' && Boolean(m.imageData);

                return (
                  <div key={m.id} className={isUser ? 'userRow' : 'assistantRow'}>
                    {!isUser && <div className="assistantAvatar" aria-hidden="true">⚡</div>}
                    <div className={isUser ? 'userBubble' : 'assistantBubble'}>
                      {isImage ? (
                        <div style={{ margin: '8px 0', padding: '14px', background: '#0f172a', borderRadius: '16px', border: '1px solid #38bdf8' }}>
                          <span style={{ fontSize: '13px', fontWeight: 800, color: '#38bdf8' }}>🎨 NITRO GRAPHIC STUDIO</span>
                          <img src={m.imageData} alt={m.prompt} style={{ width: '100%', maxHeight: '400px', objectFit: 'contain', marginTop: '10px', borderRadius: '8px' }} />
                        </div>
                      ) : (
                        <div style={{ whiteSpace: 'pre-wrap' }}>{m.text}</div>
                      )}
                    </div>
                    {isUser && <div className="userAvatar" aria-hidden="true">🙂</div>}
                  </div>
                );
              })}

              {thinking && (
                <div className="assistantRow">
                  <div className="assistantAvatar" aria-hidden="true">⚡</div>
                  <div className="assistantBubble">
                    <div className="typing">
                      <span /><span /><span />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {error && <div className="error-pill" style={{ margin: '10px' }}>{error}</div>}
          </div>

          <div className="aiInputDock">
            <div className="aiInputShell">
              <textarea
                className="aiInputText"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage(inputValue);
                  }
                }}
                placeholder="Ask Nitro AI (e.g., 'solve 2x+10=30', 'make an image of a cyber lion', 'tell me a story')..."
                rows={2}
                disabled={thinking}
              />

              <button className={voiceActive ? 'voiceBtn active' : 'voiceBtn'} type="button" onClick={handleVoiceClick}>
                🎙️
              </button>

              <button
                className={inputValue.trim() && !thinking ? 'sendBtn' : 'sendBtn disabled'}
                type="button"
                onClick={() => sendMessage(inputValue)}
                disabled={!inputValue.trim() || thinking}
              >
                ⬆️
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;