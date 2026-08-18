import React, { useEffect, useMemo, useRef, useState } from 'react';
import Message from './Message';

function Chat({ messages, onSend, thinking, activeAgent, emotion, onUploadRequest, onVoiceRequest }) {
  const scrollerRef = useRef(null);
  const [atBottom, setAtBottom] = useState(true);

  useEffect(() => {
    const el = scrollerRef.current;
    if (!el) return;

    const onScroll = () => {
      const threshold = 40;
      const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
      setAtBottom(nearBottom);
    };

    el.addEventListener('scroll', onScroll);
    onScroll();
    return () => el.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    if (!atBottom) return;
    const el = scrollerRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, atBottom, thinking]);

  const banner = useMemo(() => {
    if (!thinking) return null;
    return (
      <div className="thinkingBanner" role="status" aria-live="polite">
        <div className="dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <div className="thinkingText">Nitro AI is thinking...</div>
      </div>
    );
  }, [thinking]);

  return (
    <div className="chatWrap">
      <div className="topBadges">
        <div className="badge">
          <span className="badgeLabel">Agent</span>
          <span className="badgeValue">{activeAgent || 'nitro-core'}</span>
        </div>
        <div className="badge">
          <span className="badgeLabel">Engine</span>
          <span className="badgeValue">Nitro AI</span>
        </div>
        <div className="badge">
          <span className="badgeLabel">Emotion</span>
          <span className="badgeValue">{emotion || 'neutral'}</span>
        </div>
      </div>

      <div className="messages" ref={scrollerRef}>
        {banner}
        {messages.map((m) => (
          <Message key={m.id} msg={m} />
        ))}
        {thinking && (
          <div className="assistantRow">
            <div className="assistantAvatar" aria-hidden="true">⚡</div>
            <div className="assistantBubble">
              <div className="typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="actionsRow">
        <button className="ghostBtn" type="button" onClick={onUploadRequest}>Upload</button>
        <button className="ghostBtn" type="button" onClick={onVoiceRequest}>Voice</button>
      </div>
    </div>
  );
}

export default Chat;