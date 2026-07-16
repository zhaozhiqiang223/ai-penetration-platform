import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Tabs, 
  Form, 
  Input, 
  Button, 
  Switch, 
  Select, 
  message, 
  Typography,
  Row,
  Col,
  Statistic,
  Alert,
  Divider,
  Space,
  Modal,
  Table,
  Tag,
  Descriptions,
  Upload,
  Progress
} from 'antd';
import { 
  UserOutlined, 
  TeamOutlined, 
  SettingOutlined, 
  DatabaseOutlined,
  SecurityOutlined,
  BellOutlined,
  GlobalOutlined,
  ClusterOutlined,
  DesktopOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { systemAPI, userAPI } from '../services/api';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;

const SettingsPage = () => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('general');
  const [systemStatus, setSystemStatus] = useState({});
  const [systemStats, setSystemStats] = useState({});
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetchSystemStatus();
    fetchSystemStats();
    fetchCurrentUser();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await systemAPI.health();
      setSystemStatus(response.data);
    } catch (error) {
      console.error('获取系统状态失败:', error);
    }
  };

  const fetchSystemStats = async () => {
    try {
      const response = await systemAPI.info();
      setSystemStats(response.data);
    } catch (error) {
      console.error('获取系统统计信息失败:', error);
    }
  };

  const fetchCurrentUser = async () => {
    try {
      const response = await userAPI.getCurrentUser();
      setUser(response.data);
    } catch (error) {
      console.error('获取当前用户信息失败:', error);
    }
  };

  const generalSettingsForm = {
    initialValues: {
      siteName: 'AI自动化渗透测试平台',
      siteDescription: '智能安全评估，自动化渗透测试',
      language: 'zh-CN',
      theme: 'light',
      maintenanceMode: false,
      registrationEnabled: true,
      emailNotifications: true,
      smsNotifications: false
    }
  };

  const securitySettingsForm = {
    initialValues: {
      passwordPolicy: 'strong',
      sessionTimeout: 3600,
      maxLoginAttempts: 5,
      accountLockoutDuration: 900,
      enableTwoFactor: true,
      enableSSO: false,
      enableAPIKeyAuth: true,
      enableIPWhitelist: false,
      allowedIPs: []
    }
  };

  const scanSettingsForm = {
    initialValues: {
      maxConcurrentScans: 10,
      defaultTimeout: 3600,
      maxScanDuration: 7200,
      enableAIScanning: true,
      enableRealTimeMonitoring: true,
      scanResultRetention: 30,
      logRetention: 90,
      enableAutoRemediation: false
    }
  };

  const backupSettingsForm = {
    initialValues: {
      autoBackupEnabled: true,
      backupFrequency: 'daily',
      backupRetention: 7,
      backupLocation: '/var/backups',
      enableCompression: true,
      enableEncryption: false
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>系统设置</Title>
        <Text type="secondary">配置系统参数和安全设置</Text>
      </div>

      {/* 系统状态卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="系统状态"
              value={systemStatus.status === 'healthy' ? '正常' : '异常'}
              prefix={systemStatus.status === 'healthy' ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
              valueStyle={{ color: systemStatus.status === 'healthy' ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="运行时间"
              value={systemStatus.uptime || 0}
              suffix="天"
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="API调用"
              value={systemStats.api_calls || 0}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={systemStats.active_users || 0}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="常规设置" key="general">
            <Form
              {...generalSettingsForm}
              layout="vertical"
              onFinish={(values) => {
                message.success('设置已保存');
              }}
            >
              <Form.Item
                name="siteName"
                label="站点名称"
                rules={[{ required: true, message: '请输入站点名称' }]}
              >
                <Input placeholder="请输入站点名称" />
              </Form.Item>

              <Form.Item
                name="siteDescription"
                label="站点描述"
                rules={[{ required: true, message: '请输入站点描述' }]}
              >
                <Input.TextArea 
                  placeholder="请输入站点描述" 
                  rows={3}
                />
              </Form.Item>

              <Form.Item
                name="language"
                label="默认语言"
                rules={[{ required: true, message: '请选择默认语言' }]}
              >
                <Select placeholder="请选择默认语言">
                  <Option value="zh-CN">中文</Option>
                  <Option value="en-US">English</Option>
                  <Option value="ja-JP">日本語</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="theme"
                label="默认主题"
                rules={[{ required: true, message: '请选择默认主题' }]}
              >
                <Select placeholder="请选择默认主题">
                  <Option value="light">浅色</Option>
                  <Option value="dark">深色</Option>
                  <Option value="auto">自动</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="maintenanceMode"
                label="维护模式"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="registrationEnabled"
                label="允许注册"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="emailNotifications"
                label="邮件通知"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="smsNotifications"
                label="短信通知"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit">
                  保存设置
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab="安全设置" key="security">
            <Form
              {...securitySettingsForm}
              layout="vertical"
              onFinish={(values) => {
                message.success('安全设置已保存');
              }}
            >
              <Form.Item
                name="passwordPolicy"
                label="密码策略"
                rules={[{ required: true, message: '请选择密码策略' }]}
              >
                <Select placeholder="请选择密码策略">
                  <Option value="weak">弱密码</Option>
                  <Option value="medium">中等密码</Option>
                  <Option value="strong">强密码</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="sessionTimeout"
                label="会话超时（秒）"
                rules={[{ required: true, message: '请输入会话超时时间' }]}
              >
                <Input type="number" placeholder="请输入会话超时时间" />
              </Form.Item>

              <Form.Item
                name="maxLoginAttempts"
                label="最大登录尝试次数"
                rules={[{ required: true, message: '请输入最大登录尝试次数' }]}
              >
                <Input type="number" placeholder="请输入最大登录尝试次数" />
              </Form.Item>

              <Form.Item
                name="accountLockoutDuration"
                label="账户锁定时长（秒）"
                rules={[{ required: true, message: '请输入账户锁定时长' }]}
              >
                <Input type="number" placeholder="请输入账户锁定时长" />
              </Form.Item>

              <Form.Item
                name="enableTwoFactor"
                label="启用双因素认证"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="enableSSO"
                label="启用单点登录"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="enableAPIKeyAuth"
                label="启用API密钥认证"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="enableIPWhitelist"
                label="启用IP白名单"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              {securitySettingsForm.initialValues.enableIPWhitelist && (
                <Form.Item
                  name="allowedIPs"
                  label="允许的IP地址"
                >
                  <Input.TextArea 
                    placeholder="请输入允许的IP地址，每行一个" 
                    rows={4}
                  />
                </Form.Item>
              )}

              <Form.Item>
                <Button type="primary" htmlType="submit">
                  保存设置
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab="扫描设置" key="scan">
            <Form
              {...scanSettingsForm}
              layout="vertical"
              onFinish={(values) => {
                message.success('扫描设置已保存');
              }}
            >
              <Form.Item
                name="maxConcurrentScans"
                label="最大并发扫描数"
                rules={[{ required: true, message: '请输入最大并发扫描数' }]}
              >
                <Input type="number" placeholder="请输入最大并发扫描数" />
              </Form.Item>

              <Form.Item
                name="defaultTimeout"
                label="默认超时时间（秒）"
                rules={[{ required: true, message: '请输入默认超时时间' }]}
              >
                <Input type="number" placeholder="请输入默认超时时间" />
              </Form.Item>

              <Form.Item
                name="maxScanDuration"
                label="最大扫描时长（秒）"
                rules={[{ required: true, message: '请输入最大扫描时长' }]}
              >
                <Input type="number" placeholder="请输入最大扫描时长" />
              </Form.Item>

              <Form.Item
                name="enableAIScanning"
                label="启用AI扫描"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="enableRealTimeMonitoring"
                label="启用实时监控"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="scanResultRetention"
                label="扫描结果保留期（天）"
                rules={[{ required: true, message: '请输入扫描结果保留期' }]}
              >
                <Input type="number" placeholder="请输入扫描结果保留期" />
              </Form.Item>

              <Form.Item
                name="logRetention"
                label="日志保留期（天）"
                rules={[{ required: true, message: '请输入日志保留期' }]}
              >
                <Input type="number" placeholder="请输入日志保留期" />
              </Form.Item>

              <Form.Item
                name="enableAutoRemediation"
                label="启用自动修复"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit">
                  保存设置
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab="备份设置" key="backup">
            <Form
              {...backupSettingsForm}
              layout="vertical"
              onFinish={(values) => {
                message.success('备份设置已保存');
              }}
            >
              <Form.Item
                name="autoBackupEnabled"
                label="启用自动备份"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              {backupSettingsForm.initialValues.autoBackupEnabled && (
                <>
                  <Form.Item
                    name="backupFrequency"
                    label="备份频率"
                    rules={[{ required: true, message: '请选择备份频率' }]}
                  >
                    <Select placeholder="请选择备份频率">
                      <Option value="hourly">每小时</Option>
                      <Option value="daily">每天</Option>
                      <Option value="weekly">每周</Option>
                      <Option value="monthly">每月</Option>
                    </Select>
                  </Form.Item>

                  <Form.Item
                    name="backupRetention"
                    label="备份保留期（天）"
                    rules={[{ required: true, message: '请输入备份保留期' }]}
                  >
                    <Input type="number" placeholder="请输入备份保留期" />
                  </Form.Item>

                  <Form.Item
                    name="backupLocation"
                    label="备份位置"
                    rules={[{ required: true, message: '请输入备份位置' }]}
                  >
                    <Input placeholder="请输入备份位置" />
                  </Form.Item>

                  <Form.Item
                    name="enableCompression"
                    label="启用压缩"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>

                  <Form.Item
                    name="enableEncryption"
                    label="启用加密"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </>
              )}

              <Form.Item>
                <Button type="primary" htmlType="submit">
                  保存设置
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab="系统信息" key="info">
            <div>
              <Title level={4}>系统概览</Title>
              <Descriptions column={2}>
                <Descriptions.Item label="系统版本">{systemStats.version || '1.0.0'}</Descriptions.Item>
                <Descriptions.Item label="构建时间">{systemStats.build_time || 'N/A'}</Descriptions.Item>
                <Descriptions.Item label="运行时间">{systemStatus.uptime || 0} 天</Descriptions.Item>
                <Descriptions.Item label="内存使用">{systemStatus.memory_usage || 'N/A'}</Descriptions.Item>
                <Descriptions.Item label="CPU使用">{systemStatus.cpu_usage || 'N/A'}</Descriptions.Item>
                <Descriptions.Item label="磁盘使用">{systemStatus.disk_usage || 'N/A'}</Descriptions.Item>
              </Descriptions>

              <Divider />

              <Title level={4}>API统计</Title>
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="总调用次数"
                      value={systemStats.api_calls || 0}
                      prefix={<BarChartOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="成功调用"
                      value={systemStats.successful_calls || 0}
                      prefix={<CheckCircleOutlined />}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="失败调用"
                      value={systemStats.failed_calls || 0}
                      prefix={<ExclamationCircleOutlined />}
                      valueStyle={{ color: '#ff4d4f' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="平均响应时间"
                      value={systemStats.avg_response_time || 0}
                      suffix="ms"
                      prefix={<ClockCircleOutlined />}
                    />
                  </Card>
                </Col>
              </Row>

              <Divider />

              <Title level={4}>数据库信息</Title>
              <Descriptions column={2}>
                <Descriptions.Item label="数据库类型">{systemStats.database_type || 'PostgreSQL'}</Descriptions.Item>
                <Descriptions.Item label="数据库版本">{systemStats.database_version || '13.0'}</Descriptions.Item>
                <Descriptions.Item label="连接数">{systemStats.active_connections || 0}</Descriptions.Item>
                <Descriptions.Item label="最大连接数">{systemStats.max_connections || 100}</Descriptions.Item>
                <Descriptions.Item label="查询次数">{systemStats.query_count || 0}</Descriptions.Item>
                <Descriptions.Item label="缓存命中率">{systemStats.cache_hit_rate || 0}%</Descriptions.Item>
              </Descriptions>

              <Divider />

              <Title level={4}>服务状态</Title>
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="API服务"
                      value={systemStatus.services?.api === 'running' ? '运行中' : '停止'}
                      prefix={systemStatus.services?.api === 'running' ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
                      valueStyle={{ color: systemStatus.services?.api === 'running' ? '#52c41a' : '#ff4d4f' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="数据库"
                      value={systemStatus.services?.database === 'connected' ? '已连接' : '未连接'}
                      prefix={systemStatus.services?.database === 'connected' ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
                      valueStyle={{ color: systemStatus.services?.database === 'connected' ? '#52c41a' : '#ff4d4f' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="缓存服务"
                      value={systemStatus.services?.cache === 'running' ? '运行中' : '停止'}
                      prefix={systemStatus.services?.cache === 'running' ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
                      valueStyle={{ color: systemStatus.services?.cache === 'running' ? '#52c41a' : '#ff4d4f' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="消息队列"
                      value={systemStatus.services?.queue === 'running' ? '运行中' : '停止'}
                      prefix={systemStatus.services?.queue === 'running' ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
                      valueStyle={{ color: systemStatus.services?.queue === 'running' ? '#52c41a' : '#ff4d4f' }}
                    />
                  </Card>
                </Col>
              </Row>
            </div>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default SettingsPage;