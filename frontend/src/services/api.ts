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
      // 重新加载页面回到登录状态
      window.location.reload();
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
  
  updateUser: (data: { username?: string }) =>
    api.put('/auth/me', data),
  
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.put('/auth/change-password', data),
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
  
  // GitHub OAuth登录到第三方网站
  oauthLogin: (githubAccountId: number, websiteUrl: string = 'https://anyrouter.top') =>
    api.post(`/github/oauth-login/${githubAccountId}?website_url=${encodeURIComponent(websiteUrl)}`),
  
  // anyrouter.top GitHub OAuth登录快捷方式
  oauthLoginAnyrouter: (githubAccountId: number) =>
    api.post(`/github/oauth-login-anyrouter/${githubAccountId}`),
};

// 定时任务接口
export const scheduledTasksAPI = {
  // 获取所有定时任务
  getTasks: () =>
    api.get('/scheduled-tasks/tasks'),
  
  // 获取任务详情
  getTask: (id: number) =>
    api.get(`/scheduled-tasks/tasks/${id}`),
  
  // 创建GitHub OAuth定时任务
  createGitHubOAuthTask: (data: {
    name: string;
    description?: string;
    cron_expression: string;
    github_account_ids: number[];
    target_website?: string;
    retry_count?: number;
    is_active?: boolean;
  }) =>
    api.post('/scheduled-tasks/tasks/github-oauth', data),
  
  // 更新任务
  updateTask: (id: number, data: {
    name?: string;
    description?: string;
    cron_expression?: string;
    task_params?: any;
    is_active?: boolean;
  }) =>
    api.put(`/scheduled-tasks/tasks/${id}`, data),
  
  // 删除任务
  deleteTask: (id: number) =>
    api.delete(`/scheduled-tasks/tasks/${id}`),
  
  // 手动执行任务
  runTask: (id: number) =>
    api.post(`/scheduled-tasks/tasks/${id}/run`),
  
  // 获取任务执行日志
  getTaskLogs: (id: number, limit?: number) =>
    api.get(`/scheduled-tasks/tasks/${id}/logs`, { params: { limit } }),
  
  // 切换任务状态
  toggleTask: (id: number) =>
    api.post(`/scheduled-tasks/tasks/${id}/toggle`),
};

// API网站接口
export const apiWebsiteAPI = {
  // 获取所有API网站
  getWebsites: () =>
    api.get('/api-website/websites'),
  
  // 获取单个API网站详情
  getWebsite: (id: number) =>
    api.get(`/api-website/websites/${id}`),
  
  // 创建API网站
  createWebsite: (data: {
    name: string;
    type: string;
    login_url: string;
    username: string;
    password: string;
  }) =>
    api.post('/api-website/websites', data),
  
  // 更新API网站
  updateWebsite: (id: number, data: any) =>
    api.put(`/api-website/websites/${id}`, data),
  
  // 删除API网站
  deleteWebsite: (id: number) =>
    api.delete(`/api-website/websites/${id}`),
  
  // 模拟登录
  simulateLogin: (id: number) =>
    api.post(`/api-website/websites/${id}/login`),
  
  // 获取账户信息
  getAccountInfo: (id: number) =>
    api.get(`/api-website/websites/${id}/account-info`),
};

export default api;