import React, { useEffect, useMemo, useState } from 'react';
import OtpInput from './OtpInput';
import {
  firebaseEnabled,
  signInWithGooglePopup,
  sendPhoneCode,
  verifyPhoneCode,
  initRecaptcha,
} from '../firebaseConfig';

export default function LoginScreen({ onSuccess, onGuest, onSaraswati }) {
  const [stage, setStage] = useState('main');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otpValue, setOtpValue] = useState('');
  const [confirmationResult, setConfirmationResult] = useState(null);
  const [accountId, setAccountId] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (stage === 'phone' && firebaseEnabled) {
      initRecaptcha('recaptcha-container');
    }
  }, [stage]);

  const isPhoneValid = useMemo(() => phoneNumber.trim().length >= 10, [phoneNumber]);

  async function handleGoogleLogin() {
    setError('');
    setLoading(true);
    try {
      const result = await signInWithGooglePopup();
      const user = result.user;
      onSuccess({
        provider: 'google',
        uid: user.uid,
        displayName: user.displayName || 'Google User',
        email: user.email || '',
      });
    } catch (err) {
      setError(err.message || 'Google login failed.');
    } finally {
      setLoading(false);
    }
  }

  async function handleStartPhone() {
    setError('');
    if (!firebaseEnabled) {
      setError('Phone login requires Firebase configuration.');
      return;
    }
    if (!isPhoneValid) {
      setError('Enter a valid phone number with country code.');
      return;
    }
    setLoading(true);
    try {
      const result = await sendPhoneCode(phoneNumber.trim());
      setConfirmationResult(result);
      setStage('verify');
    } catch (err) {
      setError(err.message || 'Unable to send verification code.');
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp() {
    setError('');
    if (!confirmationResult) {
      setError('No OTP request is active.');
      return;
    }
    if (otpValue.length < 6) {
      setError('Enter the 6-digit code you received.');
      return;
    }
    setLoading(true);
    try {
      const result = await verifyPhoneCode(confirmationResult, otpValue);
      const user = result.user;
      onSuccess({
        provider: 'phone',
        uid: user.uid,
        displayName: user.phoneNumber || 'Phone User',
        email: user.email || '',
      });
    } catch (err) {
      setError(err.message || 'OTP verification failed.');
    } finally {
      setLoading(false);
    }
  }

  async function handleSaraswatiLogin() {
    setError('');
    if (!accountId.trim() || !password.trim()) {
      setError('Account ID and Password are required.');
      return;
    }
    setLoading(true);
    try {
      const result = await onSaraswati(accountId.trim(), password);
      onSuccess({
        provider: 'saraswati',
        uid: result.user_id,
        displayName: result.display_name || result.user_id,
        email: result.email || '',
        token: result.token || '',
      });
    } catch (err) {
      setError(err.message || 'Invalid credentials.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="LoginShell">
      <div className="LoginCard">
        <div className="LoginBrand">
          <div className="LoginLogo" aria-hidden="true" />
          <div>
            <div className="LoginTitle">Nitro Infinity AI Access</div>
            <div className="LoginSubtitle">Secure your learning, sync across devices, or chat instantly as guest.</div>
          </div>
        </div>

        {stage === 'main' && (
          <div className="LoginOptions">
            <button className="primaryBtn LoginOption" type="button" onClick={handleGoogleLogin} disabled={loading}>
              Continue with Google
            </button>
            <button className="ghostBtn LoginOption" type="button" onClick={() => setStage('phone')} disabled={loading}>
              Continue with Phone Number
            </button>
            <button className="ghostBtn LoginOption" type="button" onClick={() => setStage('saraswati')} disabled={loading}>
              Continue with Saraswati Food Delivery Account
            </button>
            <button className="ghostBtn LoginOption" type="button" onClick={onGuest} disabled={loading}>
              Continue as Guest
            </button>
            <div className="LoginHint">The login screen appears only for new users or on logout.</div>
          </div>
        )}

        {stage === 'phone' && (
          <div className="AuthPanel">
            <div className="AuthLabel">Phone Number?</div>
            <input
              className="LoginInput"
              type="tel"
              placeholder="+1 555 123 4567"
              value={phoneNumber}
              onChange={(event) => setPhoneNumber(event.target.value)}
              disabled={loading}
            />
            <button className="primaryBtn LoginAction" type="button" onClick={handleStartPhone} disabled={loading}>
              Send verification code
            </button>
            <button className="ghostBtn LoginAction" type="button" onClick={() => setStage('main')} disabled={loading}>
              Back to login options
            </button>
            <div id="recaptcha-container" />
          </div>
        )}

        {stage === 'verify' && (
          <div className="AuthPanel">
            <div className="AuthLabel">For verification it's you, put the code you got</div>
            <OtpInput value={otpValue} onChange={setOtpValue} disabled={loading} />
            <button className="primaryBtn LoginAction" type="button" onClick={handleVerifyOtp} disabled={loading}>
              Verify code and continue
            </button>
            <button className="ghostBtn LoginAction" type="button" onClick={() => setStage('phone')} disabled={loading}>
              Change phone number
            </button>
          </div>
        )}

        {stage === 'saraswati' && (
          <div className="AuthPanel">
            <div className="AuthLabel">Saraswati Food Delivery account</div>
            <input
              className="LoginInput"
              type="text"
              placeholder="Account ID"
              value={accountId}
              onChange={(event) => setAccountId(event.target.value)}
              disabled={loading}
            />
            <input
              className="LoginInput"
              type="password"
              placeholder="Password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              disabled={loading}
            />
            <button className="primaryBtn LoginAction" type="button" onClick={handleSaraswatiLogin} disabled={loading}>
              Sign in to Saraswati
            </button>
            <button className="ghostBtn LoginAction" type="button" onClick={() => setStage('main')} disabled={loading}>
              Back to login options
            </button>
          </div>
        )}

        <div className="LoginFooter">
          {error && <div className="LoginError">{error}</div>}
          {loading && <div className="LoginLoading">Loading…</div>}
        </div>
      </div>
    </div>
  );
}
