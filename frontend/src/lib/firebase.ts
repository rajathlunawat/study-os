import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyAsoPMXy4RSUijTQQ30giKJGLivS9oln0k",
  authDomain: "studyos-11a61.firebaseapp.com",
  projectId: "studyos-11a61",
  storageBucket: "studyos-11a61.appspot.com",
  messagingSenderId: "123456789", 
  appId: "1:123456789:web:123456789" 
};

const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

export { auth, googleProvider };
