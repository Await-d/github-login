import React, { useState, useEffect } from 'react';
import {
  Layout,
  Card,
  Table,
  Button,
  Space,
  message,
  Popconfirm,
  Typography,
  Modal,
  Row,
  Col,
  Statistic,
  Progress,
  Input,
  DatePicker,
  Select,
  Tabs
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  LogoutOutlined,
  ReloadOutlined,
  KeyOutlined,
  CopyOutlined,
  ImportOutlined,
  SearchOutlined,
  FilterOutlined,
  SettingOutlined,
  GithubOutlined,
  GlobalOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { githubAPI } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import GitHubAccountForm from '../components/GitHubAccountForm';
import BatchImportModal from '../components/BatchImportModal';
import UserSettingsModal from '../components/UserSettingsModal';
import ApiWebsiteManagement from './ApiWebsiteManagement';
import ScheduledTasksManagement from './ScheduledTasksManagement';

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { Search } = Input;
const { RangePicker } = DatePicker;
const { Option } = Select;

interface GitHubAccount {
  id: number;
  username: string;
  password: string;
  totp_secret: string;
  created_at: string;
  updated_at: string;
}

interface TOTPItem {
  id: number;
  username: string;
  token: string;
  time_remaining: number;
}

interface SingleTOTPData {
  token: string;
  time_remaining: number;
}

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [accounts, setAccounts] = useState<GitHubAccount[]>([]);
  const [filteredAccounts, setFilteredAccounts] = useState<GitHubAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [formVisible, setFormVisible] = useState(false);
  const [editingAccount, setEditingAccount] = useState<GitHubAccount | undefined>();
  const [totpModalVisible, setTotpModalVisible] = useState(false);
  const [totpData, setTotpData] = useState<TOTPItem[]>([]);
  const [totpLoading, setTotpLoading] = useState(false);
  const [countdown, setCountdown] = useState<{[key: number]: number}>({});
  const [batchImportVisible, setBatchImportVisible] = useState(false);
  
  // 单个TOTP相关状态
  const [singleTotpVisible, setSingleTotpVisible] = useState(false);
  const [singleTotpData, setSingleTotpData] = useState<SingleTOTPData | null>(null);
  const [singleTotpLoading, setSingleTotpLoading] = useState(false);
  const [singleTotpCountdown, setSingleTotpCountdown] = useState(0);
  const [currentTotpAccount, setCurrentTotpAccount] = useState<GitHubAccount | null>(null);
  
  // 用户设置相关状态
  const [userSettingsVisible, setUserSettingsVisible] = useState(false);
  
  // 搜索和筛选状态
  const [searchText, setSearchText] = useState('');
  const [dateRange, setDateRange] = useState<[any, any] | null>(null);
  const [sortOrder, setSortOrder] = useState<'ascend' | 'descend' | null>('descend');

  useEffect(() => {
    loadAccounts();
  }, []);

  // TOTP倒计时定时器
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (totpModalVisible && totpData.length > 0) {
      // 初始化倒计时
      const initialCountdown: {[key: number]: number} = {};
      totpData.forEach(item => {
        initialCountdown[item.id] = item.time_remaining;
      });
      setCountdown(initialCountdown);
      
      // 每秒更新倒计时
      interval = setInterval(() => {
        setCountdown(prev => {
          const newCountdown = { ...prev };
          let shouldRefresh = false;
          
          Object.keys(newCountdown).forEach(key => {
            const id = parseInt(key);
            if (newCountdown[id] > 0) {
              newCountdown[id] -= 1;
            } else {
              // 倒计时结束，需要刷新TOTP
              shouldRefresh = true;
            }
          });
          
          // 如果有任何倒计时到达0，刷新TOTP数据
          if (shouldRefresh) {
            showTOTPBatch();
          }
          
          return newCountdown;
        });
      }, 1000);
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [totpModalVisible, totpData]);
  
  // 单个TOTP倒计时定时器
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (singleTotpVisible && singleTotpData) {
      // 每秒更新倒计时
      interval = setInterval(() => {
        setSingleTotpCountdown(prev => {
          if (prev > 0) {
            return prev - 1;
          } else {
            // 倒计时结束，刷新单个TOTP
            if (currentTotpAccount) {
              showSingleTOTP(currentTotpAccount);
            }
            return 0;
          }
        });
      }, 1000);
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [singleTotpVisible, singleTotpData, currentTotpAccount]);

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const response = await githubAPI.getAccounts();
      if (response.data.success) {
        setAccounts(response.data.accounts || []);
        setFilteredAccounts(response.data.accounts || []);
      }
    } catch (error: any) {
      message.error('加载账号列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 筛选和搜索逻辑
  useEffect(() => {
    let filtered = [...accounts];

    // 用户名搜索
    if (searchText) {
      filtered = filtered.filter(account => 
        account.username.toLowerCase().includes(searchText.toLowerCase())
      );
    }

    // 日期范围筛选
    if (dateRange && dateRange[0] && dateRange[1]) {
      const startDate = dateRange[0].startOf('day');
      const endDate = dateRange[1].endOf('day');
      filtered = filtered.filter(account => {
        const accountDate = new Date(account.created_at);
        return accountDate >= startDate.toDate() && accountDate <= endDate.toDate();
      });
    }

    // 排序
    if (sortOrder) {
      filtered.sort((a, b) => {
        const dateA = new Date(a.created_at).getTime();
        const dateB = new Date(b.created_at).getTime();
        return sortOrder === 'ascend' ? dateA - dateB : dateB - dateA;
      });
    }

    setFilteredAccounts(filtered);
  }, [accounts, searchText, dateRange, sortOrder]);

  // 重置筛选条件
  const handleResetFilters = () => {
    setSearchText('');
    setDateRange(null);
    setSortOrder('descend');
  };

  const handleAddAccount = () => {
    setEditingAccount(undefined);
    setFormVisible(true);
  };

  const handleEditAccount = async (id: number) => {
    try {
      const response = await githubAPI.getAccount(id);
      if (response.data.success) {
        setEditingAccount(response.data.account);
        setFormVisible(true);
      }
    } catch (error) {
      message.error('获取账号详情失败');
    }
  };

  const handleDeleteAccount = async (id: number) => {
    try {
      const response = await githubAPI.deleteAccount(id);
      if (response.data.success) {
        message.success('删除成功');
        loadAccounts();
      }
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleFormSubmit = async (values: any) => {
    try {
      if (editingAccount) {
        await githubAPI.updateAccount(editingAccount.id, values);
        message.success('更新成功');
      } else {
        await githubAPI.createAccount(values);
        message.success('添加成功');
      }
      setFormVisible(false);
      loadAccounts();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  const showTOTPBatch = async () => {
    setTotpLoading(true);
    setTotpModalVisible(true);
    try {
      const response = await githubAPI.getAllTOTP();
      if (response.data.success) {
        setTotpData(response.data.accounts);
        // 重置倒计时
        const newCountdown: {[key: number]: number} = {};
        response.data.accounts.forEach((item: TOTPItem) => {
          newCountdown[item.id] = item.time_remaining;
        });
        setCountdown(newCountdown);
      }
    } catch (error) {
      message.error('获取TOTP验证码失败');
    } finally {
      setTotpLoading(false);
    }
  };

  const closeTOTPModal = () => {
    setTotpModalVisible(false);
    setCountdown({});
    setTotpData([]);
  };

  const copyToClipboard = (text: string) => {
    // 兼容不同浏览器的复制方法
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        message.success('已复制到剪贴板');
      }).catch(() => {
        fallbackCopyTextToClipboard(text);
      });
    } else {
      fallbackCopyTextToClipboard(text);
    }
  };

  const fallbackCopyTextToClipboard = (text: string) => {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    
    // 避免滚动到底部
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";

    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
      const successful = document.execCommand('copy');
      if (successful) {
        message.success('已复制到剪贴板');
      } else {
        message.error('复制失败，请手动复制');
      }
    } catch (err) {
      message.error('复制失败，请手动复制');
    }

    document.body.removeChild(textArea);
  };
  
  const showSingleTOTP = async (account: GitHubAccount) => {
    setSingleTotpLoading(true);
    setCurrentTotpAccount(account);
    setSingleTotpVisible(true);
    
    try {
      const response = await githubAPI.getTOTP(account.id);
      if (response.data.success) {
        setSingleTotpData({
          token: response.data.token.token,
          time_remaining: response.data.token.time_remaining
        });
        setSingleTotpCountdown(response.data.token.time_remaining);
      } else {
        message.error('获取TOTP验证码失败');
      }
    } catch (error) {
      message.error('获取TOTP验证码失败');
    } finally {
      setSingleTotpLoading(false);
    }
  };
  
  const closeSingleTOTPModal = () => {
    setSingleTotpVisible(false);
    setSingleTotpData(null);
    setSingleTotpCountdown(0);
    setCurrentTotpAccount(null);
  };
  
  const handleUserUpdate = (updatedUser: any) => {
    // 更新本地用户信息
    const currentUserData = JSON.parse(localStorage.getItem('user') || '{}');
    const newUserData = { ...currentUserData, ...updatedUser };
    localStorage.setItem('user', JSON.stringify(newUserData));
    
    // 触发useAuth的更新（如果需要的话）
    window.location.reload();
  };

  const formatTOTPToken = (token: string) => {
    return `${token.slice(0, 3)} ${token.slice(3)}`;
  };

  const handleBatchImport = async (accounts: any[]) => {
    try {
      const response = await githubAPI.batchImport(accounts);
      if (response.data.success) {
        const result = response.data.result;
        if (result.success_count > 0) {
          message.success(`成功导入 ${result.success_count} 个账号`);
          if (result.error_count > 0) {
            message.warning(`有 ${result.error_count} 个账号导入失败`);
            // 显示错误详情
            result.errors.forEach((error: string) => {
              message.error(error);
            });
          }
        } else {
          message.error('批量导入失败：没有成功导入任何账号');
        }
      } else {
        message.error('批量导入失败：' + response.data.message);
      }
      setBatchImportVisible(false);
      loadAccounts();
    } catch (error: any) {
      message.error('批量导入失败：' + (error.response?.data?.detail || error.message));
    }
  };

  const columns = [
    {
      title: 'GitHub用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '创建日期',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (text: string) => new Date(text).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: GitHubAccount) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<KeyOutlined />}
            onClick={() => showSingleTOTP(record)}
          >
            TOTP
          </Button>
          <Button
            type="primary"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleEditAccount(record.id)}
          >
            查看
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditAccount(record.id)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个账号吗？"
            onConfirm={() => handleDeleteAccount(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  const totpColumns = [
    {
      title: 'GitHub用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: 'TOTP验证码',
      dataIndex: 'token',
      key: 'token',
      render: (token: string) => (
        <Space>
          <Text code style={{ fontSize: '16px', fontFamily: 'monospace' }}>
            {formatTOTPToken(token)}
          </Text>
          <Button
            type="text"
            size="small"
            icon={<CopyOutlined />}
            onClick={() => copyToClipboard(token)}
          />
        </Space>
      )
    },
    {
      title: '剩余时间',
      dataIndex: 'time_remaining',
      key: 'time_remaining',
      render: (time: number, record: TOTPItem) => {
        const currentTime = countdown[record.id] !== undefined ? countdown[record.id] : time;
        return (
          <Space>
            <Progress
              type="circle"
              size={40}
              percent={(currentTime / 30) * 100}
              showInfo={false}
              strokeColor={currentTime <= 10 ? '#ff4d4f' : '#52c41a'}
            />
            <Text>{currentTime}秒</Text>
          </Space>
        );
      }
    }
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 24px', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
          GitHub账号管理系统
        </Title>
        <Space>
          <Text>欢迎，{user?.username}</Text>
          <Button
            type="text"
            icon={<SettingOutlined />}
            onClick={() => setUserSettingsVisible(true)}
          >
            用户设置
          </Button>
          <Button
            type="text"
            icon={<LogoutOutlined />}
            onClick={logout}
          >
            退出登录
          </Button>
        </Space>
      </Header>

      <Content style={{ padding: '24px' }}>
        <Tabs
          defaultActiveKey="github"
          size="large"
          items={[
            {
              key: 'github',
              label: (
                <span>
                  <GithubOutlined />
                  GitHub账号管理
                </span>
              ),
              children: (
                <div>
                  <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                    <Col span={6}>
                      <Card>
                        <Statistic
                          title="总账号数"
                          value={accounts.length}
                          valueStyle={{ color: '#3f8600' }}
                        />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card>
                        <Statistic
                          title="筛选结果"
                          value={filteredAccounts.length}
                          valueStyle={{ color: '#1890ff' }}
                        />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card>
                        <Statistic
                          title="今日创建"
                          value={accounts.filter(a => a.created_at === new Date().toISOString().split('T')[0]).length}
                          valueStyle={{ color: '#faad14' }}
                        />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card>
                        <Statistic
                          title="技术栈"
                          value="Python + React"
                          valueStyle={{ color: '#722ed1' }}
                        />
                      </Card>
                    </Col>
                  </Row>

                  <Card
                    title="GitHub账号列表"
                    extra={
                      <Space>
                        <Button
                          type="primary"
                          icon={<KeyOutlined />}
                          onClick={showTOTPBatch}
                          loading={totpLoading}
                        >
                          批量查看TOTP
                        </Button>
                        <Button
                          icon={<ImportOutlined />}
                          onClick={() => setBatchImportVisible(true)}
                        >
                          批量导入
                        </Button>
                        <Button
                          icon={<ReloadOutlined />}
                          onClick={loadAccounts}
                          loading={loading}
                        >
                          刷新
                        </Button>
                        <Button
                          type="primary"
                          icon={<PlusOutlined />}
                          onClick={handleAddAccount}
                        >
                          添加账号
                        </Button>
                      </Space>
                    }
                  >
                    {/* 搜索和筛选区域 */}
                    <div style={{ marginBottom: 16 }}>
                      <Row gutter={[16, 16]}>
                        <Col span={8}>
                          <Search
                            placeholder="搜索GitHub用户名"
                            value={searchText}
                            onChange={(e) => setSearchText(e.target.value)}
                            onSearch={(value) => setSearchText(value)}
                            style={{ width: '100%' }}
                            prefix={<SearchOutlined />}
                            allowClear
                          />
                        </Col>
                        <Col span={8}>
                          <RangePicker
                            placeholder={['开始日期', '结束日期']}
                            value={dateRange}
                            onChange={(dates) => setDateRange(dates)}
                            style={{ width: '100%' }}
                          />
                        </Col>
                        <Col span={4}>
                          <Select
                            placeholder="排序方式"
                            value={sortOrder}
                            onChange={(value) => setSortOrder(value)}
                            style={{ width: '100%' }}
                          >
                            <Option value="descend">创建时间↓</Option>
                            <Option value="ascend">创建时间↑</Option>
                          </Select>
                        </Col>
                        <Col span={4}>
                          <Button
                            icon={<FilterOutlined />}
                            onClick={handleResetFilters}
                            style={{ width: '100%' }}
                          >
                            重置筛选
                          </Button>
                        </Col>
                      </Row>
                    </div>

                    <Table
                      columns={columns}
                      dataSource={filteredAccounts}
                      rowKey="id"
                      loading={loading}
                      pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 个账号`
                      }}
                    />
                  </Card>
                </div>
              )
            },
            {
              key: 'api-websites',
              label: (
                <span>
                  <GlobalOutlined />
                  API网站管理
                </span>
              ),
              children: <ApiWebsiteManagement />
            },
            {
              key: 'scheduled-tasks',
              label: (
                <span>
                  <ClockCircleOutlined />
                  定时任务管理
                </span>
              ),
              children: <ScheduledTasksManagement />
            }
          ]}
        />

        <GitHubAccountForm
          visible={formVisible}
          onCancel={() => setFormVisible(false)}
          onSubmit={handleFormSubmit}
          account={editingAccount}
        />

        <Modal
          title="TOTP验证码"
          open={totpModalVisible}
          onCancel={closeTOTPModal}
          footer={[
            <Button key="refresh" icon={<ReloadOutlined />} onClick={showTOTPBatch} loading={totpLoading}>
              刷新
            </Button>,
            <Button key="close" onClick={closeTOTPModal}>
              关闭
            </Button>
          ]}
          width={600}
        >
          <Table
            columns={totpColumns}
            dataSource={totpData}
            rowKey="id"
            loading={totpLoading}
            pagination={false}
            size="middle"
          />
        </Modal>

        <BatchImportModal
          visible={batchImportVisible}
          onCancel={() => setBatchImportVisible(false)}
          onSubmit={handleBatchImport}
        />
        
        <Modal
          title={`${currentTotpAccount?.username} - TOTP验证码`}
          open={singleTotpVisible}
          onCancel={closeSingleTOTPModal}
          footer={[
            <Button key="refresh" icon={<ReloadOutlined />} onClick={() => currentTotpAccount && showSingleTOTP(currentTotpAccount)} loading={singleTotpLoading}>
              刷新
            </Button>,
            <Button key="close" onClick={closeSingleTOTPModal}>
              关闭
            </Button>
          ]}
          width={400}
        >
          {singleTotpLoading ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <Text>正在生成TOTP验证码...</Text>
            </div>
          ) : singleTotpData ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div>
                  <Text type="secondary">验证码</Text>
                  <div style={{ margin: '10px 0' }}>
                    <Text code style={{ fontSize: '24px', fontFamily: 'monospace', fontWeight: 'bold' }}>
                      {formatTOTPToken(singleTotpData.token)}
                    </Text>
                    <Button
                      type="text"
                      size="small"
                      icon={<CopyOutlined />}
                      onClick={() => copyToClipboard(singleTotpData.token)}
                      style={{ marginLeft: 8 }}
                    />
                  </div>
                </div>
                <div>
                  <Text type="secondary">剩余时间</Text>
                  <div style={{ margin: '10px 0' }}>
                    <Progress
                      type="circle"
                      size={60}
                      percent={(singleTotpCountdown / 30) * 100}
                      showInfo={false}
                      strokeColor={singleTotpCountdown <= 10 ? '#ff4d4f' : '#52c41a'}
                    />
                    <div style={{ marginTop: 8 }}>
                      <Text style={{ fontSize: '16px' }}>{singleTotpCountdown}秒</Text>
                    </div>
                  </div>
                </div>
              </Space>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <Text type="secondary">无法获取TOTP验证码</Text>
            </div>
          )}
        </Modal>
        
        <UserSettingsModal
          visible={userSettingsVisible}
          onCancel={() => setUserSettingsVisible(false)}
          user={user}
          onUserUpdate={handleUserUpdate}
        />
      </Content>
    </Layout>
  );
};

export default Dashboard;