import React, { useRef } from 'react';

export default function FileUpload({ onFile }) {
  const ref = useRef(null);

  return (
    <div className="uploadRow">
      <input
        ref={ref}
        type="file"
        accept=".txt,.md,.pdf,image/*,.png,.jpg,.jpeg,.webp"
        style={{ display: 'none' }}
        onChange={(e) => {
          const f = e.target.files && e.target.files[0];
          if (f) onFile(f);
        }}
      />
      <button className="ghostBtn" type="button" onClick={() => ref.current && ref.current.click()}>
        Upload file/image
      </button>
    </div>
  );
}

