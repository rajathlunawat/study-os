import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyAsoPMXy4RSUijTQQ30giKJGLivS9oln0k",
  authDomain: "studyos-1dd61.firebaseapp.com",
  projectId: "studyos-1dd61",
  storageBucket: "studyos-1dd61.firebasestorage.app",
  messagingSenderId: "452077757764",
  appId: "1:452077757764:web:e7d18c0fbc856c231ba311",
  measurementId: "G-T3CTYC3QZ5"
};

const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

export { auth, googleProvider };
