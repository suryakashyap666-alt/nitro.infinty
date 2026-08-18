import React from 'react';

export default function ProviderIndicator({ agent }) {
  return (
    <div className="miniIndicator">
      <span className="miniLabel">Engine</span>
      <span className="miniValue">Nitro AI {agent ? `• ${agent}` : ''}</span>
    </div>
  );
}