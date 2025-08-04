import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  message,
  Popconfirm,
  Typography,
  Tag,
  Modal,
  Statistic,
  Row,
  Col,
  Spin,
  Tooltip
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  LoginOutlined,
  ReloadOutlined,
  DollarOutlined,
  KeyOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import { apiWebsiteAPI } from '../services/api';
import ApiWebsiteForm from '../components/ApiWebsiteForm';

const { Title, Text } = Typography;

interface ApiWebsite {
  id: number;
  name: string;
  type: string;
  login_url: string;
  username: string;
  is_logged_in: string;
  last_login_time?: string;
  balance: number;
  created_at: string;
  updated_at: string;
}

interface AccountInfo {
  balance: number;
  api_keys: Array<{
    id: number;
    name: string;
    key: string;
    created_at: string;
    status: string;
  }>;
  last_updated: string;
}

const ApiWebsiteManagement: React.FC = () => {
  const [websites, setWebsites] = useState<ApiWebsite[]>([]);
  const [loading, setLoading] = useState(false);
  const [formVisible, setFormVisible] = useState(false);
  const [editingWebsite, setEditingWebsite] = useState<ApiWebsite | undefined>();
  const [accountInfoVisible, setAccountInfoVisible] = useState(false);
  const [currentAccountInfo, setCurrentAccountInfo] = useState<AccountInfo | null>(null);
  const [accountInfoLoading, setAccountInfoLoading] = useState(false);

  useEffect(() => {
    loadWebsites();
  }, []);

  const loadWebsites = async () => {
    setLoading(true);
    try {
      const response = await apiWebsiteAPI.getWebsites();
      if (response.data.success) {
        setWebsites(response.data.websites || []);
      } else {
        message.error('获取API网站列表失败');
      }
    } catch (error: any) {
      message.error('加载API网站列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAddWebsite = () => {
    setEditingWebsite(undefined);
    setFormVisible(true);
  };

  const handleEditWebsite = async (id: number) => {
    try {
      const response = await apiWebsiteAPI.getWebsite(id);
      if (response.data.success) {
        setEditingWebsite(response.data.website);
        setFormVisible(true);
      } else {
        message.error('获取网站详情失败');
      }
    } catch (error) {
      message.error('获取网站详情失败');
    }
  };

  const handleDeleteWebsite = async (id: number) => {
    try {
      const response = await apiWebsiteAPI.deleteWebsite(id);
      if (response.data.success) {
        message.success('删除成功');
        loadWebsites();
      } else {
        message.error('删除失败');
      }
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleFormSubmit = async (values: any) => {
    try {
      if (editingWebsite) {
        const response = await apiWebsiteAPI.updateWebsite(editingWebsite.id, values);
        if (response.data.success) {
          message.success('更新成功');
        } else {
          message.error('更新失败');
        }
      } else {
        const response = await apiWebsiteAPI.createWebsite(values);
        if (response.data.success) {
          message.success('添加成功');
        } else {
          message.error('添加失败');
        }
      }
      setFormVisible(false);
      loadWebsites();
    } catch (error: any) {
      throw error; // 让表单组件处理错误
    }
  };

  const handleSimulateLogin = async (website: ApiWebsite) => {
    const loadingMessage = message.loading('正在模拟登录...', 0);
    try {
      const response = await apiWebsiteAPI.simulateLogin(website.id);
      loadingMessage();
      
      if (response.data.success) {
        message.success(`${website.name} 登录成功`);
        if (response.data.balance !== null) {
          message.info(`当前余额: $${response.data.balance}`);
        }
        loadWebsites(); // 刷新列表显示最新状态
      } else {
        message.error(`登录失败: ${response.data.message}`);
      }
    } catch (error: any) {
      loadingMessage();
      message.error('登录模拟失败');
    }
  };

  const handleViewAccountInfo = async (website: ApiWebsite) => {
    setAccountInfoLoading(true);
    setAccountInfoVisible(true);
    setCurrentAccountInfo(null);
    
    try {
      const response = await apiWebsiteAPI.getAccountInfo(website.id);
      if (response.data.success) {
        setCurrentAccountInfo({
          balance: response.data.balance || 0,
          api_keys: response.data.api_keys || [],
          last_updated: response.data.last_updated
        });
      } else {
        message.error('获取账户信息失败');
      }
    } catch (error) {
      message.error('获取账户信息失败');
    } finally {
      setAccountInfoLoading(false);
    }
  };

  const columns = [
    {
      title: '网站名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: ApiWebsite) => (
        <div>
          <Text strong>{text}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.type}
          </Text>
        </div>
      )
    },
    {
      title: '登录用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: '登录状态',
      dataIndex: 'is_logged_in',
      key: 'is_logged_in',
      render: (status: string, record: ApiWebsite) => (
        <div>
          <Tag
            icon={status === 'true' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
            color={status === 'true' ? 'success' : 'default'}
          >
            {status === 'true' ? '已登录' : '未登录'}
          </Tag>
          {record.last_login_time && (
            <div style={{ fontSize: '12px', color: '#999', marginTop: 4 }}>
              最后登录: {new Date(record.last_login_time).toLocaleString('zh-CN')}
            </div>
          )}
        </div>
      )
    },
    {
      title: '余额',
      dataIndex: 'balance',
      key: 'balance',
      render: (balance: number) => (
        <Statistic
          value={balance}
          precision={2}
          prefix="$"
          valueStyle={{ fontSize: '14px' }}
        />
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: ApiWebsite) => (
        <Space>
          <Tooltip title="模拟登录">
            <Button
              type="primary"
              size="small"
              icon={<LoginOutlined />}
              onClick={() => handleSimulateLogin(record)}
            >
              登录
            </Button>
          </Tooltip>
          <Tooltip title="查看账户信息">
            <Button
              size="small"
              icon={<DollarOutlined />}
              onClick={() => handleViewAccountInfo(record)}
              disabled={record.is_logged_in !== 'true'}
            >
              账户信息
            </Button>
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditWebsite(record.id)}
            >
              编辑
            </Button>
          </Tooltip>
          <Popconfirm
            title="确定要删除这个API网站吗？"
            onConfirm={() => handleDeleteWebsite(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
              >
                删除
              </Button>
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 统计数据
  const totalWebsites = websites.length;
  const loggedInWebsites = websites.filter(w => w.is_logged_in === 'true').length;
  const totalBalance = websites.reduce((sum, w) => sum + w.balance, 0);

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总网站数"
              value={totalWebsites}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已登录"
              value={loggedInWebsites}
              suffix={`/ ${totalWebsites}`}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总余额"
              value={totalBalance}
              precision={2}
              prefix="$"
              valueStyle={{ color: '#cf1322' }}
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

      {/* 主要内容卡片 */}
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <KeyOutlined style={{ marginRight: 8 }} />
            <span>API网站管理</span>
          </div>
        }
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadWebsites}
              loading={loading}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAddWebsite}
            >
              添加网站
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={websites}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 个网站`
          }}
        />
      </Card>

      {/* 添加/编辑表单 */}
      <ApiWebsiteForm
        visible={formVisible}
        onCancel={() => setFormVisible(false)}
        onSubmit={handleFormSubmit}
        website={editingWebsite}
      />

      {/* 账户信息模态框 */}
      <Modal
        title="账户信息"
        open={accountInfoVisible}
        onCancel={() => setAccountInfoVisible(false)}
        footer={[
          <Button key="close" onClick={() => setAccountInfoVisible(false)}>
            关闭
          </Button>
        ]}
        width={600}
      >
        {accountInfoLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Text>正在获取账户信息...</Text>
            </div>
          </div>
        ) : currentAccountInfo ? (
          <div>
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
              <Col span={12}>
                <Card>
                  <Statistic
                    title="账户余额"
                    value={currentAccountInfo.balance}
                    precision={2}
                    prefix="$"
                    valueStyle={{ color: '#3f8600' }}
                  />
                </Card>
              </Col>
              <Col span={12}>
                <Card>
                  <Statistic
                    title="API密钥数量"
                    value={currentAccountInfo.api_keys.length}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Card>
              </Col>
            </Row>
            
            {currentAccountInfo.api_keys.length > 0 && (
              <div>
                <Title level={5}>API密钥列表</Title>
                <Table
                  size="small"
                  dataSource={currentAccountInfo.api_keys}
                  rowKey="id"
                  pagination={false}
                  columns={[
                    {
                      title: '名称',
                      dataIndex: 'name',
                      key: 'name'
                    },
                    {
                      title: '密钥',
                      dataIndex: 'key',
                      key: 'key',
                      render: (key: string) => (
                        <Text code copyable>
                          {key.length > 20 ? `${key.substring(0, 20)}...` : key}
                        </Text>
                      )
                    },
                    {
                      title: '状态',
                      dataIndex: 'status',
                      key: 'status',
                      render: (status: string) => (
                        <Tag color={status === 'active' ? 'green' : 'red'}>
                          {status === 'active' ? '活跃' : '不活跃'}
                        </Tag>
                      )
                    },
                    {
                      title: '创建时间',
                      dataIndex: 'created_at',
                      key: 'created_at',
                      render: (time: string) => new Date(time).toLocaleString('zh-CN')
                    }
                  ]}
                />
              </div>
            )}
            
            {currentAccountInfo.last_updated && (
              <div style={{ textAlign: 'center', marginTop: 16, color: '#999' }}>
                <InfoCircleOutlined style={{ marginRight: 4 }} />
                最后更新: {new Date(currentAccountInfo.last_updated).toLocaleString('zh-CN')}
              </div>
            )}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Text type="secondary">暂无账户信息</Text>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ApiWebsiteManagement;