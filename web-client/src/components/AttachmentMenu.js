import React from 'react';

export default function AttachmentMenu({ onPick, onClose }) {
  return (
    <div className="attachMenu" role="menu">
      <button className="attachItem" type="button" onClick={() => onPick('file')} role="menuitem">
        📄 file
      </button>
      <button className="attachItem" type="button" onClick={() => onPick('photo')} role="menuitem">
        🖼️ photo
      </button>
      <button className="attachItem" type="button" onClick={() => onPick('video')} role="menuitem">
        🎥 video
      </button>
      <button className="attachItem" type="button" onClick={() => onPick('link')} role="menuitem">
        🔗 link
      </button>
      {onClose ? (
        <button className="attachClose" type="button" onClick={onClose}>
          Close
        </button>
      ) : null}
    </div>
  );
}

