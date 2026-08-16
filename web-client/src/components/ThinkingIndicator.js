import React from 'react';

export default function ThinkingIndicator({ active }) {
  if (!active) return null;
  return (
    <div className="thinkingIndicator" role="status" aria-live="polite">
      <span className="thinkingDot" />
      <span className="thinkingDot" />
      <span className="thinkingDot" />
      <span className="thinkingLabel">AI is thinking...</span>
    </div>
  );
}

