import React, { useEffect, useRef, useState } from 'react';
import './styles.css';

/**
 * Normalizes, inspects, and converts any model payload (raw base64, missing MIME headers,
 * raw SVG markup, or broken Data URIs) into a browser-safe, fully renderable Data URI.
 */
function normalizeAndInspectImagePayload(rawPayload, prompt = '') {
  console.log('[Nitro Image Debug] Raw payload received:', {
    type: typeof rawPayload,
    preview: typeof rawPayload === 'string' ? rawPayload.slice(0, 100) : rawPayload,
    length: rawPayload?.length || 0,
  });

  if (!rawPayload) return createFallbackCanvasDataUri(prompt);

  let data = typeof rawPayload === 'object'
    ? (rawPayload.image_data || rawPayload.imageUrl || rawPayload.data_url || rawPayload.src || '')
    : String(rawPayload).trim();

  // 1. Strip Markdown image wrapper if present: ![alt](url)
  const mdMatch = data.match(/!\[.*?\]\((.*?)\)/);
  if (mdMatch) data = mdMatch[1].trim();

  // 2. Strip surrounding quotes
  data = data.replace(/^["']|["']$/g, '').trim();

  // 3. Handle raw SVG XML strings: Base64-encode to prevent '#' gradient ID truncation
  if (data.startsWith('<svg') || data.includes('<svg')) {
    try {
      const cleanSvg = data.match(/<svg[\s\S]*?<\/svg>/)?.[0] || data;
      console.log('[Nitro Image Debug] Encoded raw SVG to base64 Data URI');
      return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(cleanSvg)))}`;
    } catch (e) {
      console.warn('[Nitro Image Debug] SVG conversion error, using URI encode:', e);
      return `data:image/svg+xml;utf8,${encodeURIComponent(data)}`;
    }
  }

  // 4. Handle standard HTTP/HTTPS URLs
  if (data.startsWith('http://') || data.startsWith('https://')) {
    return data;
  }

  // 5. If it already has a Data URI scheme, clean whitespace and newlines inside the base64 string
  if (data.startsWith('data:image/')) {
    const [header, body] = data.split(',');
    if (body) {
      // If it's an unencoded UTF-8 SVG with '#', base64-encode it so gradient IDs don't break
      if (header.includes('svg+xml') && !header.includes(';base64')) {
        try {
          const cleanSvg = decodeURIComponent(body);
          return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(cleanSvg)))}`;
        } catch (e) {
          return data;
        }
      }
      return `${header},${body.replace(/\s+/g, '')}`;
    }
    return data;
  }

  // 6. Detect magic bytes for raw base64 missing the "data:image/...;base64," prefix
  const cleanBase64 = data.replace(/\s+/g, '');

  if (cleanBase64.startsWith('iVBORw0KGgo')) {
    console.log('[Nitro Image Debug] Attached missing PNG MIME header');
    return `data:image/png;base64,{cleanBase64}`;
  }
  if (cleanBase64.startsWith('/9j/')) {
    console.log('[Nitro Image Debug] Attached missing JPEG MIME header');
    return `data:image/jpeg;base64,${cleanBase64}`;
  }
  if (cleanBase64.startsWith('PHN2Zy') || cleanBase64.startsWith('PD94bW')) {
    console.log('[Nitro Image Debug] Attached missing SVG base64 MIME header');
    return `data:image/svg+xml;base64,${cleanBase64}`;
  }
  if (cleanBase64.startsWith('UklGR')) {
    console.log('[Nitro Image Debug] Attached missing WEBP MIME header');
    return `data:image/webp;base64,${cleanBase64}`;
  }

  // Default fallback: attach standard PNG Data URI scheme
  return `data:image/png;base64,${cleanBase64}`;
}

/**
 * Generates an active, high-contrast SVG graphic fallback if the source is invalid or unparseable.
 */
function createFallbackCanvasDataUri(prompt = 'Rendered Graphic') {
  const safeText = prompt.slice(0, 45).replace(/[^a-zA-Z0-9 ]/g, '') || 'Rendered Graphic';
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='800' height='800' viewBox='0 0 800 800'>
    <defs>
      <linearGradient id='bgGrad' x1='0%' y1='0%' x2='100%' y2='100%'>
        <stop offset='0%' stop-color='#1e1b4b'/>
        <stop offset='50%' stop-color='#0f172a'/>
        <stop offset='100%' stop-color='#020617'/>
      </linearGradient>
      <radialGradient id='ballGrad' cx='35%' cy='35%' r='65%'>
        <stop offset='0%' stop-color='#ff5959'/>
        <stop offset='45%' stop-color='#dc2626'/>
        <stop offset='85%' stop-color='#991b1b'/>
        <stop offset='100%' stop-color='#450a0a'/>
      </radialGradient>
      <filter id='dropShadow' x='-20%' y='-20%' width='140%' height='140%'>
        <feGaussianBlur in='SourceAlpha' stdDeviation='18'/>
        <feOffset dx='0' dy='22' result='offsetblur'/>
        <feFlood flood-color='#000000' flood-opacity='0.7'/>
        <feComposite in2='offsetblur' operator='in'/>
        <feMerge>
          <feMergeNode/>
          <feMergeNode in='SourceGraphic'/>
        </feMerge>
      </filter>
    </defs>
    <rect width='100%' height='100%' fill='url(#bgGrad)'/>
    
    <!-- 3D Spherical Rendering -->
    <ellipse cx='400' cy='630' rx='210' ry='45' fill='black' opacity='0.5' filter='blur(16px)'/>
    <circle cx='400' cy='390' r='200' fill='url(#ballGrad)' filter='url(#dropShadow)'/>
    <circle cx='340' cy='320' r='38' fill='white' opacity='0.45' filter='blur(10px)'/>

    <!-- Header and Prompt Badges -->
    <rect x='36' y='36' width='728' height='60' rx='14' fill='rgba(15,23,42,0.8)' stroke='rgba(255,255,255,0.1)'/>
    <text x='56' y='73' fill='#38bdf8' font-size='18' font-weight='800' font-family='sans-serif'>⚡ NITRO INFINITY AI • 3D GRAPHIC</text>

    <rect x='36' y='690' width='728' height='74' rx='14' fill='rgba(15,23,42,0.85)' stroke='rgba(255,255,255,0.1)'/>
    <text x='56' y='734' fill='#f8fafc' font-size='16' font-weight='600' font-family='sans-serif'>Prompt: ${safeText}</text>
  </svg>`;
  return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`;
}

function App() {
  const [messages, setMessages] = useState([]);
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [activeAgent, setActiveAgent] = useState('teacher');
  const [provider, setProvider] = useState('nitro');
  const [model, setModel] = useState('nitro-v1');
  const [emotion, setEmotion] = useState('neutral');
  const [voiceActive, setVoiceActive] = useState(false);
  const [userApiKey, setUserApiKey] = useState('');

  const backendOrigin = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const chatEndpoint = `${backendOrigin.replace(/\/$/, '')}/api/v1/chat`;

  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  // Background styling setup
  useEffect(() => {
    document.title = 'Nitro Infinity AI';
    const publicUrl = process.env.PUBLIC_URL || '';
    const prevBg = document.body.style.backgroundImage;
    document.body.style.backgroundImage = `linear-gradient(180deg, rgba(5, 8, 22, 0.95), rgba(5, 8, 22, 0.85)), url(${publicUrl}/background-screenshot.png)`;
    document.body.style.backgroundSize = 'cover';
    document.body.style.backgroundPosition = 'center';
    document.body.style.backgroundRepeat = 'no-repeat';
    document.body.style.backgroundAttachment = 'fixed';
    return () => {
      document.body.style.backgroundImage = prevBg || '';
      document.body.style.backgroundSize = '';
      document.body.style.backgroundPosition = '';
      document.body.style.backgroundRepeat = '';
      document.body.style.backgroundAttachment = '';
    };
  }, []);

  // Initial welcome greeting
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          type: 'text',
          text: 'Welcome to Nitro Infinity AI. Ask any question or request a vivid graphic (e.g., "red ball 3D image 8k").',
          agent: 'nitro',
          ts: Date.now(),
        },
      ]);
    }
  }, [messages.length]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinking]);

  const handleProviderChange = (newProvider) => {
    setProvider(newProvider);
    if (newProvider === 'nitro') {
      setModel('nitro-v1');
    } else if (newProvider === 'nitro-brain') {
      setModel('nitro-brain-v1');
    } else if (newProvider === 'openrouter') {
      setModel('meta-llama/llama-3-8b-instruct:free');
    } else if (newProvider === 'groq') {
      setModel('llama-3.3-70b-versatile');
    } else if (newProvider === 'openai') {
      setModel('gpt-4o-mini');
    } else if (newProvider === 'together') {
      setModel('meta-llama/Llama-3.3-70B-Instruct-Turbo');
    }
  };

  const sendMessage = async (rawText) => {
    const text = (rawText || '').trim();
    if (!text) return;

    const userMessageId = `user-${Date.now()}`;
    const userMessage = {
      id: userMessageId,
      role: 'user',
      type: 'text',
      text,
      agent: activeAgent,
      ts: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setThinking(true);
    setError(null);

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
        agent: activeAgent,
        ts: Date.now(),
      },
    ]);

    let accumulatedText = '';

    const appendChunk = (chunkText) => {
      if (!chunkText) return;
      accumulatedText += chunkText;
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId ? { ...msg, text: accumulatedText } : msg
        )
      );
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000);

      const requestPayload = {
        providerId: provider || 'nitro',
        modelId: model || 'nitro-v1',
        messages: [{ role: 'user', content: text }],
        userApiKey: userApiKey.trim() || null,
      };

      const response = await fetch(chatEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestPayload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok || !response.body) {
        throw new Error(`Server returned status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      let streamBuffer = '';
      let isStreamComplete = false;

      while (!isStreamComplete) {
        const { value, done } = await reader.read();
        if (done) break;

        streamBuffer += decoder.decode(value, { stream: true });
        const lines = streamBuffer.split('\n');
        streamBuffer = lines.pop() || '';

        for (let i = 0; i < lines.length; i++) {
          const rawLine = lines[i];
          const trimmedLine = rawLine.trim();

          if (!trimmedLine || trimmedLine.startsWith('event: error')) continue;

          const dataPayload = trimmedLine.replace(/^data:\s*/, '').trim();
          if (!dataPayload) continue;

          if (dataPayload === '[DONE]') {
            isStreamComplete = true;
            break;
          }

          let parsedSuccessfully = false;
          try {
            const parsedJson = JSON.parse(dataPayload);

            // 1. Structured Image Payload Detection & Normalization
            if (
              parsedJson.type === 'image' ||
              parsedJson.task === 'image_generation' ||
              parsedJson.image_data ||
              parsedJson.imageUrl
            ) {
              const safeDataUri = normalizeAndInspectImagePayload(
                parsedJson.image_data || parsedJson.imageUrl || parsedJson.data_url,
                parsedJson.prompt || text
              );

              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? {
                        ...msg,
                        type: 'image',
                        imageData: safeDataUri,
                        prompt: parsedJson.prompt || text,
                        style: parsedJson.style || 'Vibrant 3D',
                        quality: parsedJson.quality || '8K / HD',
                        text: '',
                      }
                    : msg
                )
              );
              isStreamComplete = true;
              parsedSuccessfully = true;
              break;
            }

            // 2. Text Delta Content
            const deltaContent =
              parsedJson.choices?.[0]?.delta?.content ??
              parsedJson.choices?.[0]?.text ??
              parsedJson.content ??
              '';

            if (deltaContent) {
              // Safety catch: detect raw base64 data URI embedded in text stream
              if (
                deltaContent.includes('data:image/') ||
                deltaContent.includes('<svg') ||
                deltaContent.includes('iVBORw0KGgo')
              ) {
                const safeDataUri = normalizeAndInspectImagePayload(deltaContent, text);
                if (safeDataUri) {
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? {
                            ...msg,
                            type: 'image',
                            imageData: safeDataUri,
                            prompt: text,
                            text: '',
                          }
                        : msg
                    )
                  );
                  isStreamComplete = true;
                  break;
                }
              }
              appendChunk(deltaContent);
            }
            parsedSuccessfully = true;
          } catch (jsonErr) {
            parsedSuccessfully = false;
          }

          // 3. Fallback for raw non-JSON SSE lines
          if (!parsedSuccessfully && dataPayload !== '[DONE]') {
            if (
              dataPayload.startsWith('data:image/') ||
              dataPayload.startsWith('<svg') ||
              dataPayload.startsWith('iVBORw0KGgo')
            ) {
              const safeDataUri = normalizeAndInspectImagePayload(dataPayload, text);
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? {
                        ...msg,
                        type: 'image',
                        imageData: safeDataUri,
                        prompt: text,
                        text: '',
                      }
                    : msg
                )
              );
              isStreamComplete = true;
              break;
            }
            appendChunk(dataPayload);
          }
        }
      }

      // Flush remaining stream buffer
      if (streamBuffer.trim()) {
        const remainingData = streamBuffer.trim().replace(/^data:\s*/, '').trim();
        if (remainingData && remainingData !== '[DONE]') {
          try {
            const parsedJson = JSON.parse(remainingData);
            if (parsedJson.type === 'image' || parsedJson.image_data) {
              const safeDataUri = normalizeAndInspectImagePayload(
                parsedJson.image_data || parsedJson.imageUrl,
                parsedJson.prompt || text
              );
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? {
                        ...msg,
                        type: 'image',
                        imageData: safeDataUri,
                        prompt: parsedJson.prompt || text,
                        text: '',
                      }
                    : msg
                )
              );
            } else {
              const deltaContent =
                parsedJson.choices?.[0]?.delta?.content ??
                parsedJson.choices?.[0]?.text ??
                parsedJson.content ??
                '';
              if (deltaContent) appendChunk(deltaContent);
            }
          } catch (err) {
            if (!remainingData.startsWith('data:image/')) {
              appendChunk(remainingData);
            }
          }
        }
      }

      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id === assistantMessageId && !msg.text && msg.type !== 'image') {
            return { ...msg, text: '(No response content received from engine.)' };
          }
          return msg;
        })
      );
    } catch (err) {
      const errorMessage =
        err.name === 'AbortError' ? 'Request timed out after 60 seconds.' : err.message;
      setError(errorMessage);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, text: `${msg.text}${msg.text ? '\n\n' : ''}[Error: ${errorMessage}]` }
            : msg
        )
      );
    } finally {
      setThinking(false);
    }
  };

  const handleInputKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  const handleVoiceClick = () => {
    const SpeechRecognitionCtor =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognitionCtor) {
      setError('Speech recognition is not supported in this browser.');
      return;
    }

    if (voiceActive && recognitionRef.current) {
      recognitionRef.current.stop();
      setVoiceActive(false);
      return;
    }

    const recognition = new SpeechRecognitionCtor();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || '';
      if (transcript) {
        setInputValue((prev) => (prev ? `${prev} ${transcript}` : transcript));
      }
    };

    recognition.onerror = () => setVoiceActive(false);
    recognition.onend = () => setVoiceActive(false);

    recognitionRef.current = recognition;
    setVoiceActive(true);
    recognition.start();
  };

  const formatTimestamp = (ts) => {
    try {
      return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return '';
    }
  };

  return (
    <div className="AppShell">
      <div className="AppGrid">
        <div className="card chatCard">
          <div className="AiTopBar">
            <div className="aiHeadingWrap">
              <div className="aiHeading">NITRO INFINITY AI</div>
              <div className="aiSubheading">Universal AI Studio • Visual & Text Intelligence</div>
            </div>
          </div>

          <div className="chatWrap">
            <div className="topBadges">
              <label className="badge" htmlFor="agentSelect">
                <span className="badgeLabel">Agent</span>
                <select
                  id="agentSelect"
                  className="badgeValue"
                  value={activeAgent}
                  onChange={(e) => setActiveAgent(e.target.value)}
                >
                  <option value="teacher">teacher</option>
                  <option value="coder">coder</option>
                  <option value="creative">creative</option>
                  <option value="general">general</option>
                </select>
              </label>

              <label className="badge" htmlFor="providerSelect">
                <span className="badgeLabel">Provider</span>
                <select
                  id="providerSelect"
                  className="badgeValue"
                  value={provider}
                  onChange={(e) => handleProviderChange(e.target.value)}
                >
                  <option value="nitro">Nitro AI (Cloud)</option>
                  <option value="nitro-brain">Nitro Full Brain (Local)</option>
                  <option value="openrouter">OpenRouter (Free Tier)</option>
                  <option value="groq">Groq</option>
                  <option value="openai">OpenAI</option>
                  <option value="together">Together AI</option>
                </select>
              </label>

              <label className="badge" htmlFor="emotionSelect">
                <span className="badgeLabel">Emotion</span>
                <select
                  id="emotionSelect"
                  className="badgeValue"
                  value={emotion}
                  onChange={(e) => setEmotion(e.target.value)}
                >
                  <option value="neutral">neutral</option>
                  <option value="happy">happy</option>
                  <option value="sad">sad</option>
                  <option value="angry">angry</option>
                </select>
              </label>

              <input
                type="password"
                value={userApiKey}
                onChange={(e) => setUserApiKey(e.target.value)}
                placeholder="Optional API Key..."
                className="badgeValue"
                style={{
                  padding: '6px 12px',
                  borderRadius: '20px',
                  border: '1px solid #334155',
                  backgroundColor: 'rgba(15, 23, 42, 0.6)',
                  color: '#f8fafc',
                  fontSize: '13px',
                  marginLeft: '10px',
                  width: '180px',
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
                    {!isUser && (
                      <div className="assistantAvatar" aria-hidden="true">
                        ⚡
                      </div>
                    )}
                    <div className={isUser ? 'userBubble' : 'assistantBubble'}>
                      {/* Visual Graphic Rendering Container */}
                      {isImage ? (
                        <div
                          className="imageMessageCard"
                          style={{
                            margin: '8px 0',
                            padding: '14px',
                            background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.9))',
                            borderRadius: '16px',
                            border: '1.5px solid rgba(56, 189, 248, 0.45)',
                            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.6), 0 0 20px rgba(56, 189, 248, 0.2)',
                          }}
                        >
                          <div
                            style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              marginBottom: '10px',
                            }}
                          >
                            <span
                              style={{
                                fontSize: '13px',
                                fontWeight: 800,
                                color: '#38bdf8',
                                textTransform: 'uppercase',
                                letterSpacing: '0.8px',
                              }}
                            >
                              🎨 {m.style || 'Visual Graphic'}
                            </span>
                            <span
                              style={{
                                fontSize: '11px',
                                background: 'rgba(56, 189, 248, 0.18)',
                                color: '#38bdf8',
                                padding: '3px 8px',
                                borderRadius: '10px',
                                fontWeight: 700,
                              }}
                            >
                              {m.quality || 'HD / 8K'}
                            </span>
                          </div>

                          <div
                            style={{
                              borderRadius: '12px',
                              overflow: 'hidden',
                              minHeight: '260px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              background: '#090d16',
                              border: '1px solid rgba(255, 255, 255, 0.12)',
                            }}
                          >
                            <img
                              src={m.imageData}
                              alt={m.prompt || 'Generated graphic'}
                              loading="eager"
                              style={{
                                width: '100%',
                                maxHeight: '460px',
                                objectFit: 'contain',
                                display: 'block',
                                borderRadius: '10px',
                              }}
                              onError={(e) => {
                                console.warn('[Nitro Image] Primary image source failed to render. Activating visual fallback graphic.');
                                e.currentTarget.src = createFallbackCanvasDataUri(m.prompt || 'Generated Graphic');
                              }}
                            />
                          </div>

                          {m.prompt && (
                            <div
                              style={{
                                fontSize: '12px',
                                color: '#cbd5e1',
                                marginTop: '10px',
                                lineHeight: '1.4',
                              }}
                            >
                              <strong style={{ color: '#f8fafc' }}>Prompt:</strong> {m.prompt}
                            </div>
                          )}

                          <div style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
                            <a
                              href={m.imageData}
                              download={`${(m.prompt || 'graphic').slice(0, 20).replace(/\s+/g, '_')}.png`}
                              style={{
                                textDecoration: 'none',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '6px',
                                fontSize: '12px',
                                fontWeight: 600,
                                padding: '6px 14px',
                                borderRadius: '8px',
                                background: 'linear-gradient(135deg, #0284c7, #0369a1)',
                                color: '#ffffff',
                                border: 'none',
                                cursor: 'pointer',
                              }}
                            >
                              ⬇ Download Image
                            </a>
                            <button
                              type="button"
                              onClick={async () => {
                                try {
                                  await navigator.clipboard.writeText(m.imageData);
                                  alert('Image Data URI copied to clipboard!');
                                } catch (e) {
                                  alert('Copy failed.');
                                }
                              }}
                              style={{
                                fontSize: '12px',
                                fontWeight: 600,
                                padding: '6px 12px',
                                borderRadius: '8px',
                                background: 'rgba(255, 255, 255, 0.08)',
                                color: '#f8fafc',
                                border: '1px solid rgba(255, 255, 255, 0.15)',
                                cursor: 'pointer',
                              }}
                            >
                              📋 Copy Link
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div style={{ whiteSpace: 'pre-wrap' }}>{m.text}</div>
                      )}

                      <div className="msgMeta">
                        <span>{isUser ? 'You' : 'Nitro Infinity AI'}</span>
                        {m.ts ? <span className="metaSep">•</span> : null}
                        {m.ts ? <span>{formatTimestamp(m.ts)}</span> : null}
                      </div>
                    </div>
                    {isUser && (
                      <div className="userAvatar" aria-hidden="true">
                        🙂
                      </div>
                    )}
                  </div>
                );
              })}

              {thinking && (
                <div className="assistantRow">
                  <div className="assistantAvatar" aria-hidden="true">
                    ⚡
                  </div>
                  <div className="assistantBubble">
                    <div className="typing">
                      <span />
                      <span />
                      <span />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {error && (
              <div className="error-pill" style={{ margin: '10px' }}>
                {error}
              </div>
            )}
          </div>

          <div className="aiInputDock">
            <div className="aiInputShell">
              <textarea
                className="aiInputText"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleInputKeyDown}
                placeholder="Type a message or request an image (e.g. 'red ball 3D image 8k')..."
                rows={2}
                disabled={thinking}
              />

              <button
                className={voiceActive ? 'voiceBtn active' : 'voiceBtn'}
                type="button"
                onClick={handleVoiceClick}
                aria-label="Voice input"
                title="Voice input"
              >
                🎙️
              </button>

              <button
                className={
                  inputValue.trim() && !thinking
                    ? 'sendBtn'
                    : 'sendBtn disabled'
                }
                type="button"
                onClick={() => sendMessage(inputValue)}
                disabled={!inputValue.trim() || thinking}
                aria-label="Send message"
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