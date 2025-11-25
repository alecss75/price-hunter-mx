// Fill with your Firebase project config. You can copy these
// from Firebase Console → Project Settings → Your apps → Web app.
// Using placeholders to avoid committing secrets.
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getAnalytics } from "firebase/analytics";

export const firebaseConfig = {
  apiKey: "AIzaSyB387wI8oyG8LZIy6TKncstyRXIWem5qCY",
  authDomain: "price-hunter-mx.firebaseapp.com",
  projectId: "price-hunter-mx",
  storageBucket: "price-hunter-mx.firebasestorage.app",
  messagingSenderId: "328281360376",
  appId: "1:328281360376:web:d95824b4499503db7ef80d",
  measurementId: "G-REY01D9GP4"
};

export const firebaseApp = initializeApp(firebaseConfig);
export const firebaseAuth = getAuth(firebaseApp);
export const firebaseDb = getFirestore(firebaseApp);
const analytics = getAnalytics(firebaseApp);
