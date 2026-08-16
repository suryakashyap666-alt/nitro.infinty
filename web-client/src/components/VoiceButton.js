import React from 'react';

export default function VoiceButton({ onClick, disabled }) {
  return (
    <button className="ghostBtn" type="button" disabled={disabled} onClick={onClick}>
      🎙️ Voice
    </button>
  );
}

