import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { loginWithGoogle, registerUser } from '../api';
import { useAuth } from '../store';

import './auth.css';

export default function Signup() {
  const { login } = useAuth();
  const [form, setForm] = useState({
    email: '',
    username: '',
    first_name: '',
    last_name: '',
    password: '',
  });
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

    setForm((current) => ({
      ...current,
      [name]: value,
      ...(name === 'email' && !current.username
        ? { username: value.split('@')[0].replace(/[^a-zA-Z0-9_-]/g, '') }
        : {}),
    }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await registerUser({
        email: form.email,
        username: form.username,
        first_name: form.first_name,
        last_name: form.last_name,
        password: form.password,
      });
      login(response.data);
      window.location.hash = '#/';
    } catch (authError) {
      setError(authError?.response?.data?.detail || 'Create account failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="glass-card auth-shell">
        <header className="auth-tabs">
          <button
            type="button"
            className="auth-tab"
            onClick={() => {
              window.location.hash = '#/login';
            }}
            aria-label="Go to sign in"
          >
            Sign in
          </button>
          <button type="button" className="auth-tab" aria-current="page">
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
                Create your account to save searches, track sellers, and get price alerts.
              </p>
            </div>

            <ul>
              <li>Track verified sellers and scoring</li>
              <li>Save searches and compare later</li>
              <li>Get notified when prices drop</li>
              <li>Google or custom login supported</li>
            </ul>
          </aside>

          <section className="auth-right">
            <h3 className="auth-title">Create account</h3>
            <div className="auth-kicker">Join Fetari</div>
            <p className="auth-subtitle">Join Fetari free, always. Find the best seller in Ethiopia.</p>

            <div className="auth-google">
              {googleClientId ? (
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={handleGoogleError}
                  theme="outline"
                  size="large"
                  shape="rectangular"
                  text="signup_with"
                  width="360"
                />
              ) : (
                <button type="button" className="auth-google-fallback">
                  <span>G</span>
                  Sign up with Google
                </button>
              )}
            </div>

            <div className="auth-divider">or</div>

            <form onSubmit={onSubmit}>
              <input type="hidden" name="username" value={form.username} readOnly />

              <div className="auth-name-grid">
                <div className="auth-field">
                  <div className="auth-label">First name</div>
                  <input
                    className="auth-input"
                    type="text"
                    name="first_name"
                    value={form.first_name}
                    onChange={onChange}
                    placeholder="First"
                    autoComplete="given-name"
                  />
                </div>

                <div className="auth-field">
                  <div className="auth-label">Last name</div>
                  <input
                    className="auth-input"
                    type="text"
                    name="last_name"
                    value={form.last_name}
                    onChange={onChange}
                    placeholder="Last"
                    autoComplete="family-name"
                  />
                </div>
              </div>

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
                  autoComplete="new-password"
                  required
                />
              </div>

              <div className="auth-row">
                <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{loading ? 'Creating…' : ''}</span>
                <a className="auth-link" href="/#/login">Already have an account?</a>
              </div>

              <button className="auth-primary" type="submit" disabled={loading}>
                Create my account
              </button>
            </form>

            {(error || message) && (
              <div className="auth-message" data-variant={error ? 'error' : 'success'}>
                {error || message}
              </div>
            )}

            <div className="auth-footer">
              Already have an account? <a href="/#/login">Sign in</a>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
