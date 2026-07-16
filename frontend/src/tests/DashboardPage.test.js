import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import DashboardPage from '../pages/DashboardPage';

// Mock the API calls
jest.mock('../services/api', () => ({
  targetAPI: {
    statistics: jest.fn(),
  },
  scanAPI: {
    list: jest.fn(),
  },
  systemAPI: {
    health: jest.fn(),
  },
}));

const mockTargetAPI = require('../services/api').targetAPI;
const mockScanAPI = require('../services/api').scanAPI;
const mockSystemAPI = require('../services/api').systemAPI;

describe('DashboardPage', () => {
  beforeEach(() => {
    // Reset mocks
    mockTargetAPI.statistics.mockClear();
    mockScanAPI.list.mockClear();
    mockSystemAPI.health.mockClear();

    // Mock successful API responses
    mockTargetAPI.statistics.mockResolvedValue({
      data: {
        total_targets: 10,
        total_scans: 25,
        total_vulnerabilities: 150,
        critical_vulnerabilities: 5,
      }
    });

    mockScanAPI.list.mockResolvedValue({
      data: {
        scans: [
          {
            id: 1,
            name: 'Web应用扫描',
            target_name: 'example.com',
            status: 'completed',
            total_findings: 10,
            critical_findings: 2,
            high_findings: 3,
            medium_findings: 4,
            low_findings: 1,
          }
        ]
      }
    });

    mockSystemAPI.health.mockResolvedValue({
      data: {
        status: 'healthy',
        services: {
          database: 'connected',
        }
      }
    });
  });

  test('renders dashboard title and description', () => {
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    expect(screen.getByText('仪表板')).toBeInTheDocument();
    expect(screen.getByText('AI自动化渗透测试平台概览')).toBeInTheDocument();
  });

  test('displays system status alert', () => {
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    expect(screen.getByText('系统状态')).toBeInTheDocument();
    expect(screen.getByText('系统运行正常，服务健康度: 100%')).toBeInTheDocument();
  });

  test('displays statistics cards', async () => {
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('目标总数')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      
      expect(screen.getByText('扫描总数')).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument();
      
      expect(screen.getByText('漏洞总数')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument();
      
      expect(screen.getByText('用户总数')).toBeInTheDocument();
      expect(screen.getByText('0')).toBeInTheDocument();
    });
  });

  test('displays recent scans table', async () => {
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('最近扫描')).toBeInTheDocument();
      expect(screen.getByText('Web应用扫描')).toBeInTheDocument();
      expect(screen.getByText('example.com')).toBeInTheDocument();
      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
    });
  });

  test('displays quick action buttons', () => {
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    expect(screen.getByText('添加目标')).toBeInTheDocument();
    expect(screen.getByText('创建扫描')).toBeInTheDocument();
    expect(screen.getByText('用户管理')).toBeInTheDocument();
    expect(screen.getByText('系统设置')).toBeInTheDocument();
  });

  test('handles API errors gracefully', async () => {
    // Mock API error
    mockTargetAPI.statistics.mockRejectedValue(new Error('API Error'));
    
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      // Should still render the page even with API errors
      expect(screen.getByText('仪表板')).toBeInTheDocument();
    });
  });
});