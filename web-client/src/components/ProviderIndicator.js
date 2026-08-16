import React from 'react';

export default function ProviderIndicator({ provider }) {
  return (
    <div className="miniIndicator">
      <span className="miniLabel">Provider</span>
      <span className="miniValue">{provider || 'nitro'}</span>
    </div>
  );
}

