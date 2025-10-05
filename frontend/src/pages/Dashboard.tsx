import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  Button,
  Space,
  List,
  Tag,
  Divider,
  Alert
} from 'antd';
import {
  GithubOutlined,
  StarOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
  ArrowRightOutlined,
  RocketOutlined,
  SafetyOutlined,
  ThunderboltOutlined,
  CalendarOutlined,
  CloudOutlined,
  BulbOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { githubAPI, scheduledTasksAPI, repositoryStarAPI, apiWebsiteAPI } from '../services/api';

const { Title, Text, Paragraph } = Typography;

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    githubAccounts: 0,
    repositories: 0,
    scheduledTasks: 0,
    apiWebsites: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    try {
      const [githubRes, repoRes, tasksRes, websitesRes] = await Promise.all([
        githubAPI.getAccounts().catch(() => ({ data: { accounts: [] } })),
        repositoryStarAPI.getTasks().catch(() => ({ data: { tasks: [] } })),
        scheduledTasksAPI.getTasks().catch(() => ({ data: { tasks: [] } })),
        apiWebsiteAPI.getWebsites().catch(() => ({ data: { websites: [] } }))
      ]);

      setStats({
        githubAccounts: githubRes.data.accounts?.length || 0,
        repositories: repoRes.data.tasks?.length || 0,
        scheduledTasks: tasksRes.data.tasks?.length || 0,
        apiWebsites: websitesRes.data.websites?.length || 0
      });
    } catch (error) {
      console.error('加载统计数据失败', error);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      title: 'GitHub账号管理',
      description: '管理您的GitHub账号，查看TOTP验证码',
      icon: <GithubOutlined style={{ fontSize: 24, color: '#1890ff' }} />,
      path: '/github/accounts',
      color: '#1890ff'
    },
    {
      title: '仓库收藏管理',
      description: '批量收藏和管理GitHub仓库',
      icon: <StarOutlined style={{ fontSize: 24, color: '#faad14' }} />,
      path: '/github/repositories',
      color: '#faad14'
    },
    {
      title: '定时任务',
      description: '自动化执行GitHub OAuth登录任务',
      icon: <ClockCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />,
      path: '/automation/tasks',
      color: '#52c41a'
    },
    {
      title: 'API网站管理',
      description: '管理和测试API网站登录',
      icon: <GlobalOutlined style={{ fontSize: 24, color: '#722ed1' }} />,
      path: '/automation/websites',
      color: '#722ed1'
    }
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Space align="center" style={{ width: '100%', justifyContent: 'space-between' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              <RocketOutlined /> 仪表盘
            </Title>
            <Paragraph type="secondary" style={{ margin: '8px 0 0 0' }}>
              欢迎使用GitHub账号管理系统，这里是您的控制中心
            </Paragraph>
          </div>
          <Button
            type="primary"
            icon={<GithubOutlined />}
            href="https://github.com/Await-d/github-login"
            target="_blank"
            rel="noopener noreferrer"
            size="large"
          >
            项目仓库
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card hoverable onClick={() => navigate('/github/accounts')} style={{ cursor: 'pointer' }}>
            <Statistic
              title={
                <Space>
                  <GithubOutlined />
                  <span>GitHub账号</span>
                </Space>
              }
              value={stats.githubAccounts}
              loading={loading}
              valueStyle={{ color: '#3f8600' }}
              suffix="个"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card hoverable onClick={() => navigate('/github/repositories')} style={{ cursor: 'pointer' }}>
            <Statistic
              title={
                <Space>
                  <StarOutlined />
                  <span>仓库任务</span>
                </Space>
              }
              value={stats.repositories}
              loading={loading}
              valueStyle={{ color: '#1890ff' }}
              suffix="个"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card hoverable onClick={() => navigate('/automation/tasks')} style={{ cursor: 'pointer' }}>
            <Statistic
              title={
                <Space>
                  <ClockCircleOutlined />
                  <span>定时任务</span>
                </Space>
              }
              value={stats.scheduledTasks}
              loading={loading}
              valueStyle={{ color: '#faad14' }}
              suffix="个"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card hoverable onClick={() => navigate('/automation/websites')} style={{ cursor: 'pointer' }}>
            <Statistic
              title={
                <Space>
                  <GlobalOutlined />
                  <span>API网站</span>
                </Space>
              }
              value={stats.apiWebsites}
              loading={loading}
              valueStyle={{ color: '#722ed1' }}
              suffix="个"
            />
          </Card>
        </Col>
      </Row>

      <Card 
        title={
          <Space>
            <BulbOutlined style={{ color: '#1890ff' }} />
            <span>关于 GitHub Manager</span>
          </Space>
        }
        bordered={false}
        style={{ marginBottom: 24 }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={4} style={{ marginTop: 0 }}>
              🚀 智能账号管理与自动化平台
            </Title>
            <Paragraph>
              <Text strong>GitHub Manager</Text> 是一个企业级的GitHub账号管理和自动化平台，专为开发者和团队设计。
              通过智能化的浏览器模拟技术和强大的任务调度系统，实现GitHub账号的安全管理和第三方平台的自动化登录。
            </Paragraph>
          </div>

          <Divider style={{ margin: '12px 0' }} />

          <Row gutter={[24, 16]}>
            <Col xs={24} md={12}>
              <Title level={5}>⭐ 核心特色</Title>
              <List
                size="small"
                dataSource={[
                  { icon: <SafetyOutlined style={{ color: '#52c41a' }} />, text: '安全第一 - AES加密存储，JWT认证' },
                  { icon: <ThunderboltOutlined style={{ color: '#faad14' }} />, text: '智能自动化 - 支持反爬虫检测' },
                  { icon: <CalendarOutlined style={{ color: '#1890ff' }} />, text: '灵活调度 - Cron表达式支持' },
                  { icon: <CloudOutlined style={{ color: '#722ed1' }} />, text: '多平台支持 - 支持主流OAuth平台' }
                ]}
                renderItem={(item) => (
                  <List.Item>
                    <Space>
                      {item.icon}
                      <Text>{item.text}</Text>
                    </Space>
                  </List.Item>
                )}
              />
            </Col>
            <Col xs={24} md={12}>
              <Title level={5}>✨ 核心功能</Title>
              <List
                size="small"
                dataSource={[
                  { icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />, text: 'GitHub账号批量管理' },
                  { icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />, text: 'TOTP双因子认证' },
                  { icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />, text: 'OAuth自动登录' },
                  { icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />, text: '定时任务调度' }
                ]}
                renderItem={(item) => (
                  <List.Item>
                    <Space>
                      {item.icon}
                      <Text>{item.text}</Text>
                    </Space>
                  </List.Item>
                )}
              />
            </Col>
          </Row>

          <Divider style={{ margin: '12px 0' }} />

          <Alert
            message="开源项目"
            description={
              <Space direction="vertical">
                <Text>
                  本项目完全开源，欢迎Star、Fork和贡献代码！
                </Text>
                <Space>
                  <Button
                    type="primary"
                    icon={<GithubOutlined />}
                    href="https://github.com/Await-d/github-login"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    访问GitHub仓库
                  </Button>
                  <Button
                    icon={<StarOutlined />}
                    href="https://github.com/Await-d/github-login"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    给个Star⭐
                  </Button>
                </Space>
              </Space>
            }
            type="info"
            showIcon
          />
        </Space>
      </Card>

      <Card title="快速访问" bordered={false}>
        <List
          grid={{
            gutter: 16,
            xs: 1,
            sm: 1,
            md: 2,
            lg: 2,
            xl: 2,
            xxl: 2
          }}
          dataSource={quickActions}
          renderItem={(item) => (
            <List.Item>
              <Card
                hoverable
                onClick={() => navigate(item.path)}
                style={{
                  borderLeft: `4px solid ${item.color}`,
                  cursor: 'pointer'
                }}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Space>
                    {item.icon}
                    <Title level={4} style={{ margin: 0 }}>
                      {item.title}
                    </Title>
                  </Space>
                  <Text type="secondary">{item.description}</Text>
                  <Button type="primary" icon={<ArrowRightOutlined />} block>
                    前往
                  </Button>
                </Space>
              </Card>
            </List.Item>
          )}
        />
      </Card>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} md={12}>
          <Card title="系统信息" bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>技术栈：</Text>
                <Space>
                  <Tag color="blue">Python 3.12</Tag>
                  <Tag color="cyan">FastAPI</Tag>
                  <Tag color="geekblue">React 18</Tag>
                </Space>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>浏览器自动化：</Text>
                <Tag color="purple">Playwright</Tag>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>数据库：</Text>
                <Tag color="green">SQLite</Tag>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>UI组件库：</Text>
                <Tag color="blue">Ant Design</Tag>
              </div>
            </Space>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="功能特性" bordered={false}>
            <List
              size="small"
              dataSource={[
                '✅ GitHub账号管理与加密存储',
                '✅ TOTP二次验证码生成',
                '✅ 仓库批量收藏/取消收藏',
                '✅ OAuth自动化登录',
                '✅ 定时任务调度',
                '✅ API网站管理'
              ]}
              renderItem={(item) => <List.Item>{item}</List.Item>}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
