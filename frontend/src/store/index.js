import { useEffect, useState, createContext, useContext } from 'react';
import { setAuthToken } from '../api';

const AuthContext = createContext(null);

const STORAGE_KEY = 'ethiocompare-auth';

function loadStoredAuth() {
  if (typeof window === 'undefined') {
    return { user: null, token: null };
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { user: null, token: null };
    }

    const parsed = JSON.parse(raw);
    return {
      user: parsed?.user || null,
      token: parsed?.token || null,
    };
  } catch {
    return { user: null, token: null };
  }
}

export function AuthProvider({ children }) {
  const [authState, setAuthState] = useState(loadStoredAuth);

  useEffect(() => {
    setAuthToken(authState.token);
  }, [authState.token]);

  const login = (authData) => {
    const nextAuthState = {
      user: authData?.user || authData || null,
      token: authData?.token || null,
    };

    setAuthState(nextAuthState);
    setAuthToken(nextAuthState.token);

    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextAuthState));
    }
  };

  const logout = () => {
    setAuthState({ user: null, token: null });
    setAuthToken(null);

    if (typeof window !== 'undefined') {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  };

  return (
    <AuthContext.Provider value={{ user: authState.user, token: authState.token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
