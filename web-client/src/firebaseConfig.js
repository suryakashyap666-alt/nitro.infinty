import { initializeApp } from 'firebase/app';
import {
  getAuth,
  signInWithPopup,
  GoogleAuthProvider,
  RecaptchaVerifier,
  signInWithPhoneNumber,
  signOut as firebaseSignOut,
  onAuthStateChanged,
} from 'firebase/auth';
import {
  getFirestore,
  collection,
  query,
  orderBy,
  getDocs,
  addDoc,
  doc,
  setDoc,
} from 'firebase/firestore';

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY || "AIzaSyCiCUguIAiT2IisYLsXis-Cmw5RIRcW8PQ",
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN || "nitro-infinty.firebaseapp.com",
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID || "nitro-infinty",
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET || "nitro-infinty.firebasestorage.app",
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID || "112848617925",
  appId: process.env.REACT_APP_FIREBASE_APP_ID || "1:112848617925:web:14a53b955d4bdff77ccbac",
  measurementId: process.env.REACT_APP_FIREBASE_MEASUREMENT_ID || "G-0068VVVDBK",
};

export const firebaseEnabled = Boolean(
  firebaseConfig.apiKey &&
  firebaseConfig.projectId &&
  firebaseConfig.appId
);

const firebaseApp = firebaseEnabled ? initializeApp(firebaseConfig) : null;
export const auth = firebaseEnabled ? getAuth(firebaseApp) : null;
export const db = firebaseEnabled ? getFirestore(firebaseApp) : null;

export const googleProvider = firebaseEnabled ? new GoogleAuthProvider() : null;
if (googleProvider) {
  googleProvider.setCustomParameters({ prompt: 'select_account' });
}

export async function signInWithGooglePopup() {
  if (!firebaseEnabled || !auth || !googleProvider) {
    throw new Error('Firebase is not configured for Google login.');
  }
  return signInWithPopup(auth, googleProvider);
}

export function initRecaptcha(containerId = 'recaptcha-container') {
  if (!firebaseEnabled || !auth) {
    throw new Error('Firebase is not configured for phone login.');
  }
  if (!window.__nitro_recaptcha) {
    window.__nitro_recaptcha = new RecaptchaVerifier(containerId, {
      size: 'invisible',
      badge: 'bottomleft',
    }, auth);
    window.__nitro_recaptcha.render().catch(() => {});
  }
  return window.__nitro_recaptcha;
}

export async function sendPhoneCode(phoneNumber) {
  const verifier = initRecaptcha();
  return signInWithPhoneNumber(auth, phoneNumber, verifier);
}

export function verifyPhoneCode(confirmationResult, code) {
  return confirmationResult.confirm(code);
}

export function observeAuthState(callback) {
  if (!firebaseEnabled || !auth) {
    return () => {};
  }
  return onAuthStateChanged(auth, callback);
}

export async function signOutFirebase() {
  if (firebaseEnabled && auth) {
    await firebaseSignOut(auth);
  }
}

export async function saveUserProfile(uid, profile) {
  if (!db || !uid) return;
  const userRef = doc(db, 'users', uid);
  await setDoc(userRef, { ...profile, uid }, { merge: true });
}

export async function saveChatEvent(uid, event) {
  if (!db || !uid) return;
  const historyRef = collection(db, 'users', uid, 'history');
  await addDoc(historyRef, {
    ...event,
    ts: event.ts || new Date().toISOString(),
  });
}

export async function loadUserHistory(uid) {
  if (!db || !uid) return [];
  const historyRef = collection(db, 'users', uid, 'history');
  const historyQuery = query(historyRef, orderBy('ts', 'asc'));
  const snapshot = await getDocs(historyQuery);
  return snapshot.docs.map((docSnap) => ({ id: docSnap.id, ...docSnap.data() }));
}