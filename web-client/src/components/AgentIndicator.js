import React from 'react';

export default function AgentIndicator({ agent }) {
  return (
    <div className="miniIndicator">
      <span className="miniLabel">Agent</span>
      <span className="miniValue">{agent || 'teacher'}</span>
    </div>
  );
}

