import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('netracare_user');
    const token = localStorage.getItem('netracare_session_token');
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem('netracare_user');
        localStorage.removeItem('netracare_session_token');
      }
    }
    setLoading(false);
  }, []);

  const login = async (payload) => {
    const res = await api.login(payload);
    if (res.ok) {
      setUser(res.user);
      localStorage.setItem('netracare_session_token', res.session_token);
      localStorage.setItem('netracare_user', JSON.stringify(res.user));
    }
    return res;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('netracare_session_token');
    localStorage.removeItem('netracare_user');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

