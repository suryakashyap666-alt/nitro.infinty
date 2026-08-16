import React from 'react';

export default function ReasoningPanel({ text }) {
  if (!text) return null;
  return (
    <div className="reasonPanel">
      <div className="panelTitle">Reasoning</div>
      <pre className="reasonText">{text}</pre>
    </div>
  );
}

