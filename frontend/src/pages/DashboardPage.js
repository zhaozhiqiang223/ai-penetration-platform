import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, Table, Tag, Button, Alert, Spin } from 'antd';
import { 
  DashboardOutlined, 
  BugOutlined, 
  CheckCircleOutlined, 
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons';
import api from '../services/api';

const DashboardPage = () => {
  const [loading, setLoading] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [recentScans, setRecentScans] = useState([]);
  const [engineStatus, setEngineStatus] = useState(null);
  const [error, setError] = useState(null);

  const columns = [
    {
      title: '扫描名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '目标',
      dataIndex: 'target_url',
      key: 'target_url',
    },
    {
      title: '类型',
      dataIndex: 'scan_type',
      key: 'scan_type',
      render: (type) => (
        <Tag color={type === 'web' ? 'blue' : type === 'mobile' ? 'green' : 'orange'}>
          {type.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusConfig = {
          pending: { color: 'default', text: '等待中', icon: <ClockCircleOutlined /> },
          running: { color: 'processing', text: '运行中', icon: <ArrowUpOutlined /> },
          completed: { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
          failed: { color: 'error', text: '失败', icon: <ExclamationCircleOutlined /> },
          cancelled: { color: 'warning', text: '已取消', icon: <ClockCircleOutlined /> },
        };
        const config = statusConfig[status] || statusConfig.pending;
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress) => (
        <Progress 
          percent={progress} 
          size="small" 
          status={progress === 100 ? 'success' : 'active'}
        />
      ),
    },
    {
      title: '发现',
      dataIndex: 'total_findings',
      key: 'total_findings',
      render: (total, record) => (
        <div>
          <div>总计: {total}</div>
          <div>
            <Tag color="red">严重: {record.critical_findings}</Tag>
            <Tag color="orange">高危: {record.high_findings}</Tag>
            <Tag color="yellow">中危: {record.medium_findings}</Tag>
            <Tag color="blue">低危: {record.low_findings}</Tag>
            <Tag color="default">提示: {record.info_findings}</Tag>
          </div>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button 
          type="link" 
          onClick={() => window.location.href = `/scans/${record.id}`}
        >
          查看详情
        </Button>
      ),
    },
  ];

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // 30秒刷新一次
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 并行获取数据
      const [dashboardRes, scansRes, engineRes] = await Promise.all([
        api.get('/dashboard'),
        api.get('/scans?limit=10&status=all'),
        api.get('/engine/status')
      ]);
      
      setDashboardData(dashboardRes.data);
      setRecentScans(scansRes.data.data || scansRes.data || []);
      setEngineStatus(engineRes.data);
      
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('获取仪表板数据失败');
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevelColor = (riskLevel) => {
    const colors = {
      critical: 'red',
      high: 'orange',
      medium: 'yellow',
      low: 'blue',
      info: 'default'
    };
    return colors[riskLevel] || 'default';
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: '20px' }}>加载仪表板数据...</div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="错误"
        description={error}
        type="error"
        showIcon
        style={{ marginBottom: '20px' }}
      />
    );
  }

  return (
    <div>
      <h1>仪表板</h1>
      
      {engineStatus && (
        <Alert
          message={`引擎状态: ${engineStatus.engine_status}`}
          description={
            engineStatus.engine_status === 'running' 
              ? `运行中 - 队列任务: ${engineStatus.queue_status?.pending_tasks || 0}, 
                 运行任务: ${engineStatus.queue_status?.running_tasks || 0}`
              : '引擎未运行'
          }
          type={engineStatus.engine_status === 'running' ? 'success' : 'warning'}
          showIcon
          style={{ marginBottom: '20px' }}
        />
      )}
      
      <Row gutter={[16, 16]} style={{ marginBottom: '20px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总扫描数"
              value={dashboardData?.total_scans || 0}
              prefix={<DashboardOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="运行中扫描"
              value={dashboardData?.running_scans || 0}
              prefix={<ArrowUpOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总发现数"
              value={dashboardData?.total_findings || 0}
              prefix={<BugOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均风险分数"
              value={dashboardData?.average_risk_score || 0}
              precision={1}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ 
                color: dashboardData?.average_risk_score > 70 ? '#f5222d' : 
                       dashboardData?.average_risk_score > 40 ? '#fa8c16' : '#52c41a'
              }}
            />
          </Card>
        </Col>
      </Row>

      {dashboardData && (
        <Row gutter={[16, 16]} style={{ marginBottom: '20px' }}>
          <Col xs={24} md={12}>
            <Card title="风险分布">
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span>严重</span>
                  <span>{dashboardData.critical_findings || 0}</span>
                </div>
                <Progress percent={(dashboardData.critical_findings / dashboardData.total_findings) * 100 || 0} 
                         strokeColor="#f5222d" />
              </div>
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span>高危</span>
                  <span>{dashboardData.high_findings || 0}</span>
                </div>
                <Progress percent={(dashboardData.high_findings / dashboardData.total_findings) * 100 || 0} 
                         strokeColor="#fa8c16" />
              </div>
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span>中危</span>
                  <span>{dashboardData.medium_findings || 0}</span>
                </div>
                <Progress percent={(dashboardData.medium_findings / dashboardData.total_findings) * 100 || 0} 
                         strokeColor="#fadb14" />
              </div>
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span>低危</span>
                  <span>{dashboardData.low_findings || 0}</span>
                </div>
                <Progress percent={(dashboardData.low_findings / dashboardData.total_findings) * 100 || 0} 
                         strokeColor="#1890ff" />
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span>提示</span>
                  <span>{dashboardData.info_findings || 0}</span>
                </div>
                <Progress percent={(dashboardData.info_findings / dashboardData.total_findings) * 100 || 0} 
                         strokeColor="#d9d9d9" />
              </div>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card title="扫描统计">
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span>成功率</span>
                  <span>{dashboardData.success_rate || 0}%</span>
                </div>
                <Progress percent={dashboardData.success_rate || 0} />
              </div>
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span>平均耗时</span>
                  <span>{dashboardData.average_duration || 0}分钟</span>
                </div>
                <Progress percent={Math.min(100, (dashboardData.average_duration || 0) / 60 * 100)} />
              </div>
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span>今日扫描</span>
                  <span>{dashboardData.today_scans || 0}</span>
                </div>
                <Progress percent={Math.min(100, (dashboardData.today_scans || 0) / 10 * 100)} />
              </div>
            </Card>
          </Col>
        </Row>
      )}

      <Card title="最近扫描" extra={
        <Button type="link" onClick={() => window.location.href = '/scans'}>
          查看全部
        </Button>
      }>
        <Table 
          columns={columns} 
          dataSource={recentScans} 
          rowKey="id"
          pagination={false}
          loading={loading}
        />
      </Card>
    </div>
  );
};

export default DashboardPage;