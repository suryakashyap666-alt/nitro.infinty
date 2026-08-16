import React from 'react';

export default function EmotionIndicator({ emotion }) {
  return (
    <div className="miniIndicator">
      <span className="miniLabel">Emotion</span>
      <span className="miniValue">{emotion || 'neutral'}</span>
    </div>
  );
}

