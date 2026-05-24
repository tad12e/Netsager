import React, { useEffect, useRef, useState } from 'react';
import { CircleCheckBig, Globe, LoaderCircle, LogIn, Shield, UserPlus } from 'lucide-react';
import { loginUser, loginWithGoogle, registerUser } from '../api';
import { useAuth } from '../store';

export default function AuthPanel() {
  const { user, login, logout } = useAuth();
  const googleButtonRef = useRef(null);
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({
    email: '',
    username: '',
    password: '',
    first_name: '',
    last_name: '',
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

  const updateField = (event) => {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
      ...(mode === 'register' && name === 'email' && !current.username
        ? { username: value.split('@')[0].replace(/[^a-zA-Z0-9_-]/g, '') }
        : {}),
    }));
  };

  const submitAuthForm = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const payload = mode === 'register'
        ? {
            email: form.email,
            username: form.username,
            password: form.password,
            first_name: form.first_name,
            last_name: form.last_name,
          }
        : {
            email: form.email,
            password: form.password,
          };

      const response = mode === 'register'
        ? await registerUser(payload)
        : await loginUser(payload);

      login(response.data);
      setMessage(mode === 'register' ? 'Account created and signed in.' : 'Signed in successfully.');
    } catch (authError) {
      setError(authError?.response?.data?.detail || 'Authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!googleClientId || !googleButtonRef.current) {
      return undefined;
    }

    const renderGoogleButton = () => {
      if (!window.google?.accounts?.id || !googleButtonRef.current) {
        return;
      }

      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (credentialResponse) => {
          setLoading(true);
          setError('');
          setMessage('');

          try {
            const response = await loginWithGoogle({ credential: credentialResponse.credential });
            login(response.data);
            setMessage('Signed in with Google.');
          } catch (googleError) {
            setError(googleError?.response?.data?.detail || 'Google sign-in failed.');
          } finally {
            setLoading(false);
          }
        },
      });

      window.google.accounts.id.renderButton(googleButtonRef.current, {
        theme: 'outline',
        size: 'large',
        shape: 'pill',
        width: 320,
        text: 'signin_with',
      });
    };

    if (window.google?.accounts?.id) {
      renderGoogleButton();
      return undefined;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = renderGoogleButton;
    document.body.appendChild(script);

    return () => {
      script.remove();
    };
  }, [googleClientId, login]);

  if (user) {
    return (
      <section className="glass-card" style={{ padding: '1.5rem', marginTop: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', color: 'var(--accent)', fontSize: '0.8rem', fontWeight: 700 }}>
              <CircleCheckBig size={16} />
              Signed in
            </div>
            <h3 style={{ fontFamily: 'Outfit', marginTop: '0.4rem', fontSize: '1.35rem' }}>Welcome back, {user.first_name || user.username || user.email}</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>{user.email}</p>
          </div>

          <button
            type="button"
            onClick={logout}
            style={{
              background: 'rgba(255,255,255,0.04)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-glass)',
              borderRadius: '999px',
              padding: '0.75rem 1.1rem',
              cursor: 'pointer',
            }}
          >
            Log out
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="glass-card" style={{ marginTop: '1.5rem', padding: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', color: 'var(--primary)', fontSize: '0.8rem', fontWeight: 700 }}>
            <Shield size={16} />
            Account access
          </div>
          <h3 style={{ fontFamily: 'Outfit', marginTop: '0.4rem', fontSize: '1.35rem' }}>Sign in with Google or your custom account</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>Use a local email/password account or Google sign-in against the same user profile.</p>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            type="button"
            onClick={() => setMode('login')}
            style={{
              background: mode === 'login' ? 'var(--primary)' : 'rgba(255,255,255,0.04)',
              color: mode === 'login' ? '#fff' : 'var(--text-secondary)',
              border: '1px solid var(--border-glass)',
              borderRadius: '999px',
              padding: '0.7rem 1rem',
              cursor: 'pointer',
            }}
          >
            <LogIn size={14} style={{ display: 'inline', marginRight: '0.35rem' }} />
            Sign in
          </button>
          <button
            type="button"
            onClick={() => setMode('register')}
            style={{
              background: mode === 'register' ? 'var(--primary)' : 'rgba(255,255,255,0.04)',
              color: mode === 'register' ? '#fff' : 'var(--text-secondary)',
              border: '1px solid var(--border-glass)',
              borderRadius: '999px',
              padding: '0.7rem 1rem',
              cursor: 'pointer',
            }}
          >
            <UserPlus size={14} style={{ display: 'inline', marginRight: '0.35rem' }} />
            Create account
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '1.25rem', marginTop: '1.25rem' }}>
        <form onSubmit={submitAuthForm} style={{ display: 'grid', gap: '0.9rem' }}>
          <div style={{ display: 'grid', gap: '0.75rem', gridTemplateColumns: mode === 'register' ? '1fr 1fr' : '1fr' }}>
            <label style={{ display: 'grid', gap: '0.35rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Email</span>
              <div style={{ position: 'relative' }}>
                <Globe size={16} style={{ position: 'absolute', left: '0.9rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                  name="email"
                  type="email"
                  value={form.email}
                  onChange={updateField}
                  placeholder="you@example.com"
                  required
                  style={{
                    width: '100%',
                    padding: '0.9rem 0.9rem 0.9rem 2.55rem',
                    borderRadius: '14px',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-glass)',
                    color: 'var(--text-primary)',
                    outline: 'none',
                  }}
                />
              </div>
            </label>

            {mode === 'register' && (
              <label style={{ display: 'grid', gap: '0.35rem' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Username</span>
                <input
                  name="username"
                  type="text"
                  value={form.username}
                  onChange={updateField}
                  placeholder="your-handle"
                  required
                  style={{
                    width: '100%',
                    padding: '0.9rem 0.9rem',
                    borderRadius: '14px',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-glass)',
                    color: 'var(--text-primary)',
                    outline: 'none',
                  }}
                />
              </label>
            )}
          </div>

          {mode === 'register' && (
            <div style={{ display: 'grid', gap: '0.75rem', gridTemplateColumns: '1fr 1fr' }}>
              <label style={{ display: 'grid', gap: '0.35rem' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>First name</span>
                <input
                  name="first_name"
                  type="text"
                  value={form.first_name}
                  onChange={updateField}
                  placeholder="First"
                  style={{
                    width: '100%',
                    padding: '0.9rem',
                    borderRadius: '14px',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-glass)',
                    color: 'var(--text-primary)',
                    outline: 'none',
                  }}
                />
              </label>
              <label style={{ display: 'grid', gap: '0.35rem' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Last name</span>
                <input
                  name="last_name"
                  type="text"
                  value={form.last_name}
                  onChange={updateField}
                  placeholder="Last"
                  style={{
                    width: '100%',
                    padding: '0.9rem',
                    borderRadius: '14px',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-glass)',
                    color: 'var(--text-primary)',
                    outline: 'none',
                  }}
                />
              </label>
            </div>
          )}

          <label style={{ display: 'grid', gap: '0.35rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Password</span>
            <input
              name="password"
              type="password"
              value={form.password}
              onChange={updateField}
              placeholder="Password"
              required
              style={{
                width: '100%',
                padding: '0.9rem',
                borderRadius: '14px',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--border-glass)',
                color: 'var(--text-primary)',
                outline: 'none',
              }}
            />
          </label>

          <button
            type="submit"
            disabled={loading}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              padding: '0.95rem 1.1rem',
              borderRadius: '14px',
              border: '1px solid hsla(var(--primary-hue), 95%, 60%, 0.3)',
              background: 'var(--primary)',
              color: '#fff',
              fontWeight: 700,
              cursor: 'pointer',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? <LoaderCircle size={16} className="animate-pulse-glow" /> : null}
            {mode === 'register' ? 'Create account' : 'Sign in'}
          </button>

          {(message || error) && (
            <div
              style={{
                padding: '0.85rem 1rem',
                borderRadius: '12px',
                border: error ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid rgba(16, 185, 129, 0.3)',
                background: error ? 'rgba(239, 68, 68, 0.08)' : 'rgba(16, 185, 129, 0.08)',
                color: error ? '#fca5a5' : 'var(--accent)',
                fontSize: '0.9rem',
              }}
            >
              {error || message}
            </div>
          )}
        </form>

        <div style={{ display: 'grid', gap: '1rem', alignContent: 'start' }}>
          <div style={{ padding: '1rem', borderRadius: '16px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)' }}>
            <h4 style={{ fontFamily: 'Outfit', fontSize: '1rem', marginBottom: '0.4rem' }}>Google sign-in</h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.9rem' }}>
              Set VITE_GOOGLE_CLIENT_ID in the frontend and GOOGLE_CLIENT_ID in the backend for verified Google login.
            </p>
            <div ref={googleButtonRef} />
            {!googleClientId && (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.75rem' }}>
                Google button is disabled until the client id is configured.
              </p>
            )}
          </div>

          <div style={{ padding: '1rem', borderRadius: '16px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)' }}>
            <h4 style={{ fontFamily: 'Outfit', fontSize: '1rem', marginBottom: '0.4rem' }}>How it works</h4>
            <ul style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', paddingLeft: '1.1rem', lineHeight: 1.6 }}>
              <li>Local accounts use email + password.</li>
              <li>Google sign-in maps the Google email to the same user model.</li>
              <li>The backend returns a DRF token for API access.</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
