import React from 'react';

function padOtp(value, length) {
  return value.slice(0, length).padEnd(length, '');
}

export default function OtpInput({ value, length = 6, onChange, disabled }) {
  const digits = padOtp(value || '', length).split('');

  function handleDigitChange(index, next) {
    if (disabled) return;
    const sanitized = next.replace(/\D/g, '').slice(0, 1);
    const updated = digits.map((digit, idx) => (idx === index ? sanitized : digit)).join('');
    onChange(updated.replace(/\s+/g, ''));
  }

  function handleKeyDown(event, index) {
    const { key } = event;
    if (key === 'Backspace' && !value[index] && index > 0) {
      const newValue = value.slice(0, index - 1) + value.slice(index);
      onChange(newValue);
    }
  }

  return (
    <div className="OtpRow">
      {digits.map((digit, index) => (
        <input
          key={index}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={1}
          value={digit}
          disabled={disabled}
          onChange={(event) => handleDigitChange(index, event.target.value)}
          onKeyDown={(event) => handleKeyDown(event, index)}
          className="OtpCell"
          autoComplete="one-time-code"
        />
      ))}
    </div>
  );
}
