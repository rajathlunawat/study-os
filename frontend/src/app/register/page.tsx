'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { signInWithPopup } from 'firebase/auth';
import { auth, googleProvider } from '@/lib/firebase';
import styles from '../auth.module.css';

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleGoogleLogin = async () => {
    setError('');
    setIsLoading(true);
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const user = result.user;
      const token = await user.getIdToken();
      
      // Save Firebase ID token and User UID
      localStorage.setItem('studyos_token', token);
      localStorage.setItem('studyos_user_id', user.uid);
      
      router.push('/dashboard');
    } catch (err: any) {
      setError(err?.message || 'Failed to login with Google.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.authContainer}>
      <div className={`${styles.bgShape} ${styles.shape1}`}></div>
      <div className={`${styles.bgShape} ${styles.shape2}`}></div>
      
      <div className={styles.authCard}>
        <div className={styles.authHeader}>
          <h1 className={styles.title}>Welcome to StudyOS</h1>
          <p className={styles.subtitle}>Sign in with Google to continue.</p>
        </div>

        {error && <div className={styles.errorText}>{error}</div>}

        <button 
          onClick={handleGoogleLogin} 
          className={styles.submitBtn} 
          disabled={isLoading}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', backgroundColor: '#ffffff', color: '#000000' }}
        >
          <img src="https://www.google.com/favicon.ico" alt="Google" width="20" height="20" />
          {isLoading ? 'Signing in...' : 'Sign in with Google'}
        </button>

        <div className={styles.footer}>
          By continuing, you agree to our Terms of Service.
        </div>
      </div>
    </div>
  );
}
