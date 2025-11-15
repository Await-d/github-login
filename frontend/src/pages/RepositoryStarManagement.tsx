import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  message,
  Popconfirm,
  Tag,
  Progress,
  Modal,
  Input,
  Select,
  Form,
  Checkbox,
  Descriptions,
  Statistic,
  Row,
  Col,
  Alert,
  Typography,
  Divider,
  List,
  Dropdown
} from 'antd';
import type { MenuProps } from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  ImportOutlined,
  StarOutlined,
  GithubOutlined,
  StopOutlined,
  EditOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  RocketOutlined,
  MoreOutlined
} from '@ant-design/icons';
import { repositoryStarAPI, githubAPI, githubGroupsAPI } from '../services/api';

const { TextArea } = Input;
const { Option } = Select;

interface RepositoryStarTask {
  id: number;
  repository_url: string;
  owner: string;
  repo_name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  total_accounts: number;
  starred_accounts: number;
  success_count: number;
  failed_count: number;
}

interface GitHubAccount {
  id: number;
  username: string;
  group_id?: number;
}

interface GitHubGroup {
  id: number;
  name: string;
  color: string | null;
  account_count: number;
}

interface ExecutionRecord {
  id: number;
  task_id: number;
  github_account_id: number;
  github_username: string;
  status: string;
  error_message: string | null;
  executed_at: string;
}

const RepositoryStarManagement: React.FC = () => {
  const [tasks, setTasks] = useState<RepositoryStarTask[]>([]);
  const [githubAccounts, setGithubAccounts] = useState<GitHubAccount[]>([]);
  const [groups, setGroups] = useState<GitHubGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  
  // 批量操作状态
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([]);
  const [batchExecuting, setBatchExecuting] = useState(false);
  
  // 添加任务对话框
  const [addTaskVisible, setAddTaskVisible] = useState(false);
  const [addTaskForm] = Form.useForm();
  const [addTaskLoading, setAddTaskLoading] = useState(false);

  // 编辑任务对话框
  const [editTaskVisible, setEditTaskVisible] = useState(false);
  const [editTaskForm] = Form.useForm();
  const [editTaskLoading, setEditTaskLoading] = useState(false);
  const [editingTask, setEditingTask] = useState<RepositoryStarTask | null>(null);

  // 批量导入对话框
  const [batchImportVisible, setBatchImportVisible] = useState(false);
  const [batchImportForm] = Form.useForm();
  const [batchImportLoading, setBatchImportLoading] = useState(false);
  
  // 任务详情对话框
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState<RepositoryStarTask | null>(null);
  const [executionRecords, setExecutionRecords] = useState<ExecutionRecord[]>([]);
  const [recordsLoading, setRecordsLoading] = useState(false);

  // 介绍卡片显示状态
  const [showIntro, setShowIntro] = useState(() => {
    const saved = localStorage.getItem('repo_star_intro_dismissed');
    return saved !== 'true';
  });

  const { Title, Text, Paragraph } = Typography;

  // 全选状态
  const [addTaskSelectAll, setAddTaskSelectAll] = useState(false);
  const [batchImportSelectAll, setBatchImportSelectAll] = useState(false);

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  useEffect(() => {
    loadTasks();
    loadGitHubAccounts();
    loadGroups();

    // 监听窗口大小变化
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const response = await repositoryStarAPI.getTasks();
      if (response.data.success) {
        setTasks(response.data.tasks || []);
      }
    } catch (error: any) {
      message.error('加载任务列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadGitHubAccounts = async () => {
    try {
      const response = await githubAPI.getAccounts();
      if (response.data.success) {
        setGithubAccounts(response.data.accounts || []);
      }
    } catch (error) {
      message.error('加载GitHub账号列表失败');
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

  const handleSelectByGroup = (groupId: number) => {
    const accountsInGroup = githubAccounts
      .filter(account => account.group_id === groupId)
      .map(account => account.id);
    addTaskForm.setFieldsValue({ github_account_ids: accountsInGroup });
    setAddTaskSelectAll(false);
  };

  const handleBatchImportSelectByGroup = (groupId: number) => {
    const accountsInGroup = githubAccounts
      .filter(account => account.group_id === groupId)
      .map(account => account.id);
    batchImportForm.setFieldsValue({ github_account_ids: accountsInGroup });
    setBatchImportSelectAll(false);
  };

  const handleAddTask = () => {
    addTaskForm.resetFields();
    setAddTaskSelectAll(false);
    setAddTaskVisible(true);
  };

  const handleAddTaskSelectAllChange = (checked: boolean) => {
    setAddTaskSelectAll(checked);
    if (checked) {
      // 全选所有账号
      const allAccountIds = githubAccounts.map(account => account.id);
      addTaskForm.setFieldsValue({ github_account_ids: allAccountIds });
    } else {
      // 取消全选
      addTaskForm.setFieldsValue({ github_account_ids: [] });
    }
  };

  const handleAddTaskSubmit = async () => {
    try {
      const values = await addTaskForm.validateFields();
      setAddTaskLoading(true);
      
      const response = await repositoryStarAPI.createTask({
        repository_url: values.repository_url,
        description: values.description,
        github_account_ids: values.github_account_ids || [],
        execute_immediately: values.execute_immediately || false
      });
      
      if (response.data.success) {
        message.success('任务创建成功');
        setAddTaskVisible(false);
        loadTasks();
      }
    } catch (error: any) {
      if (error.response?.data?.detail) {
        message.error(error.response.data.detail);
      } else {
        message.error('创建任务失败');
      }
    } finally {
      setAddTaskLoading(false);
    }
  };

  const handleEditTask = (task: RepositoryStarTask) => {
    setEditingTask(task);
    editTaskForm.setFieldsValue({
      repository_url: task.repository_url,
      description: task.description
    });
    setEditTaskVisible(true);
  };

  const handleEditTaskSubmit = async () => {
    try {
      const values = await editTaskForm.validateFields();
      setEditTaskLoading(true);

      const response = await repositoryStarAPI.updateTask(editingTask!.id, {
        repository_url: values.repository_url,
        description: values.description
      });

      if (response.data.success) {
        message.success('任务更新成功');
        setEditTaskVisible(false);
        setEditingTask(null);
        loadTasks();
      }
    } catch (error: any) {
      if (error.response?.data?.detail) {
        message.error(error.response.data.detail);
      } else {
        message.error('更新任务失败');
      }
    } finally {
      setEditTaskLoading(false);
    }
  };

  const handleDeleteTask = async (id: number) => {
    try {
      const response = await repositoryStarAPI.deleteTask(id);
      if (response.data.success) {
        message.success('任务删除成功');
        loadTasks();
      }
    } catch (error) {
      message.error('删除任务失败');
    }
  };

  const handleExecuteTask = async (id: number, forceExecute: boolean = false) => {
    try {
      const msgContent = forceExecute ? '正在加入队列(强制执行)...' : '正在加入队列...';
      message.loading({ content: msgContent, key: 'execute', duration: 0 });
      const response = await repositoryStarAPI.executeTask(id, { force_execute: forceExecute });

      if (response.data.success) {
        const result = response.data;

        // 检查是否有队列状态信息
        if (result.queue_status) {
          const queueStatus = result.queue_status;
          const queuePos = queueStatus.queue_position;

          let statusMsg = '';
          if (queuePos === 0) {
            statusMsg = '任务正在执行中...';
          } else if (queuePos && queuePos > 0) {
            statusMsg = `任务已加入队列，前面还有 ${queuePos} 个任务`;
          } else {
            statusMsg = '任务已加入队列';
          }

          message.success({
            content: statusMsg,
            key: 'execute',
            duration: 3
          });

          // 如果任务还在队列中，启动轮询
          if (queueStatus.status === 'pending' || queueStatus.status === 'running') {
            pollQueueStatus(id);
          }
        } else {
          // 兼���旧版本响应（无队列状态）
          message.success({
            content: `执行完成: 成功${result.success_count}个，失败${result.failed_count}个，已收藏${result.already_starred_count}个`,
            key: 'execute',
            duration: 3
          });
        }

        loadTasks();
      }
    } catch (error: any) {
      message.error({ content: '加入队列失败', key: 'execute' });
    }
  };

  // 轮询队列状态
  const pollQueueStatus = async (taskId: number) => {
    const maxAttempts = 300; // 最多轮询5分钟(每秒一次)
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await repositoryStarAPI.getQueueStatus(taskId);

        if (response.data.success && response.data.data) {
          const queueStatus = response.data.data;

          // 如果任务完成或失败，停止轮询
          if (queueStatus.status === 'completed') {
            message.success({
              content: '任务执行完成！',
              duration: 3
            });
            loadTasks();
            return;
          } else if (queueStatus.status === 'failed') {
            message.error({
              content: `任务执行失败: ${queueStatus.error || '未知错误'}`,
              duration: 5
            });
            loadTasks();
            return;
          } else if (queueStatus.status === 'cancelled') {
            message.warning({
              content: '任务已被取消',
              duration: 3
            });
            loadTasks();
            return;
          }

          // 任务还在执行中，继续轮询
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(poll, 1000); // 1秒后再次轮询
          } else {
            message.warning({
              content: '轮询超时，请手动刷新页面查看结果',
              duration: 5
            });
          }
        }
      } catch (error) {
        // 轮询出错，停止轮询
        console.error('轮询队列状态失败:', error);
      }
    };

    // 开始轮询
    setTimeout(poll, 2000); // 2秒后开始第一次轮询
  };

  const handleUnstarTask = async (id: number) => {
    try {
      message.loading({ content: '正在取消收藏...', key: 'unstar', duration: 0 });
      const response = await repositoryStarAPI.unstarTask(id);

      if (response.data.success) {
        const result = response.data;
        message.success({
          content: `取消收藏完成: 成功${result.success_count}个，失败${result.failed_count}个`,
          key: 'unstar',
          duration: 3
        });
        loadTasks();
      }
    } catch (error: any) {
      message.error({ content: '取消收藏失败', key: 'unstar' });
    }
  };

  const handleViewDetail = async (task: RepositoryStarTask) => {
    setSelectedTask(task);
    setDetailVisible(true);
    setRecordsLoading(true);
    
    try {
      const response = await repositoryStarAPI.getTaskRecords(task.id);
      if (response.data.success) {
        setExecutionRecords(response.data.records || []);
      }
    } catch (error) {
      message.error('加载执行记录失败');
    } finally {
      setRecordsLoading(false);
    }
  };

  const handleBatchImport = () => {
    batchImportForm.resetFields();
    setBatchImportSelectAll(false);
    setBatchImportVisible(true);
  };

  const handleBatchImportSelectAllChange = (checked: boolean) => {
    setBatchImportSelectAll(checked);
    if (checked) {
      // 全选所有账号
      const allAccountIds = githubAccounts.map(account => account.id);
      batchImportForm.setFieldsValue({ github_account_ids: allAccountIds });
    } else {
      // 取消全选
      batchImportForm.setFieldsValue({ github_account_ids: [] });
    }
  };

  const handleBatchExecute = async (forceExecute: boolean = false) => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要执行的任务');
      return;
    }

    Modal.confirm({
      title: forceExecute ? '确认批量强制执行' : '确认批量执行',
      content: `${forceExecute ? '强制执行将重新对所有账号执行收藏操作。' : ''}即将执行 ${selectedRowKeys.length} 个任务，确定继续吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          setBatchExecuting(true);
          const response = await repositoryStarAPI.batchExecute({
            task_ids: selectedRowKeys,
            force_execute: forceExecute
          });

          if (response.data.success) {
            message.success(response.data.message || '批量执行任务已加入队列');
            setSelectedRowKeys([]);
            loadTasks();
          }
        } catch (error: any) {
          message.error(error.response?.data?.detail || '批量执行失败');
        } finally {
          setBatchExecuting(false);
        }
      }
    });
  };

  const handleBatchImportSubmit = async () => {
    try {
      const values = await batchImportForm.validateFields();
      setBatchImportLoading(true);
      
      // 解析仓库URL列表
      const urls = values.repository_urls
        .split('\n')
        .map((url: string) => url.trim())
        .filter((url: string) => url.length > 0);
      
      if (urls.length === 0) {
        message.warning('请输入至少一个仓库URL');
        return;
      }
      
      const response = await repositoryStarAPI.batchImport({
        repository_urls: urls,
        github_account_ids: values.github_account_ids || [],
        execute_immediately: values.execute_immediately || false
      });
      
      if (response.data.success) {
        message.success(response.data.message);
        setBatchImportVisible(false);
        loadTasks();
      }
    } catch (error: any) {
      message.error('批量导入失败');
    } finally {
      setBatchImportLoading(false);
    }
  };

  const columns = [
    {
      title: '仓库',
      key: 'repository',
      render: (_: any, record: RepositoryStarTask) => (
        <Space direction="vertical" size="small">
          <a href={record.repository_url} target="_blank" rel="noopener noreferrer">
            <GithubOutlined /> {record.owner}/{record.repo_name}
          </a>
          {record.description && (
            <span style={{ fontSize: '12px', color: '#888' }}>
              {String(record.description).substring(0, 200)}
            </span>
          )}
        </Space>
      )
    },
    {
      title: '收藏进度',
      key: 'progress',
      render: (_: any, record: RepositoryStarTask) => {
        const percentage = record.total_accounts > 0 
          ? Math.round((record.starred_accounts / record.total_accounts) * 100)
          : 0;
        
        return (
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Progress 
              percent={percentage} 
              size="small"
              status={percentage === 100 ? 'success' : 'active'}
            />
            <span style={{ fontSize: '12px' }}>
              {record.starred_accounts}/{record.total_accounts} 个账号已收藏
            </span>
          </Space>
        );
      }
    },
    {
      title: '执行统计',
      key: 'stats',
      render: (_: any, record: RepositoryStarTask) => (
        <Space>
          <Tag color="success">成功: {record.success_count}</Tag>
          <Tag color="error">失败: {record.failed_count}</Tag>
        </Space>
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
      render: (_: any, record: RepositoryStarTask) => (
        <Space size={4}>
          <Button
            type="primary"
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => handleExecuteTask(record.id, false)}
            title="执行未收藏的账号"
          >
            执行
          </Button>
          <Popconfirm
            title="强制执行将重新对所有账号执行收藏操作，确定继续吗？"
            onConfirm={() => handleExecuteTask(record.id, true)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="primary"
              size="small"
              icon={<ReloadOutlined />}
              title="强制重新执行所有账号"
              style={{ backgroundColor: '#ff9800', borderColor: '#ff9800' }}
            >
              强制执行
            </Button>
          </Popconfirm>
          <Button
            size="small"
            danger
            icon={<StopOutlined />}
            onClick={() => handleUnstarTask(record.id)}
          >
            取消收藏
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditTask(record)}
          >
            编辑
          </Button>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          <Popconfirm
            title="确定要删除这个任务吗？"
            onConfirm={() => handleDeleteTask(record.id)}
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

  const recordColumns = [
    {
      title: 'GitHub账号',
      dataIndex: 'github_username',
      key: 'github_username'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig: any = {
          success: { color: 'success', text: '成功' },
          failed: { color: 'error', text: '失败' },
          already_starred: { color: 'default', text: '已收藏' },
          skipped: { color: 'warning', text: '跳过' }
        };
        const config = statusConfig[status] || { color: 'default', text: status };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      render: (text: string | null) => text ? String(text).substring(0, 500) : '-'
    },
    {
      title: '执行时间',
      dataIndex: 'executed_at',
      key: 'executed_at',
      render: (text: string) => new Date(text).toLocaleString('zh-CN')
    }
  ];

  // 移动端卡片视图渲染
  const renderMobileCard = (task: RepositoryStarTask) => {
    const percentage = task.total_accounts > 0 
      ? Math.round((task.starred_accounts / task.total_accounts) * 100)
      : 0;

    const getActionMenuItems = (record: RepositoryStarTask): MenuProps['items'] => [
      {
        key: 'execute',
        label: '执行',
        icon: <PlayCircleOutlined />,
        onClick: () => handleExecuteTask(record.id, false)
      },
      {
        key: 'force-execute',
        label: '强制执行',
        icon: <ReloadOutlined />,
        onClick: () => {
          Modal.confirm({
            title: '确认强制执行',
            content: '强制执行将重新对所有账号执行收藏操作，确定继续吗？',
            okText: '确定',
            cancelText: '取消',
            onOk: () => handleExecuteTask(record.id, true)
          });
        }
      },
      {
        key: 'unstar',
        label: '取消收藏',
        icon: <StopOutlined />,
        danger: true,
        onClick: () => handleUnstarTask(record.id)
      },
      {
        key: 'edit',
        label: '编辑',
        icon: <EditOutlined />,
        onClick: () => handleEditTask(record)
      },
      {
        key: 'detail',
        label: '详情',
        icon: <EyeOutlined />,
        onClick: () => handleViewDetail(record)
      },
      {
        key: 'delete',
        label: '删除',
        icon: <DeleteOutlined />,
        danger: true,
        onClick: () => {
          Modal.confirm({
            title: '确认删除',
            content: '确定要删除这个任务吗？',
            okText: '确定',
            cancelText: '取消',
            onOk: () => handleDeleteTask(record.id)
          });
        }
      }
    ];

    return (
      <Card 
        key={task.id}
        style={{ marginBottom: 12 }}
        size="small"
      >
        <Space direction="vertical" style={{ width: '100%' }} size="small">
          <div>
            <a 
              href={task.repository_url} 
              target="_blank" 
              rel="noopener noreferrer"
              style={{ fontSize: '14px', fontWeight: 500 }}
            >
              <GithubOutlined /> {task.owner}/{task.repo_name}
            </a>
          </div>
          
          {task.description && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {String(task.description).substring(0, 200)}
            </Text>
          )}

          <div>
            <div style={{ marginBottom: 4 }}>
              <Text style={{ fontSize: '12px' }}>
                收藏进度: {task.starred_accounts}/{task.total_accounts}
              </Text>
            </div>
            <Progress 
              percent={percentage} 
              size="small"
              status={percentage === 100 ? 'success' : 'active'}
            />
          </div>

          <Space wrap size="small">
            <Tag color="success">成功: {task.success_count}</Tag>
            <Tag color="error">失败: {task.failed_count}</Tag>
          </Space>

          <Text type="secondary" style={{ fontSize: '11px' }}>
            创建于: {new Date(task.created_at).toLocaleString('zh-CN', {
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            })}
          </Text>

          <Space wrap size="small" style={{ width: '100%' }}>
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleExecuteTask(task.id, false)}
            >
              执行
            </Button>
            <Button
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(task)}
            >
              详情
            </Button>
            <Dropdown 
              menu={{ items: getActionMenuItems(task) }}
              trigger={['click']}
            >
              <Button size="small" icon={<MoreOutlined />}>
                更多
              </Button>
            </Dropdown>
          </Space>
        </Space>
      </Card>
    );
  };

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总任务数"
              value={tasks.length}
              prefix={<StarOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已完成任务"
              value={tasks.filter(t => t.starred_accounts === t.total_accounts && t.total_accounts > 0).length}
              prefix={<StarOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="GitHub账号数"
              value={githubAccounts.length}
              prefix={<GithubOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总成功次数"
              value={tasks.reduce((sum, t) => sum + t.success_count, 0)}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 功能介绍卡片 */}
      {showIntro && (
        <Alert
          message={
            <Space>
              <RocketOutlined />
              <Text strong>GitHub仓库收藏功能介绍</Text>
            </Space>
          }
          description={
            <div>
              <Paragraph>
                批量管理GitHub仓库收藏，让多个账号快速Star您指定的仓库。
              </Paragraph>

              <Title level={5}>
                <CheckCircleOutlined /> 主要功能
              </Title>
              <List
                size="small"
                dataSource={[
                  '批量添加仓库收藏任务',
                  '选择指定的GitHub账号或分组执行',
                  '支持立即执行或稍后手动执行',
                  '查看详细的执行记录和状态',
                  '快捷跳转到GitHub仓库页面'
                ]}
                renderItem={item => (
                  <List.Item style={{ padding: '4px 0', border: 'none' }}>
                    <Text>• {item}</Text>
                  </List.Item>
                )}
              />

              <Divider style={{ margin: '12px 0' }} />

              <Title level={5}>
                <InfoCircleOutlined /> 使用步骤
              </Title>
              <List
                size="small"
                dataSource={[
                  { step: 1, text: '点击"添加任务"按钮，输入GitHub仓库URL（如：https://github.com/owner/repo）' },
                  { step: 2, text: '选择要执行收藏的GitHub账号，可按分组选择' },
                  { step: 3, text: '选择是否立即执行，或稍后点击"执行"按钮' },
                  { step: 4, text: '点击"详情"查看每个账号的执行状态和结果' }
                ]}
                renderItem={item => (
                  <List.Item style={{ padding: '4px 0', border: 'none' }}>
                    <Text>
                      <Tag color="blue">{item.step}</Tag>
                      {item.text}
                    </Text>
                  </List.Item>
                )}
              />

              <Divider style={{ margin: '12px 0' }} />

              <Space wrap>
                <Text type="secondary">
                  <StarOutlined /> 提示：点击仓库名称可快速跳转到GitHub
                </Text>
                <Text type="secondary">
                  <ImportOutlined /> 支持批量导入多个仓库URL
                </Text>
                <Text type="secondary">
                  <ReloadOutlined /> 强制执行可重新收藏已成功的账号
                </Text>
              </Space>
            </div>
          }
          type="info"
          closable
          onClose={() => {
            setShowIntro(false);
            localStorage.setItem('repo_star_intro_dismissed', 'true');
          }}
          style={{ marginBottom: 24 }}
        />
      )}

      <Card
        title={
          <Space>
            <span>仓库收藏任务列表</span>
            <Button
              type="link"
              size="small"
              icon={<GithubOutlined />}
              href="https://github.com/Await-d/github-login"
              target="_blank"
              rel="noopener noreferrer"
              style={{ padding: 0 }}
            >
              项目仓库
            </Button>
          </Space>
        }
        extra={
          <Space wrap>
            {selectedRowKeys.length > 0 && (
              <>
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={() => handleBatchExecute(false)}
                  loading={batchExecuting}
                  size={isMobile ? 'small' : 'middle'}
                >
                  批量执行 ({selectedRowKeys.length})
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => handleBatchExecute(true)}
                  loading={batchExecuting}
                  size={isMobile ? 'small' : 'middle'}
                  style={{ backgroundColor: '#ff9800', borderColor: '#ff9800', color: '#fff' }}
                >
                  强制执行 ({selectedRowKeys.length})
                </Button>
              </>
            )}
            {!showIntro && (
              <Button
                icon={<InfoCircleOutlined />}
                onClick={() => setShowIntro(true)}
                size={isMobile ? 'small' : 'middle'}
              >
                {isMobile ? '帮助' : '使用帮助'}
              </Button>
            )}
            <Button
              icon={<ImportOutlined />}
              onClick={handleBatchImport}
              size={isMobile ? 'small' : 'middle'}
            >
              {isMobile ? '导入' : '批量导入'}
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadTasks}
              loading={loading}
              size={isMobile ? 'small' : 'middle'}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAddTask}
              size={isMobile ? 'small' : 'middle'}
            >
              {isMobile ? '添加' : '添加任务'}
            </Button>
          </Space>
        }
      >
        {isMobile ? (
          // 移动端：卡片列表视图
          <div>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <ReloadOutlined spin style={{ fontSize: '24px' }} />
              </div>
            ) : tasks.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 20px', color: '#999' }}>
                <StarOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <div>暂无任务</div>
                <div style={{ fontSize: '12px', marginTop: '8px' }}>
                  点击右上角"添加"按钮创建任务
                </div>
              </div>
            ) : (
              tasks.map(task => renderMobileCard(task))
            )}
          </div>
        ) : (
          // PC端：表格视图
          <Table
            columns={columns}
            dataSource={tasks}
            rowKey="id"
            loading={loading}
            scroll={{ x: 'max-content' }}
            rowSelection={{
              selectedRowKeys,
              onChange: (selectedKeys) => setSelectedRowKeys(selectedKeys as number[]),
              selections: [
                Table.SELECTION_ALL,
                Table.SELECTION_INVERT,
                Table.SELECTION_NONE,
              ],
            }}
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: tasks.length,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 个任务`,
              onChange: (page, size) => {
                setCurrentPage(page);
                if (size !== pageSize) {
                  setPageSize(size);
                  setCurrentPage(1); // 改变页大小时重置到第一页
                }
              }
            }}
          />
        )}
      </Card>

      {/* 添加任务对话框 */}
      <Modal
        title="添加仓库收藏任务"
        open={addTaskVisible}
        onOk={handleAddTaskSubmit}
        onCancel={() => setAddTaskVisible(false)}
        confirmLoading={addTaskLoading}
        width={600}
      >
        <Form form={addTaskForm} layout="vertical">
          <Form.Item
            name="repository_url"
            label="仓库URL"
            rules={[
              { required: true, message: '请输入仓库URL' },
              { pattern: /github\.com\/[^/]+\/[^/]+/, message: '请输入有效的GitHub仓库URL' }
            ]}
          >
            <Input placeholder="https://github.com/owner/repo" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="描述/备注"
          >
            <TextArea 
              rows={3} 
              maxLength={500}
              showCount
              placeholder="可选，描述这个仓库收藏任务(最多500字)" 
            />
          </Form.Item>
          
          <Form.Item
            name="github_account_ids"
            label={
              <Space>
                <span>选择GitHub账号</span>
                <Checkbox
                  checked={addTaskSelectAll}
                  onChange={(e) => handleAddTaskSelectAllChange(e.target.checked)}
                >
                  全选
                </Checkbox>
                {groups.length > 0 && (
                  <Select
                    placeholder="按分组选择"
                    style={{ width: 150 }}
                    onChange={(value) => handleSelectByGroup(value)}
                    size="small"
                    allowClear
                  >
                    {groups.map(group => (
                      <Option key={group.id} value={group.id}>
                        <Space>
                          {group.color && (
                            <div
                              style={{
                                width: 6,
                                height: 6,
                                borderRadius: '50%',
                                backgroundColor: group.color,
                                display: 'inline-block'
                              }}
                            />
                          )}
                          <span>{group.name}</span>
                        </Space>
                      </Option>
                    ))}
                  </Select>
                )}
              </Space>
            }
          >
            <Select
              mode="multiple"
              placeholder="选择要使用的GitHub账号（可多选，不选则使用所有账号）"
              allowClear
              onChange={() => {
                // 手动修改选择时，检查是否还是全选状态
                const selectedIds = addTaskForm.getFieldValue('github_account_ids') || [];
                setAddTaskSelectAll(selectedIds.length === githubAccounts.length && githubAccounts.length > 0);
              }}
            >
              {githubAccounts.map(account => (
                <Option key={account.id} value={account.id}>
                  {account.username}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="execute_immediately"
            valuePropName="checked"
          >
            <Checkbox>立即执行（创建后立即开始收藏）</Checkbox>
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量导入对话框 */}
      <Modal
        title="批量导入仓库"
        open={batchImportVisible}
        onOk={handleBatchImportSubmit}
        onCancel={() => setBatchImportVisible(false)}
        confirmLoading={batchImportLoading}
        width={700}
      >
        <Form form={batchImportForm} layout="vertical">
          <Form.Item
            name="repository_urls"
            label="仓库URL列表"
            rules={[{ required: true, message: '请输入至少一个仓库URL' }]}
          >
            <TextArea
              rows={10}
              maxLength={10000}
              showCount
              placeholder="每行一个GitHub仓库URL，例如：&#10;https://github.com/facebook/react&#10;https://github.com/vuejs/vue&#10;https://github.com/angular/angular&#10;(最多100个仓库)"
            />
          </Form.Item>
          
          <Form.Item
            name="github_account_ids"
            label={
              <Space>
                <span>选择GitHub账号</span>
                <Checkbox
                  checked={batchImportSelectAll}
                  onChange={(e) => handleBatchImportSelectAllChange(e.target.checked)}
                >
                  全选
                </Checkbox>
                {groups.length > 0 && (
                  <Select
                    placeholder="按分组选择"
                    style={{ width: 150 }}
                    onChange={(value) => handleBatchImportSelectByGroup(value)}
                    size="small"
                    allowClear
                  >
                    {groups.map(group => (
                      <Option key={group.id} value={group.id}>
                        <Space>
                          {group.color && (
                            <div
                              style={{
                                width: 6,
                                height: 6,
                                borderRadius: '50%',
                                backgroundColor: group.color,
                                display: 'inline-block'
                              }}
                            />
                          )}
                          <span>{group.name}</span>
                        </Space>
                      </Option>
                    ))}
                  </Select>
                )}
              </Space>
            }
            rules={[{ required: true, message: '请至少选择一个GitHub账号' }]}
          >
            <Select
              mode="multiple"
              placeholder="选择要使用的GitHub账号"
              allowClear
              onChange={() => {
                // 手动修改选择时，检查是否还是全选状态
                const selectedIds = batchImportForm.getFieldValue('github_account_ids') || [];
                setBatchImportSelectAll(selectedIds.length === githubAccounts.length && githubAccounts.length > 0);
              }}
            >
              {githubAccounts.map(account => (
                <Option key={account.id} value={account.id}>
                  {account.username}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="execute_immediately"
            valuePropName="checked"
          >
            <Checkbox>立即执行（导入后立即开始收藏）</Checkbox>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑任务对话框 */}
      <Modal
        title="编辑仓库收藏任务"
        open={editTaskVisible}
        onOk={handleEditTaskSubmit}
        onCancel={() => {
          setEditTaskVisible(false);
          setEditingTask(null);
        }}
        confirmLoading={editTaskLoading}
        width={600}
      >
        <Form form={editTaskForm} layout="vertical">
          <Form.Item
            name="repository_url"
            label="仓库URL"
            rules={[{ required: true, message: '请输入GitHub仓库URL' }]}
          >
            <Input placeholder="https://github.com/owner/repo" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述/备注"
          >
            <TextArea 
              rows={3}
              maxLength={500}
              showCount
              placeholder="可选：添加任务描述或备注信息(最多500字)" 
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 任务详情对话框 */}
      <Modal
        title="任务详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>
        ]}
        width={900}
      >
        {selectedTask && (
          <div>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="仓库">
                <a href={selectedTask.repository_url} target="_blank" rel="noopener noreferrer">
                  {selectedTask.owner}/{selectedTask.repo_name}
                </a>
              </Descriptions.Item>
              <Descriptions.Item label="描述">
                {selectedTask.description || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="总账号数">
                {selectedTask.total_accounts}
              </Descriptions.Item>
              <Descriptions.Item label="已收藏账号数">
                {selectedTask.starred_accounts}
              </Descriptions.Item>
              <Descriptions.Item label="成功次数">
                <Tag color="success">{selectedTask.success_count}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="失败次数">
                <Tag color="error">{selectedTask.failed_count}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {new Date(selectedTask.created_at).toLocaleString('zh-CN')}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {new Date(selectedTask.updated_at).toLocaleString('zh-CN')}
              </Descriptions.Item>
            </Descriptions>
            
            <div style={{ marginTop: 24 }}>
              <h3>执行记录</h3>
              <Table
                columns={recordColumns}
                dataSource={executionRecords}
                rowKey="id"
                loading={recordsLoading}
                pagination={false}
                scroll={{ x: 'max-content', y: 400 }}
                size="small"
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default RepositoryStarManagement;
