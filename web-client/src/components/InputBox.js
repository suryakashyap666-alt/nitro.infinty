import React, { useMemo, useRef, useState } from 'react';
import AttachmentMenu from './AttachmentMenu';

export default function InputBox({ onSend, disabled, onAttach }) {
  const [text, setText] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const [sendingPulse, setSendingPulse] = useState(false);
  const fileRef = useRef(null);

  const canSend = useMemo(() => text.trim().length > 0 && !disabled, [text, disabled]);

  async function handleSend() {
    if (!canSend) return;
    const payload = text;
    setText('');
    setMenuOpen(false);
    setSendingPulse(true);

    // short click effect
    setTimeout(() => setSendingPulse(false), 180);

    await onSend(payload);
  }

  function pick(kind) {
    setMenuOpen(false);
    if (onAttach) onAttach(kind);

    if ((kind === 'file' || kind === 'photo' || kind === 'video') && fileRef.current) {
      fileRef.current.click();
    }

    if (kind === 'link') {
      setText((t) => (t.trim().length ? `${t}\nlink: ` : 'link: '));
    }
  }

  return (
    <div className="aiInputShell">
      <input
        ref={fileRef}
        type="file"
        accept=".txt,.md,.pdf,image/*,.png,.jpg,.jpeg,.webp,video/*"
        style={{ display: 'none' }}
        onChange={() => {
          // Keep Nitro upload flow in App.js; UI-level attachment is handled there.
          // We only trigger the menu click behavior.
        }}
      />

      <button
        className="attachBtn"
        type="button"
        aria-label="Add attachment"
        onClick={() => setMenuOpen((v) => !v)}
      >
        ➕
      </button>

      <div className="attachSlot">
        {menuOpen ? (
          <AttachmentMenu
            onPick={pick}
            onClose={() => setMenuOpen(false)}
          />
        ) : null}
      </div>

      <textarea
        className="aiInputText"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type a message…"
        rows={2}
        disabled={disabled}
        onKeyDown={(e) => {
          // Enter to send, Shift+Enter newline
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
      />

      <button
        className={canSend ? (sendingPulse ? 'sendBtn pulse' : 'sendBtn') : 'sendBtn disabled'}
        type="button"
        onClick={handleSend}
        disabled={!canSend}
        aria-label="Send message"
      >
        ⬆️
      </button>
    </div>
  );
}

