import React, { useState, useEffect } from 'react';
import {
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
  Select
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ReloadOutlined,
  KeyOutlined,
  CopyOutlined,
  ImportOutlined,
  SearchOutlined,
  FilterOutlined,
  ExportOutlined
} from '@ant-design/icons';
import { githubAPI, githubGroupsAPI } from '../services/api';
import GitHubAccountForm from '../components/GitHubAccountForm';
import BatchImportModal from '../components/BatchImportModal';

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
  group_id?: number;
}

interface GitHubGroup {
  id: number;
  name: string;
  color: string | null;
  account_count: number;
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

const GitHubAccountManagement: React.FC = () => {
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

  const [singleTotpVisible, setSingleTotpVisible] = useState(false);
  const [singleTotpData, setSingleTotpData] = useState<SingleTOTPData | null>(null);
  const [singleTotpLoading, setSingleTotpLoading] = useState(false);
  const [singleTotpCountdown, setSingleTotpCountdown] = useState(0);
  const [currentTotpAccount, setCurrentTotpAccount] = useState<GitHubAccount | null>(null);

  const [searchText, setSearchText] = useState('');
  const [dateRange, setDateRange] = useState<[any, any] | null>(null);
  const [sortOrder, setSortOrder] = useState<'ascend' | 'descend' | null>('descend');

  // 分组相关状态
  const [groups, setGroups] = useState<GitHubGroup[]>([]);
  const [selectedGroupFilter, setSelectedGroupFilter] = useState<number | null>(null);

  useEffect(() => {
    loadAccounts();
    loadGroups();
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (totpModalVisible && totpData.length > 0) {
      const initialCountdown: {[key: number]: number} = {};
      totpData.forEach(item => {
        initialCountdown[item.id] = item.time_remaining;
      });
      setCountdown(initialCountdown);

      interval = setInterval(() => {
        setCountdown(prev => {
          const newCountdown = { ...prev };
          let shouldRefresh = false;

          Object.keys(newCountdown).forEach(key => {
            const id = parseInt(key);
            if (newCountdown[id] > 0) {
              newCountdown[id] -= 1;
            } else {
              shouldRefresh = true;
            }
          });

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

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (singleTotpVisible && singleTotpData) {
      interval = setInterval(() => {
        setSingleTotpCountdown(prev => {
          if (prev > 0) {
            return prev - 1;
          } else {
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

  const loadGroups = async () => {
    try {
      const response = await githubGroupsAPI.getGroups();
      if (response.data.success) {
        setGroups(response.data.groups || []);
      }
    } catch (error: any) {
      message.error('加载分组列表失败');
    }
  };

  useEffect(() => {
    let filtered = [...accounts];

    if (searchText) {
      filtered = filtered.filter(account =>
        account.username.toLowerCase().includes(searchText.toLowerCase())
      );
    }

    if (dateRange && dateRange[0] && dateRange[1]) {
      const startDate = dateRange[0].startOf('day');
      const endDate = dateRange[1].endOf('day');
      filtered = filtered.filter(account => {
        const accountDate = new Date(account.created_at);
        return accountDate >= startDate.toDate() && accountDate <= endDate.toDate();
      });
    }

    // 按分组筛选
    if (selectedGroupFilter !== null) {
      if (selectedGroupFilter === -1) {
        // 未分组
        filtered = filtered.filter(account => !account.group_id);
      } else {
        filtered = filtered.filter(account => account.group_id === selectedGroupFilter);
      }
    }

    if (sortOrder) {
      filtered.sort((a, b) => {
        const dateA = new Date(a.created_at).getTime();
        const dateB = new Date(b.created_at).getTime();
        return sortOrder === 'ascend' ? dateA - dateB : dateB - dateA;
      });
    }

    setFilteredAccounts(filtered);
  }, [accounts, searchText, dateRange, sortOrder, selectedGroupFilter]);

  const handleResetFilters = () => {
    setSearchText('');
    setDateRange(null);
    setSortOrder('descend');
    setSelectedGroupFilter(null);
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

  const handleExportAccounts = () => {
    try {
      // 获取当前筛选后的账号列表
      const exportData = filteredAccounts.map(account => ({
        用户名: account.username,
        密码: account.password || '',
        TOTP密钥: account.totp_secret || '',
        所属分组: account.group_id ? groups.find(g => g.id === account.group_id)?.name || '' : '',
        创建时间: new Date(account.created_at).toLocaleString('zh-CN'),
        更新时间: new Date(account.updated_at).toLocaleString('zh-CN')
      }));

      // 转换为CSV格式
      const headers = Object.keys(exportData[0] || {});
      const csvContent = [
        headers.join(','),
        ...exportData.map(row =>
          headers.map(header => {
            const value = row[header as keyof typeof row];
            // 处理包含逗号的字段，用引号包裹
            return value?.includes(',') ? `"${value}"` : value;
          }).join(',')
        )
      ].join('\n');

      // 创建Blob并下载
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `github_accounts_${new Date().toISOString().slice(0, 10)}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      message.success(`成功导出 ${exportData.length} 个账号`);
    } catch (error) {
      message.error('导出失败');
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
      title: '所属分组',
      key: 'group',
      render: (_: any, record: GitHubAccount) => {
        if (!record.group_id) {
          return <Text type="secondary">未分组</Text>;
        }
        const group = groups.find(g => g.id === record.group_id);
        if (!group) {
          return <Text type="secondary">未知分组</Text>;
        }
        return (
          <Space>
            {group.color && (
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: group.color,
                }}
              />
            )}
            <Text>{group.name}</Text>
          </Space>
        );
      }
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
    <div>
      <Title level={2}>GitHub账号管理</Title>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总账号数"
              value={accounts.length}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="筛选结果"
              value={filteredAccounts.length}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日创建"
              value={accounts.filter(a => a.created_at === new Date().toISOString().split('T')[0]).length}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="状态"
              value="运行中"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="账号列表"
        extra={
          <Space wrap>
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
              icon={<ExportOutlined />}
              onClick={handleExportAccounts}
              disabled={filteredAccounts.length === 0}
            >
              导出账号
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
        <div style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
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
            <Col xs={24} sm={12} md={6}>
              <Select
                placeholder="筛选分组"
                value={selectedGroupFilter}
                onChange={(value) => setSelectedGroupFilter(value)}
                style={{ width: '100%' }}
                allowClear
              >
                <Option value={-1}>未分组</Option>
                {groups.map(group => (
                  <Option key={group.id} value={group.id}>
                    <Space>
                      {group.color && (
                        <div
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            backgroundColor: group.color,
                            display: 'inline-block'
                          }}
                        />
                      )}
                      <span>{group.name}</span>
                      <span style={{ color: '#999' }}>({group.account_count})</span>
                    </Space>
                  </Option>
                ))}
              </Select>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <RangePicker
                placeholder={['开始日期', '结束日期']}
                value={dateRange}
                onChange={(dates) => setDateRange(dates)}
                style={{ width: '100%' }}
              />
            </Col>
            <Col xs={12} sm={6} md={3}>
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
            <Col xs={12} sm={6} md={3}>
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

      <GitHubAccountForm
        visible={formVisible}
        onCancel={() => setFormVisible(false)}
        onSubmit={handleFormSubmit}
        account={editingAccount}
        groups={groups}
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
        groups={groups}
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
    </div>
  );
};

export default GitHubAccountManagement;
