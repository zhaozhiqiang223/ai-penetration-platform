import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('accessToken');
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
    if (error.response) {
      const { status, data } = error.response;
      
      // 处理401未授权错误
      if (status === 401) {
        // 清除本地存储的token
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        
        // 重定向到登录页
        window.location.href = '/login';
      }
      
      // 处理403权限错误
      if (status === 403) {
        console.error('Permission denied:', data.detail);
      }
      
      // 处理500服务器错误
      if (status === 500) {
        console.error('Server error:', data.detail);
      }
    }
    
    return Promise.reject(error);
  }
);

// 认证相关API
export const authAPI = {
  // 用户注册
  register: (userData) => api.post('/auth/register', userData),
  
  // 用户登录
  login: (loginData) => api.post('/auth/login', loginData),
  
  // 刷新令牌
  refreshToken: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
  
  // 用户登出
  logout: () => api.post('/auth/logout'),
  
  // 修改密码
  changePassword: (currentPassword, newPassword) => 
    api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword }),
  
  // 重置密码
  resetPassword: (email) => api.post('/auth/reset-password', { email }),
  
  // 确认密码重置
  confirmPasswordReset: (token, newPassword) => 
    api.post('/auth/confirm-password-reset', { token, new_password: newPassword }),
};

// 目标管理API
export const targetAPI = {
  // 创建目标
  create: (targetData) => api.post('/targets', targetData),
  
  // 获取目标列表
  list: (params = {}) => api.get('/targets', { params }),
  
  // 获取目标详情
  get: (targetId) => api.get(`/targets/${targetId}`),
  
  // 更新目标
  update: (targetId, targetData) => api.put(`/targets/${targetId}`, targetData),
  
  // 删除目标
  delete: (targetId) => api.delete(`/targets/${targetId}`),
  
  // 发现目标
  discover: (discoveryData) => api.post('/targets/discover', discoveryData),
  
  // 获取目标统计
  statistics: () => api.get('/targets/statistics'),
};

// 扫描管理API
export const scanAPI = {
  // 创建扫描
  create: (scanData) => api.post('/scans', scanData),
  
  // 启动扫描
  start: (scanId) => api.post(`/scans/${scanId}/start`),
  
  // 取消扫描
  cancel: (scanId) => api.post(`/scans/${scanId}/cancel`),
  
  // 获取扫描详情
  get: (scanId) => api.get(`/scans/${scanId}`),
  
  // 获取扫描列表
  list: (params = {}) => api.get('/scans', { params }),
  
  // 获取正在运行的扫描
  running: () => api.get('/scans/running'),
  
  // 获取引擎状态
  engineStatus: () => api.get('/engine/status'),
};

// 用户管理API
export const userAPI = {
  // 获取当前用户信息
  getCurrentUser: () => api.get('/users/me'),
  
  // 获取用户列表
  list: (params = {}) => api.get('/users', { params }),
  
  // 获取用户详情
  get: (userId) => api.get(`/users/${userId}`),
  
  // 更新用户
  update: (userId, userData) => api.put(`/users/${userId}`, userData),
  
  // 删除用户
  delete: (userId) => api.delete(`/users/${userId}`),
};

// 系统API
export const systemAPI = {
  // 健康检查
  health: () => api.get('/health'),
  
  // API信息
  info: () => api.get('/info'),
};

// 导出默认API实例
export default api;