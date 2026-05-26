import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { loginUser, loginWithGoogle } from '../api';
import { useAuth } from '../store';

import './auth.css';

export default function Login() {
  const { login } = useAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

  const handleGoogleSuccess = async (credentialResponse) => {
    const idToken = credentialResponse?.credential;

    if (!idToken) {
      setError('Google did not return a credential.');
      return;
    }

    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await loginWithGoogle({ credential: idToken });
      login(response.data);
      window.location.hash = '#/';
    } catch (googleError) {
      const detail = googleError?.response?.data?.detail;
      const messageText = String(googleError?.message || '').toLowerCase();
      const timedOut = googleError?.code === 'ECONNABORTED' || messageText.includes('timeout');

      const networkMessage = timedOut
        ? 'Google sign-in timed out waiting for Django. Confirm the backend can reach Google (oauth2.googleapis.com) and try again.'
        : googleError?.request
          ? 'Backend did not respond. Make sure Django is running on http://127.0.0.1:8000.'
          : 'Google sign-in failed.';

      console.error('Google backend sign-in failed:', googleError);
      setError(detail || networkMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = () => {
    setError('Google sign-in was cancelled or failed.');
  };

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await loginUser({ email: form.email, password: form.password });
      login(response.data);
      window.location.hash = '#/';
    } catch (authError) {
      setError(authError?.response?.data?.detail || 'Sign in failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="glass-card auth-shell">
        <header className="auth-tabs">
          <button type="button" className="auth-tab" aria-current="page">
            Sign in
          </button>
          <button
            type="button"
            className="auth-tab"
            onClick={() => {
              window.location.hash = '#/signup';
            }}
            aria-label="Go to create account"
          >
            Create account
          </button>
        </header>

        <div className="auth-grid">
          <aside className="auth-left">
            <div className="auth-brand">
              <span className="auth-brand-mark" aria-hidden="true" />
              <div>
                <h1>Fetari</h1>
                <small>Ethiopia’s seller ranker</small>
              </div>
            </div>

            <div className="auth-hero">
              <h2>
                Find the <strong>best</strong>
                <br />
                seller in <strong>Addis</strong>
              </h2>
              <p>
                AI-powered comparison across Jiji, Shega, and more. One search. Instant results.
              </p>
            </div>

            <ul>
              <li>12,400+ sellers tracked across Ethiopia</li>
              <li>AI reviews sentiment every 6 hours</li>
              <li>Free to search — always</li>
              <li>Save searches and get price alerts</li>
            </ul>
          </aside>

          <section className="auth-right">
            <h3 className="auth-title">Welcome back</h3>
            <div className="auth-kicker">Fetari account</div>
            <p className="auth-subtitle">Continue to your account to save searches and track prices.</p>

            <div className="auth-google">
              {googleClientId ? (
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={handleGoogleError}
                  theme="outline"
                  size="large"
                  shape="rectangular"
                  text="continue_with"
                  width="360"
                />
              ) : (
                <button type="button" className="auth-google-fallback">
                  <span>G</span>
                  Continue with Google
                </button>
              )}
            </div>

            <div className="auth-divider">or</div>

            <form onSubmit={onSubmit}>
              <div className="auth-field">
                <div className="auth-label">Email address</div>
                <input
                  className="auth-input"
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={onChange}
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                />
              </div>

              <div className="auth-field">
                <div className="auth-label">Password</div>
                <input
                  className="auth-input"
                  type="password"
                  name="password"
                  value={form.password}
                  onChange={onChange}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  required
                />
              </div>

              <div className="auth-row">
                <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{loading ? 'Signing in…' : ''}</span>
                <a className="auth-link" href="#forgot">Forgot password?</a>
              </div>

              <button className="auth-primary" type="submit" disabled={loading}>
                Sign in to Fetari
              </button>
            </form>

            {(error || message) && (
              <div className="auth-message" data-variant={error ? 'error' : 'success'}>
                {error || message}
              </div>
            )}

            <div className="auth-footer">
              Don’t have an account? <a href="/#/signup">Create one free</a>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
