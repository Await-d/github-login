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
  Progress
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  LogoutOutlined,
  ReloadOutlined,
  KeyOutlined,
  CopyOutlined
} from '@ant-design/icons';
import { githubAPI } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import GitHubAccountForm from '../components/GitHubAccountForm';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

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

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [accounts, setAccounts] = useState<GitHubAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [formVisible, setFormVisible] = useState(false);
  const [editingAccount, setEditingAccount] = useState<GitHubAccount | undefined>();
  const [totpModalVisible, setTotpModalVisible] = useState(false);
  const [totpData, setTotpData] = useState<TOTPItem[]>([]);
  const [totpLoading, setTotpLoading] = useState(false);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const response = await githubAPI.getAccounts();
      if (response.data.success) {
        setAccounts(response.data.accounts || []);
      }
    } catch (error: any) {
      message.error('加载账号列表失败');
    } finally {
      setLoading(false);
    }
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
      }
    } catch (error) {
      message.error('获取TOTP验证码失败');
    } finally {
      setTotpLoading(false);
    }
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

  const formatTOTPToken = (token: string) => {
    return `${token.slice(0, 3)} ${token.slice(3)}`;
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
      render: (time: number) => (
        <Space>
          <Progress
            type="circle"
            size={40}
            percent={(time / 30) * 100}
            showInfo={false}
            strokeColor={time <= 10 ? '#ff4d4f' : '#52c41a'}
          />
          <Text>{time}秒</Text>
        </Space>
      )
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
            icon={<LogoutOutlined />}
            onClick={logout}
          >
            退出登录
          </Button>
        </Space>
      </Header>

      <Content style={{ padding: '24px' }}>
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={8}>
            <Card>
              <Statistic
                title="总账号数"
                value={accounts.length}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="今日创建"
                value={accounts.filter(a => a.created_at === new Date().toISOString().split('T')[0]).length}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={8}>
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
          <Table
            columns={columns}
            dataSource={accounts}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 个账号`
            }}
          />
        </Card>

        <GitHubAccountForm
          visible={formVisible}
          onCancel={() => setFormVisible(false)}
          onSubmit={handleFormSubmit}
          account={editingAccount}
        />

        <Modal
          title="TOTP验证码"
          open={totpModalVisible}
          onCancel={() => setTotpModalVisible(false)}
          footer={[
            <Button key="refresh" icon={<ReloadOutlined />} onClick={showTOTPBatch} loading={totpLoading}>
              刷新
            </Button>,
            <Button key="close" onClick={() => setTotpModalVisible(false)}>
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
      </Content>
    </Layout>
  );
};

export default Dashboard;