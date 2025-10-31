import { api } from './api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { User } from '@types';

export interface LoginPayload { username: string; password: string }
export interface AuthResponse { token: string; user: User }

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/api/auth/login', payload);
  await AsyncStorage.setItem('auth_token', data.token);
  await AsyncStorage.setItem('user_data', JSON.stringify(data.user));
  return data;
}

export async function logout() {
  await AsyncStorage.removeItem('auth_token');
  await AsyncStorage.removeItem('user_data');
}

export async function getStoredUser(): Promise<User | null> {
  const raw = await AsyncStorage.getItem('user_data');
  return raw ? JSON.parse(raw) : null;
}
