// Lightweight multilingual STT/TTS using browser Web Speech APIs.
// No heavy deps.

const getSpeechRecognition = () => {
  const w = typeof window !== 'undefined' ? window : undefined;
  if (!w) return null;
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
};

const safeSupported = () => {
  const Rec = getSpeechRecognition();
  const ttsOk = typeof window !== 'undefined' && window.speechSynthesis && window.SpeechSynthesisUtterance;
  return Boolean(Rec) && ttsOk;
};

const stripToReasonable = (s) => (s || '').replace(/\s+/g, ' ').trim().slice(0, 2000);

// Minimal language hints based on unicode.
// Must align with backend heuristics loosely.
const detectLangFromText = (text) => {
  const t = (text || '').trim();
  if (!t) return 'en';

  if (/[\u3040-\u309F\u30A0-\u30FF]/.test(t)) return 'ja';
  if (/[\u4E00-\u9FFF]/.test(t)) return 'zh';
  if (/[\u0600-\u06FF]/.test(t)) {
    const low = t.toLowerCase();
    if (["اور", "کیسے", "کتنا", "خوش", "براہ"].some((w) => low.includes(w))) return 'ur';
    return 'ar';
  }
  if (/[\u0400-\u04FF]/.test(t)) return 'ru';
  if (/[\u0900-\u097F]/.test(t)) return 'hi';
  if (/[\u0980-\u09FF]/.test(t)) return 'bn';
  if (/[\u0B80-\u0BFF]/.test(t)) return 'ta';
  if (/[\u0C00-\u0C7F]/.test(t)) return 'te';

  const low = t.toLowerCase();
  if (["hola", "gracias", "por favor"].some((w) => low.includes(w))) return 'es';
  if (["bonjour", "merci", "s\u2019il vous plait", "s\u2019il vous plaît"].some((w) => low.includes(w))) return 'fr';
  if (["hallo", "danke", "bitte"].some((w) => low.includes(w))) return 'de';
  if (["ol\u00e1", "obrigado", "por favor"].some((w) => low.includes(w))) return 'pt';
  if (["merhaba", "te\u015fekk\u00fcr", "l\u00fctfen"].some((w) => low.includes(w))) return 'tr';
  if (["ciao", "grazie", "per favore"].some((w) => low.includes(w))) return 'it';

  return 'en';
};

// SpeechRecognition languages (BROWSER will ignore if unsupported)
const speechRecognitionLangMap = {
  en: 'en-US',
  hi: 'hi-IN',
  ja: 'ja-JP',
  ar: 'ar-SA',
  ur: 'ur-PK',
  es: 'es-ES',
  fr: 'fr-FR',
  zh: 'zh-CN',
  ru: 'ru-RU',
  bn: 'bn-BD',
  ta: 'ta-IN',
  te: 'te-IN',
};

const pickTtsVoice = (preferredLangCode) => {
  try {
    const synth = window.speechSynthesis;
    const voices = synth.getVoices ? synth.getVoices() : [];
    if (!voices || !voices.length) return null;

    // First try: exact lang match prefix
    const lc = (preferredLangCode || 'en').toLowerCase();
    const want = speechRecognitionLangMap[lc] || speechRecognitionLangMap[lc.slice(0, 2)] || null;

    if (want) {
      const v = voices.find((x) => (x.lang || '').toLowerCase() === want.toLowerCase());
      if (v) return v;
    }

    // Next try: startsWith match
    const v2 = voices.find((x) => (x.lang || '').toLowerCase().startsWith((want || '').toLowerCase()));
    if (v2) return v2;

    // Fallback: by language prefix of code
    const v3 = voices.find((x) => (x.lang || '').toLowerCase().startsWith(lc));
    return v3 || voices[0];
  } catch {
    return null;
  }
};

export function canUseVoice() {
  return safeSupported();
}

export function createSttController() {
  const Rec = getSpeechRecognition();
  if (!Rec) return null;

  const recognition = new Rec();
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.maxAlternatives = 1;

  return recognition;
}

export function startSpeechToText({
  onTranscript,
  onFinal,
  onError,
  languageHint,
} = {}) {
  const recognition = createSttController();
  if (!recognition) {
    onError?.(new Error('SpeechRecognition not supported'));
    return { stop: () => {} };
  }

  try {
    const hint = languageHint || 'en';
    recognition.lang = speechRecognitionLangMap[hint] || 'en-US';
  } catch {
    // ignore
  }

  recognition.onresult = (event) => {
    try {
      let interim = '';
      let finalText = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const res = event.results[i];
        const text = res[0]?.transcript || '';
        if (res.isFinal) finalText += text;
        else interim += text;
      }

      const cleanInterim = stripToReasonable(interim);
      if (cleanInterim) onTranscript?.(cleanInterim);

      const cleanFinal = stripToReasonable(finalText);
      if (cleanFinal) onFinal?.(cleanFinal);
    } catch (e) {
      onError?.(e);
    }
  };

  recognition.onerror = (e) => {
    onError?.(e);
  };

  recognition.onend = () => {
    // no-op. Final callback should have fired.
  };

  recognition.start();

  return {
    stop: () => {
      try {
        recognition.stop();
      } catch {
        // ignore
      }
    },
  };
}

const _playAudioBlob = (blob, rate = 1.0) => {
  try {
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.preload = 'auto';
    audio.playbackRate = rate || 1.0;
    audio.onended = () => URL.revokeObjectURL(url);
    audio.onerror = () => URL.revokeObjectURL(url);
    audio.play().catch(() => {
      URL.revokeObjectURL(url);
    });
    return true;
  } catch {
    return false;
  }
};

const _fetchNitroVoiceAudio = async (text, languageHint) => {
  try {
    const res = await fetch('/voice/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language: languageHint || 'en' }),
    });

    if (!res.ok || res.status === 204) {
      return null;
    }

    const arrayBuffer = await res.arrayBuffer();
    if (!arrayBuffer || !arrayBuffer.byteLength) {
      return null;
    }

    return new Blob([arrayBuffer], { type: 'audio/wav' });
  } catch {
    return null;
  }
};

const _speakBrowser = ({ text, languageHint, rate, pitch }) => {
  try {
    if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) return false;

    // Stop current speech
    try {
      window.speechSynthesis.cancel();
    } catch {
      // ignore
    }

    const utter = new window.SpeechSynthesisUtterance(text);
    const langCode = languageHint || detectLangFromText(text);
    const v = pickTtsVoice(langCode);
    if (v) {
      utter.voice = v;
      utter.lang = v.lang;
    }

    utter.rate = rate;
    utter.pitch = pitch;

    window.speechSynthesis.speak(utter);
    return true;
  } catch {
    return false;
  }
};

export async function speakText({
  text,
  languageHint,
  rate = 1.0,
  pitch = 1.0,
} = {}) {
  const msg = stripToReasonable(text);
  if (!msg) return false;

  const voiceLang = languageHint || detectLangFromText(msg);
  const audioBlob = await _fetchNitroVoiceAudio(msg, voiceLang);
  if (audioBlob) {
    return _playAudioBlob(audioBlob, rate);
  }

  return _speakBrowser({ text: msg, languageHint: voiceLang, rate, pitch });
}

export function detectLanguageHint(text) {
  return detectLangFromText(text);
}

