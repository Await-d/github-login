import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '../services/api';

interface User {
  id: number;
  username: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<{ success: boolean; message?: string }>;
  register: (username: string, password: string) => Promise<{ success: boolean; message?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');

    if (!token) {
      setIsAuthenticated(false);
      setLoading(false);
      return;
    }

    // 先从localStorage恢复用户状态，提供快速响应
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
        setIsAuthenticated(true);
      } catch (error) {
        localStorage.removeItem('user');
        setIsAuthenticated(false);
      }
    }

    try {
      const response = await authAPI.getCurrentUser();
      if (response.data.success) {
        setUser(response.data.user);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        setIsAuthenticated(true);
      } else {
        // API调用失败，清除状态
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      // API调用失败，清除状态
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string) => {
    try {
      const response = await authAPI.login(username, password);
      if (response.data.success && response.data.user && response.data.access_token) {
        // 立即更新状态和本地存储
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        setUser(response.data.user);
        setIsAuthenticated(true);
        return { success: true };
      } else {
        return { success: false, message: '登录响应无效' };
      }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '登录失败'
      };
    }
  };

  const register = async (username: string, password: string) => {
    try {
      const response = await authAPI.register(username, password);
      if (response.data.success) {
        return { success: true };
      } else {
        return { success: false, message: response.data.message || '注册失败' };
      }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '注册失败'
      };
    }
  };

  const logout = () => {
    // 立即清除状态和本地存储
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};