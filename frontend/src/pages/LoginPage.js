import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, Row, Col, Space, Alert } from 'antd';
import { UserOutlined, LockOutlined, SafetyOutlined } from '@ant-design/icons';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../services/api';

const { Title, Text } = Typography;

const LoginPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await authAPI.login(values);
      
      // 保存token
      localStorage.setItem('accessToken', response.data.access_token);
      localStorage.setItem('refreshToken', response.data.refresh_token);
      
      // 跳转到仪表板
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <Row justify="center" align="middle" style={{ width: '100%' }}>
        <Col xs={22} sm={20} md={16} lg={12} xl={8}>
          <Card 
            style={{ 
              borderRadius: '12px', 
              boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
              border: 'none'
            }}
            bodyStyle={{ padding: '40px' }}
          >
            <div style={{ textAlign: 'center', marginBottom: '32px' }}>
              <div style={{ 
                width: '80px', 
                height: '80px', 
                borderRadius: '50%', 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                margin: '0 auto 20px'
              }}>
                <SafetyOutlined style={{ fontSize: '36px', color: 'white' }} />
              </div>
              <Title level={2} style={{ margin: 0, color: '#1a1a1a' }}>
                AI渗透测试平台
              </Title>
              <Text type="secondary" style={{ fontSize: '16px', marginTop: '8px' }}>
                智能安全评估，自动化渗透测试
              </Text>
            </div>

            {error && (
              <Alert
                message="登录失败"
                description={error}
                type="error"
                showIcon
                style={{ marginBottom: '24px' }}
              />
            )}

            <Form
              name="login"
              onFinish={onFinish}
              layout="vertical"
              size="large"
            >
              <Form.Item
                name="username"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, message: '用户名至少3个字符' }
                ]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="用户名"
                  style={{ height: '48px', fontSize: '16px' }}
                />
              </Form.Item>

              <Form.Item
                name="password"
                rules={[
                  { required: true, message: '请输入密码' },
                  { min: 6, message: '密码至少6个字符' }
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="密码"
                  style={{ height: '48px', fontSize: '16px' }}
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  style={{
                    width: '100%',
                    height: '48px',
                    fontSize: '16px',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none'
                  }}
                >
                  登录
                </Button>
              </Form.Item>

              <div style={{ textAlign: 'center' }}>
                <Text type="secondary">
                  还没有账号？{' '}
                  <Link to="/register" style={{ color: '#667eea' }}>
                    立即注册
                  </Link>
                </Text>
              </div>
            </Form>

            <div style={{ 
              marginTop: '32px', 
              padding: '20px', 
              background: '#f8f9fa', 
              borderRadius: '8px',
              borderLeft: '4px solid #667eea'
            }}>
              <Text style={{ fontSize: '14px', color: '#666' }}>
                <strong>提示：</strong> 使用管理员账号登录，初始账号：admin，密码：admin123
              </Text>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default LoginPage;