import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Tag, 
  Button, 
  Progress, 
  Timeline, 
  Alert, 
  Spin, 
  Modal,
  Descriptions,
  Divider,
  List,
  Typography,
  Statistic,
  Badge
} from 'antd';
import { 
  ArrowLeftOutlined, 
  PlayCircleOutlined, 
  PauseCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  BugOutlined,
  SafetyOutlined,
  WarningOutlined
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';

const { Title, Text } = Typography;
const { Item } = Descriptions;

const ScanDetailPage = () => {
  const { scanId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [scan, setScan] = useState(null);
  const [results, setResults] = useState([]);
  const [riskAssessment, setRiskAssessment] = useState(null);
  const [logs, setLogs] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);

  useEffect(() => {
    fetchScanDetail();
  }, [scanId]);

  const fetchScanDetail = async () => {
    try {
      setLoading(true);
      const [scanRes, resultsRes, riskRes, logsRes] = await Promise.all([
        api.get(`/scans/${scanId}`),
        api.get(`/scans/${scanId}/results`),
        api.get(`/scans/${scanId}/risk-assessment`),
        api.get(`/scans/${scanId}/logs`)
      ]);
      
      setScan(scanRes.data);
      setResults(resultsRes.data.data || resultsRes.data || []);
      setRiskAssessment(riskRes.data);
      setLogs(logsRes.data.data || logsRes.data || []);
      
    } catch (err) {
      console.error('Failed to fetch scan detail:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleScanAction = async (action) => {
    try {
      setLoading(true);
      await api.post(`/scans/${scanId}/${action}`);
      fetchScanDetail();
    } catch (err) {
      console.error('Failed to scan action:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'red',
      high: 'orange',
      medium: 'yellow',
      low: 'blue',
      info: 'default'
    };
    return colors[severity] || 'default';
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      critical: <ExclamationCircleOutlined style={{ color: '#f5222d' }} />,
      high: <WarningOutlined style={{ color: '#fa8c16' }} />,
      medium: <SafetyOutlined style={{ color: '#fadb14' }} />,
      low: <SafetyOutlined style={{ color: '#1890ff' }} />,
      info: <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
    };
    return icons[severity] || <ClockCircleOutlined />;
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0秒';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}小时${minutes}分钟${secs}秒`;
    } else if (minutes > 0) {
      return `${minutes}分钟${secs}秒`;
    } else {
      return `${secs}秒`;
    }
  };

  if (loading && !scan) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: '20px' }}>加载扫描详情...</div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <Button 
          type="text" 
          icon={<ArrowLeftOutlined />} 
          onClick={() => navigate('/scans')}
          style={{ marginRight: '16px' }}
        >
          返回扫描列表
        </Button>
        <Title level={2}>{scan?.name || '扫描详情'}</Title>
      </div>

      {scan && (
        <>
          <Card title="扫描信息" style={{ marginBottom: '20px' }}>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={8}>
                <Item label="扫描状态">
                  <Tag color={
                    scan.status === 'completed' ? 'success' :
                    scan.status === 'running' ? 'processing' :
                    scan.status === 'failed' ? 'error' :
                    scan.status === 'cancelled' ? 'warning' : 'default'
                  }>
                    {scan.status === 'completed' && <CheckCircleOutlined />}
                    {scan.status === 'running' && <ReloadOutlined spin />}
                    {scan.status === 'failed' && <ExclamationCircleOutlined />}
                    {scan.status === 'cancelled' && <StopOutlined />}
                    {scan.status === 'pending' && <ClockCircleOutlined />}
                    {scan.status}
                  </Tag>
                </Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Item label="扫描类型">
                  <Tag color="blue">{scan.scan_type?.toUpperCase()}</Tag>
                </Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Item label="目标">
                  <Text>{scan.target_url || scan.target_ip}</Text>
                </Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Item label="进度">
                  <Progress 
                    percent={scan.progress || 0} 
                    size="small"
                    status={scan.progress === 100 ? 'success' : 'active'}
                  />
                </Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Item label="开始时间">
                  <Text>{scan.started_at ? new Date(scan.started_at).toLocaleString() : '未开始'}</Text>
                </Item>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Item label="耗时">
                  <Text>{formatDuration(scan.actual_duration)}</Text>
                </Item>
              </Col>
            </Row>
          </Card>

          <Card title="扫描统计" style={{ marginBottom: '20px' }}>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="总发现"
                  value={scan.total_findings || 0}
                  prefix={<BugOutlined />}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="严重"
                  value={scan.critical_findings || 0}
                  prefix={<ExclamationCircleOutlined />}
                  valueStyle={{ color: '#f5222d' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="高危"
                  value={scan.high_findings || 0}
                  prefix={<WarningOutlined />}
                  valueStyle={{ color: '#fa8c16' }}
                />
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Statistic
                  title="中危"
                  value={scan.medium_findings || 0}
                  prefix={<SafetyOutlined />}
                  valueStyle={{ color: '#fadb14' }}
                />
              </Col>
            </Row>
          </Card>

          {scan.status === 'running' && (
            <Card title="扫描控制" style={{ marginBottom: '20px' }}>
              <Row gutter={[16, 16]}>
                <Col>
                  <Button 
                    type="primary" 
                    icon={<PauseCircleOutlined />}
                    onClick={() => handleScanAction('pause')}
                    style={{ marginRight: '8px' }}
                  >
                    暂停
                  </Button>
                  <Button 
                    type="primary" 
                    icon={<StopOutlined />}
                    onClick={() => handleScanAction('cancel')}
                    style={{ marginRight: '8px' }}
                  >
                    取消
                  </Button>
                  <Button 
                    type="primary" 
                    icon={<ReloadOutlined />}
                    onClick={() => handleScanAction('restart')}
                  >
                    重启
                  </Button>
                </Col>
              </Row>
            </Card>
          )}

          {scan.status === 'completed' && riskAssessment && (
            <Card title="风险评估" style={{ marginBottom: '20px' }}>
              <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
                <Col xs={24} sm={12} md={8}>
                  <Statistic
                    title="风险分数"
                    value={riskAssessment.risk_score}
                    precision={1}
                    valueStyle={{ 
                      color: riskAssessment.risk_score > 70 ? '#f5222d' : 
                             riskAssessment.risk_score > 40 ? '#fa8c16' : '#52c41a'
                    }}
                  />
                </Col>
                <Col xs={24} sm={12} md={8}>
                  <Statistic
                    title="风险等级"
                    value={riskAssessment.risk_level}
                    valueStyle={{ 
                      color: getSeverityColor(riskAssessment.risk_level)
                    }}
                  />
                </Col>
                <Col xs={24} sm={12} md={8}>
                  <Statistic
                    title="评估时间"
                    value={new Date(riskAssessment.assessment_timestamp).toLocaleString()}
                  />
                </Col>
              </Row>
              
              <Divider />
              
              <Title level={4}>风险因素</Title>
              <List
                dataSource={riskAssessment.risk_factors}
                renderItem={(factor, index) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={getSeverityIcon(factor.severity)}
                      title={
                        <div>
                          <Tag color={getSeverityColor(factor.severity)}>
                            {factor.severity.toUpperCase()}
                          </Tag>
                          {factor.category}
                        </div>
                      }
                      description={factor.description}
                    />
                    <div>
                      <div>置信度: {(factor.confidence * 100).toFixed(1)}%</div>
                      <div>影响分数: {factor.impact_score.toFixed(1)}</div>
                      <div>可利用性: {factor.exploitability_score.toFixed(1)}</div>
                    </div>
                  </List.Item>
                )}
              />
              
              <Divider />
              
              <Title level={4}>修复建议</Title>
              <List
                dataSource={riskAssessment.recommendations}
                renderItem={(recommendation, index) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<SafetyOutlined />}
                      title={`建议 ${index + 1}`}
                      description={recommendation}
                    />
                  </List.Item>
                )}
              />
              
              <Divider />
              
              <Title level={4}>受影响组件</Title>
              <div>
                {riskAssessment.affected_components.map((component, index) => (
                  <Tag key={index} color="blue" style={{ marginRight: '8px' }}>
                    {component}
                  </Tag>
                ))}
              </div>
            </Card>
          )}

          <Card title="扫描结果" style={{ marginBottom: '20px' }}>
            <List
              dataSource={results}
              renderItem={(result, index) => (
                <List.Item
                  actions={[
                    <Button 
                      type="link" 
                      onClick={() => {
                        setIsModalVisible(true);
                        // 这里可以添加查看详情的逻辑
                      }}
                    >
                      查看详情
                    </Button>
                  ]}
                >
                  <List.Item.Meta
                    avatar={getSeverityIcon(result.severity)}
                    title={
                      <div>
                        <Tag color={getSeverityColor(result.severity)}>
                          {result.severity.toUpperCase()}
                        </Tag>
                        {result.title}
                      </div>
                    }
                    description={result.description}
                  />
                  <div>
                    <div>类型: {result.type}</div>
                    <div>置信度: {(result.confidence * 100).toFixed(1)}%</div>
                    <div>发现时间: {new Date(result.created_at).toLocaleString()}</div>
                  </div>
                </List.Item>
              )}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`
              }}
            />
          </Card>

          <Card title="扫描日志" style={{ marginBottom: '20px' }}>
            <Timeline>
              {logs.map((log, index) => (
                <Timeline.Item 
                  key={index}
                  color={log.level === 'ERROR' ? 'red' : log.level === 'WARN' ? 'orange' : 'blue'}
                >
                  <div>
                    <div style={{ marginBottom: '4px' }}>
                      <Badge color={log.level === 'ERROR' ? 'red' : log.level === 'WARN' ? 'orange' : 'blue'}>
                        {log.level}
                      </Badge>
                      <span style={{ marginLeft: '8px' }}>
                        {new Date(log.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div>{log.message}</div>
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>

          <Modal
            title="漏洞详情"
            visible={isModalVisible}
            onCancel={() => setIsModalVisible(false)}
            footer={null}
            width={800}
          >
            {results.length > 0 && (
              <div>
                <Descriptions bordered column={2}>
                  <Item label="漏洞标题">{results[0].title}</Item>
                  <Item label="漏洞类型">{results[0].type}</Item>
                  <Item label="严重程度">{results[0].severity}</Item>
                  <Item label="置信度">{(results[0].confidence * 100).toFixed(1)}%</Item>
                  <Item label="描述">{results[0].description}</Item>
                  <Item label="影响范围">{results[0].impact_scope || '未知'}</Item>
                  <Item label="利用难度">{results[0].exploit_difficulty || '未知'}</Item>
                  <Item label="业务影响">{results[0].business_impact || '未知'}</Item>
                </Descriptions>
                <Divider />
                <Title level={4}>证据</Title>
                <List
                  dataSource={results[0].evidence || []}
                  renderItem={(evidence, index) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<BugOutlined />}
                        title={`证据 ${index + 1}`}
                        description={evidence}
                      />
                    </List.Item>
                  )}
                />
              </div>
            )}
          </Modal>
        </>
      )}
    </div>
  );
};

export default ScanDetailPage;