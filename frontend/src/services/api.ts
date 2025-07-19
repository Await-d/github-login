import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 用户接口
export const authAPI = {
  register: (username: string, password: string) =>
    api.post('/auth/register', { username, password }),
  
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  
  getCurrentUser: () =>
    api.get('/auth/me'),
};

// GitHub账号接口
export const githubAPI = {
  // 获取所有账号
  getAccounts: () =>
    api.get('/github/accounts'),
  
  // 获取单个账号详情（包含真实密码和密钥）
  getAccount: (id: number) =>
    api.get(`/github/accounts/${id}`),
  
  // 创建账号
  createAccount: (data: {
    username: string;
    password: string;
    totp_secret: string;
    created_at: string;
  }) =>
    api.post('/github/accounts', data),
  
  // 更新账号
  updateAccount: (id: number, data: any) =>
    api.put(`/github/accounts/${id}`, data),
  
  // 删除账号
  deleteAccount: (id: number) =>
    api.delete(`/github/accounts/${id}`),
  
  // 获取TOTP验证码
  getTOTP: (id: number) =>
    api.get(`/github/accounts/${id}/totp`),
  
  // 批量获取所有TOTP验证码
  getAllTOTP: () =>
    api.get('/github/totp/batch'),
  
  // 批量导入账号
  batchImport: (accounts: Array<{
    username: string;
    password: string;
    totp_secret: string;
    created_at: string;
  }>) =>
    api.post('/github/accounts/batch-import', { accounts }),
};

export default api;