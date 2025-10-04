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
  Col
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  ImportOutlined,
  StarOutlined,
  GithubOutlined,
  StopOutlined
} from '@ant-design/icons';
import { repositoryStarAPI, githubAPI } from '../services/api';

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
  const [loading, setLoading] = useState(false);
  
  // 添加任务对话框
  const [addTaskVisible, setAddTaskVisible] = useState(false);
  const [addTaskForm] = Form.useForm();
  const [addTaskLoading, setAddTaskLoading] = useState(false);
  
  // 批量导入对话框
  const [batchImportVisible, setBatchImportVisible] = useState(false);
  const [batchImportForm] = Form.useForm();
  const [batchImportLoading, setBatchImportLoading] = useState(false);
  
  // 任务详情对话框
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState<RepositoryStarTask | null>(null);
  const [executionRecords, setExecutionRecords] = useState<ExecutionRecord[]>([]);
  const [recordsLoading, setRecordsLoading] = useState(false);

  useEffect(() => {
    loadTasks();
    loadGitHubAccounts();
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

  const handleAddTask = () => {
    addTaskForm.resetFields();
    setAddTaskVisible(true);
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

  const handleExecuteTask = async (id: number) => {
    try {
      message.loading({ content: '正在执行收藏任务...', key: 'execute', duration: 0 });
      const response = await repositoryStarAPI.executeTask(id);

      if (response.data.success) {
        const result = response.data;
        message.success({
          content: `执行完成: 成功${result.success_count}个，失败${result.failed_count}个，已收藏${result.already_starred_count}个`,
          key: 'execute',
          duration: 3
        });
        loadTasks();
      }
    } catch (error: any) {
      message.error({ content: '执行任务失败', key: 'execute' });
    }
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
    setBatchImportVisible(true);
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
            <span style={{ fontSize: '12px', color: '#888' }}>{record.description}</span>
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
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => handleExecuteTask(record.id)}
          >
            执行
          </Button>
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
      render: (text: string | null) => text || '-'
    },
    {
      title: '执行时间',
      dataIndex: 'executed_at',
      key: 'executed_at',
      render: (text: string) => new Date(text).toLocaleString('zh-CN')
    }
  ];

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

      <Card
        title="仓库收藏任务列表"
        extra={
          <Space>
            <Button
              icon={<ImportOutlined />}
              onClick={handleBatchImport}
            >
              批量导入
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadTasks}
              loading={loading}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAddTask}
            >
              添加任务
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个任务`
          }}
        />
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
            <TextArea rows={3} placeholder="可选，描述这个仓库收藏任务" />
          </Form.Item>
          
          <Form.Item
            name="github_account_ids"
            label="选择GitHub账号"
          >
            <Select
              mode="multiple"
              placeholder="选择要使用的GitHub账号（可多选）"
              allowClear
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
              placeholder="每行一个GitHub仓库URL，例如：&#10;https://github.com/facebook/react&#10;https://github.com/vuejs/vue&#10;https://github.com/angular/angular"
            />
          </Form.Item>
          
          <Form.Item
            name="github_account_ids"
            label="选择GitHub账号"
            rules={[{ required: true, message: '请至少选择一个GitHub账号' }]}
          >
            <Select
              mode="multiple"
              placeholder="选择要使用的GitHub账号"
              allowClear
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
                pagination={{ pageSize: 5 }}
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
