// GitHub账号管理系统前端应用

class GitHubManager {
    constructor() {
        this.currentUser = null;
        this.accounts = [];
        this.totpInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuthStatus();
        
        // 设置当前日期为默认值
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('createdAt').value = today;
    }

    bindEvents() {
        // 认证相关事件
        document.getElementById('loginTabBtn').addEventListener('click', () => this.showLoginForm());
        document.getElementById('registerTabBtn').addEventListener('click', () => this.showRegisterForm());
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('registerForm').addEventListener('submit', (e) => this.handleRegister(e));
        document.getElementById('logoutBtn').addEventListener('click', () => this.handleLogout());

        // 账号管理事件
        document.getElementById('addAccountForm').addEventListener('submit', (e) => this.handleAddAccount(e));
        document.getElementById('refreshBtn').addEventListener('click', () => this.loadAccounts());
        document.getElementById('exportBtn').addEventListener('click', () => this.exportAccounts());
        document.getElementById('toggleTotpBtn').addEventListener('click', () => this.toggleTotpDisplay());

        // 确认对话框事件
        document.getElementById('confirmOk').addEventListener('click', () => this.handleConfirmOk());
        document.getElementById('confirmCancel').addEventListener('click', () => this.hideConfirmDialog());
    }

    // 显示消息
    showMessage(message, type = 'info') {
        const container = document.getElementById('messageContainer');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        messageElement.textContent = message;
        
        container.appendChild(messageElement);
        
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 5000);
    }

    // 显示确认对话框
    showConfirmDialog(title, message, callback) {
        document.getElementById('confirmTitle').textContent = title;
        document.getElementById('confirmMessage').textContent = message;
        document.getElementById('confirmDialog').classList.remove('hidden');
        this.confirmCallback = callback;
    }

    hideConfirmDialog() {
        document.getElementById('confirmDialog').classList.add('hidden');
        this.confirmCallback = null;
    }

    handleConfirmOk() {
        if (this.confirmCallback) {
            this.confirmCallback();
        }
        this.hideConfirmDialog();
    }

    // API请求方法
    async apiRequest(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                credentials: 'include',
                ...options
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || '请求失败');
            }
            
            return data;
        } catch (error) {
            console.error('API请求错误:', error);
            throw error;
        }
    }

    // 认证状态检查
    async checkAuthStatus() {
        try {
            const data = await this.apiRequest('/api/auth/status');
            if (data.isLoggedIn) {
                this.currentUser = data.user;
                this.showMainPage();
                this.loadAccounts();
            } else {
                this.showLoginPage();
            }
        } catch (error) {
            this.showLoginPage();
        }
    }

    // 显示登录表单
    showLoginForm() {
        document.getElementById('loginTabBtn').classList.add('active');
        document.getElementById('registerTabBtn').classList.remove('active');
        document.getElementById('loginForm').classList.remove('hidden');
        document.getElementById('registerForm').classList.add('hidden');
    }

    // 显示注册表单
    showRegisterForm() {
        document.getElementById('registerTabBtn').classList.add('active');
        document.getElementById('loginTabBtn').classList.remove('active');
        document.getElementById('registerForm').classList.remove('hidden');
        document.getElementById('loginForm').classList.add('hidden');
    }

    // 处理登录
    async handleLogin(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const loginData = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        try {
            const data = await this.apiRequest('/api/auth/login', {
                method: 'POST',
                body: JSON.stringify(loginData)
            });

            this.currentUser = data.user;
            this.showMessage('登录成功！', 'success');
            this.showMainPage();
            this.loadAccounts();
        } catch (error) {
            this.showMessage(error.message, 'error');
        }
    }

    // 处理注册
    async handleRegister(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const registerData = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        try {
            const data = await this.apiRequest('/api/auth/register', {
                method: 'POST',
                body: JSON.stringify(registerData)
            });

            this.currentUser = data.user;
            this.showMessage('注册成功！', 'success');
            this.showMainPage();
            this.loadAccounts();
        } catch (error) {
            this.showMessage(error.message, 'error');
        }
    }

    // 处理登出
    async handleLogout() {
        try {
            await this.apiRequest('/api/auth/logout', { method: 'POST' });
            this.currentUser = null;
            this.accounts = [];
            this.clearTotpInterval();
            this.showMessage('已成功登出', 'success');
            this.showLoginPage();
        } catch (error) {
            this.showMessage(error.message, 'error');
        }
    }

    // 显示页面
    showLoginPage() {
        document.getElementById('loginPage').classList.remove('hidden');
        document.getElementById('mainPage').classList.add('hidden');
    }

    showMainPage() {
        document.getElementById('loginPage').classList.add('hidden');
        document.getElementById('mainPage').classList.remove('hidden');
        if (this.currentUser) {
            document.getElementById('usernameDisplay').textContent = this.currentUser.username;
        }
    }

    // 处理添加账号
    async handleAddAccount(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const accountData = {
            username: formData.get('username'),
            password: formData.get('password'),
            totpSecret: formData.get('totpSecret'),
            createdAt: formData.get('createdAt')
        };

        try {
            await this.apiRequest('/api/github/accounts', {
                method: 'POST',
                body: JSON.stringify(accountData)
            });

            this.showMessage('GitHub账号添加成功！', 'success');
            e.target.reset();
            
            // 重置日期为今天
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('createdAt').value = today;
            
            this.loadAccounts();
        } catch (error) {
            this.showMessage(error.message, 'error');
        }
    }

    // 加载账号列表
    async loadAccounts() {
        try {
            const data = await this.apiRequest('/api/github/accounts');
            this.accounts = data.accounts || [];
            this.renderAccounts();
        } catch (error) {
            this.showMessage('加载账号列表失败: ' + error.message, 'error');
        }
    }

    // 渲染账号列表
    renderAccounts() {
        const container = document.getElementById('accountsList');
        
        if (this.accounts.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">暂无GitHub账号，请先添加账号。</p>';
            return;
        }

        container.innerHTML = this.accounts.map(account => `
            <div class="account-item" data-id="${account.id}">
                <div class="account-info">
                    <h3>${this.escapeHtml(account.username)}</h3>
                    <p>创建日期: ${account.createdAt}</p>
                </div>
                <div class="account-info">
                    <p>账号ID: ${account.id}</p>
                    <p>最后更新: ${account.updatedAt ? new Date(account.updatedAt).toLocaleDateString() : '未知'}</p>
                </div>
                <div class="account-info">
                    <button class="btn-secondary" onclick="app.getTotpCode(${account.id})">获取TOTP</button>
                </div>
                <div class="account-actions">
                    <button class="btn-secondary" onclick="app.editAccount(${account.id})">编辑</button>
                    <button class="btn-danger" onclick="app.deleteAccount(${account.id})">删除</button>
                </div>
            </div>
        `).join('');
    }

    // 获取单个账号的TOTP
    async getTotpCode(accountId) {
        try {
            const data = await this.apiRequest(`/api/github/accounts/${accountId}/totp`);
            if (data.success && data.token) {
                this.showMessage(`TOTP验证码: ${data.token.token} (剩余${data.token.timeRemaining}秒)`, 'success');
            }
        } catch (error) {
            this.showMessage('获取TOTP验证码失败: ' + error.message, 'error');
        }
    }

    // 删除账号
    deleteAccount(accountId) {
        const account = this.accounts.find(acc => acc.id === accountId);
        if (!account) return;

        this.showConfirmDialog(
            '删除账号',
            `确定要删除GitHub账号 "${account.username}" 吗？此操作不可恢复。`,
            async () => {
                try {
                    await this.apiRequest(`/api/github/accounts/${accountId}`, {
                        method: 'DELETE'
                    });
                    this.showMessage('账号删除成功', 'success');
                    this.loadAccounts();
                } catch (error) {
                    this.showMessage('删除账号失败: ' + error.message, 'error');
                }
            }
        );
    }

    // 编辑账号（简单实现）
    editAccount(accountId) {
        this.showMessage('编辑功能开发中...', 'info');
    }

    // 切换TOTP显示
    async toggleTotpDisplay() {
        const totpSection = document.getElementById('totpSection');
        
        if (totpSection.classList.contains('hidden')) {
            // 显示TOTP
            totpSection.classList.remove('hidden');
            await this.loadAllTotp();
            this.startTotpTimer();
        } else {
            // 隐藏TOTP
            totpSection.classList.add('hidden');
            this.clearTotpInterval();
        }
    }

    // 加载所有账号的TOTP
    async loadAllTotp() {
        try {
            const data = await this.apiRequest('/api/github/totp/all');
            this.renderTotpList(data.accounts || []);
        } catch (error) {
            this.showMessage('加载TOTP验证码失败: ' + error.message, 'error');
        }
    }

    // 渲染TOTP列表
    renderTotpList(totpAccounts) {
        const container = document.getElementById('totpList');
        
        if (totpAccounts.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #666;">暂无TOTP验证码</p>';
            return;
        }

        container.innerHTML = totpAccounts.map(account => `
            <div class="totp-item">
                <h4>${this.escapeHtml(account.username)}</h4>
                <div class="totp-code">${account.token}</div>
                <div class="totp-remaining">剩余 ${account.timeRemaining} 秒</div>
            </div>
        `).join('');
    }

    // 启动TOTP定时器
    startTotpTimer() {
        this.clearTotpInterval();
        
        this.totpInterval = setInterval(async () => {
            await this.loadAllTotp();
            this.updateTotpTimer();
        }, 1000);
        
        this.updateTotpTimer();
    }

    // 更新TOTP定时器显示
    updateTotpTimer() {
        const now = Math.floor(Date.now() / 1000);
        const remaining = 30 - (now % 30);
        const timerElement = document.getElementById('totpTimer');
        if (timerElement) {
            timerElement.textContent = `(${remaining}秒后刷新)`;
        }
    }

    // 清除TOTP定时器
    clearTotpInterval() {
        if (this.totpInterval) {
            clearInterval(this.totpInterval);
            this.totpInterval = null;
        }
    }

    // 导出账号信息
    async exportAccounts() {
        try {
            const response = await fetch('/api/github/export', {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('导出失败');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'github-accounts.txt';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.showMessage('账号信息导出成功', 'success');
        } catch (error) {
            this.showMessage('导出失败: ' + error.message, 'error');
        }
    }

    // HTML转义
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, (m) => map[m]);
    }
}

// 初始化应用
const app = new GitHubManager();

// 页面卸载时清理定时器
window.addEventListener('beforeunload', () => {
    app.clearTotpInterval();
});