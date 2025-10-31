import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '@services/api.service';
import { User } from '../types';

interface AuthContextShape {
  user: User | null;
  loading: boolean;
  login: (payload: { username: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextShape | undefined>(undefined);

export const AuthProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const raw = await AsyncStorage.getItem('user_data');
        const token = await AsyncStorage.getItem('auth_token');
        if (token) {
          api.setAuthToken(token);
          try {
            await api.get('/api/auth/verify');
          } catch {
            await AsyncStorage.removeItem('auth_token');
            await AsyncStorage.removeItem('user_data');
          }
        }
        if (raw) setUser(JSON.parse(raw));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const value = useMemo(() => ({
    user,
    loading,
  login: async ({ username, password }: { username: string; password: string }) => {
      const res = await api.post<any>('/api/auth/login', { username, password });
      if (!res?.success) throw new Error(res?.message || 'Login failed');
      const { token, user: u } = res;
      await AsyncStorage.setItem('auth_token', token);
      await AsyncStorage.setItem('user_data', JSON.stringify(u));
      api.setAuthToken(token);
      setUser(u);
    },
    logout: async () => {
      await AsyncStorage.removeItem('user_data');
      await AsyncStorage.removeItem('auth_token');
      api.clearAuthToken();
      setUser(null);
    }
  }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
