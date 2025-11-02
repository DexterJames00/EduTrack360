import axios, {AxiosInstance, AxiosError} from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Base API URL - Update this to match your backend server
const API_URL = 'http://192.168.0.111:5000';
// For Android emulator: 'http://10.0.2.2:5000'
// For physical device: 'http://YOUR_COMPUTER_IP:5000'

class ApiService {
  private axiosInstance: AxiosInstance;

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: API_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.axiosInstance.interceptors.request.use(
      async config => {
        const token = await AsyncStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      error => {
        return Promise.reject(error);
      },
    );

    // Response interceptor for error handling
    this.axiosInstance.interceptors.response.use(
      response => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          await AsyncStorage.removeItem('auth_token');
          await AsyncStorage.removeItem('user_data');
          // Navigate to login screen (implement in your navigation)
        }
        return Promise.reject(error);
      },
    );
  }

  // Generic request methods
  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.axiosInstance.get<T>(url, {params});
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.axiosInstance.post<T>(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.axiosInstance.put<T>(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.axiosInstance.delete<T>(url);
    return response.data;
  }

  // Set auth token
  setAuthToken(token: string) {
    this.axiosInstance.defaults.headers.common.Authorization = `Bearer ${token}`;
  }

  // Clear auth token
  clearAuthToken() {
    delete this.axiosInstance.defaults.headers.common.Authorization;
  }

  // Get base URL for Socket.IO connection (use http(s), Socket.IO handles upgrade)
  getWebSocketUrl(): string {
    return API_URL;
  }

  // Attendance endpoints (parents)
  async getAttendanceSummary<T = any>(): Promise<T> {
    return this.get<T>('/api/attendance/summary');
  }

  async getAttendanceHistory<T = any>(limit: number = 50): Promise<T> {
    return this.get<T>('/api/attendance/history', { limit });
  }

  // Meetings endpoints
  async getMeetings<T = any>(): Promise<T> {
    return this.get<T>('/api/meetings');
  }
}

export default new ApiService();
