import React from 'react';

export default function AchievementPanel({ stats }) {
  const items = (stats && stats.items) || [];
  return (
    <div className="achPanel">
      <div className="panelTitle">Achievements</div>
      {items.length === 0 ? (
        <div className="panelEmpty">Complete streaks & coding/math practice to unlock badges.</div>
      ) : (
        <div className="achGrid">
          {items.map((it) => (
            <div className="achItem" key={it.id}>
              <div className="achIcon" aria-hidden="true">🏅</div>
              <div className="achText">
                <div className="achName">{it.name}</div>
                <div className="achDesc">{it.desc}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

