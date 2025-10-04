import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from datetime import datetime
import random

from app.services.db import get_db

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/statistics", response_model=Dict[str, int])
def get_alert_statistics():
    """获取告警统计信息
    
    返回: 
        不同严重性级别的告警数量统计
    """
    try:
        # 模拟告警统计数据
        # 在实际应用中，这里应该从数据库查询真实数据
        alert_types = {"Critical": random.randint(1, 5),
                      "Major": random.randint(3, 10),
                      "Minor": random.randint(5, 15),
                      "Warning": random.randint(10, 30)}
        
        total_alerts = sum(alert_types.values())
        
        result = {
            "total": total_alerts,
            **alert_types,
            "new": random.randint(5, 20),
            "acknowledged": random.randint(10, 35),
            "resolved": random.randint(20, 50)
        }
        
        logger.info(f"获取告警统计数据成功: {result}")
        return result
        
    except Exception as e:
        logger.error(f"获取告警统计数据失败: {str(e)}")
        # 返回默认的模拟数据
        return {
            "total": 85,
            "Critical": 3,
            "Major": 8,
            "Minor": 15,
            "Warning": 25,
            "new": 15,
            "acknowledged": 28,
            "resolved": 42
        }

@router.get("/", response_model=Dict[str, Any])
def get_alerts(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    search: str = Query("", description="搜索关键词"),
    severity: str = Query("all", description="告警级别过滤"),
    status: str = Query("all", description="告警状态过滤")
):
    """获取告警列表（支持分页、搜索和过滤）
    
    返回: 
        告警列表及分页信息
    """
    try:
        # 模拟告警数据
        # 在实际应用中，这里应该从数据库查询真实数据并应用过滤条件
        alert_types = ["Interface Down", "High CPU Usage", "High Memory Usage", "Link Flapping", "Configuration Changed"]
        severity_levels = ["Critical", "Major", "Minor", "Warning"]
        alert_statuses = ["New", "Acknowledged", "Resolved"]
        
        alerts = []
        total_items = 120  # 模拟总共有120条告警记录
        
        # 计算偏移量
        offset = (page - 1) * pageSize
        
        # 生成当前页的告警数据
        for i in range(offset, min(offset + pageSize, total_items)):
            hours_ago = random.randint(0, 720)  # 过去30天内的随机时间
            alert_time = (datetime.now() - datetime.timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:%M:%S")
            
            # 根据过滤条件筛选数据
            alert_severity = random.choice(severity_levels)
            alert_status = random.choice(alert_statuses)
            device_name = f"Device-{random.randint(1, 30)}"
            device_ip = f"192.168.{random.randint(1, 24)}.{random.randint(1, 254)}"
            alert_type = random.choice(alert_types)
            
            # 应用搜索过滤
            if search and search.lower() not in device_name.lower() and \
               search.lower() not in device_ip and \
               search.lower() not in alert_type.lower():
                continue
            
            # 应用严重性过滤
            if severity != "all" and alert_severity != severity:
                continue
            
            # 应用状态过滤
            if status != "all" and alert_status != status:
                continue
            
            alerts.append({
                "id": i + 1,
                "device_name": device_name,
                "device_ip": device_ip,
                "alert_type": alert_type,
                "severity": alert_severity,
                "message": f"{alert_type} detected on interface {random.choice(['GigabitEthernet1/0/1', 'GigabitEthernet1/0/2', 'GigabitEthernet1/0/3', 'Ten-GigabitEthernet1/0/1', 'FastEthernet0/1'])}",
                "timestamp": alert_time,
                "status": alert_status,
                "acknowledged_by": "admin" if alert_status == "Acknowledged" or alert_status == "Resolved" else None,
                "acknowledged_at": (datetime.now() - datetime.timedelta(hours=random.randint(1, 24))).strftime("%Y-%m-%d %H:%M:%S") if alert_status == "Acknowledged" or alert_status == "Resolved" else None,
                "resolved_by": "admin" if alert_status == "Resolved" else None,
                "resolved_at": (datetime.now() - datetime.timedelta(hours=random.randint(1, 12))).strftime("%Y-%m-%d %H:%M:%S") if alert_status == "Resolved" else None
            })
        
        # 计算总页数（考虑过滤后的实际数量）
        total_pages = (len(alerts) + pageSize - 1) // pageSize
        
        result = {
            "data": alerts,
            "pagination": {
                "page": page,
                "pageSize": pageSize,
                "total": len(alerts),
                "totalPages": total_pages
            }
        }
        
        logger.info(f"获取告警列表成功，页码: {page}, 每页数量: {pageSize}, 总记录数: {len(alerts)}")
        return result
        
    except Exception as e:
        logger.error(f"获取告警列表失败: {str(e)}")
        # 返回默认的模拟数据
        return {
            "data": [
                {
                    "id": 1,
                    "device_name": "Device-5",
                    "device_ip": "192.168.5.10",
                    "alert_type": "Interface Down",
                    "severity": "Critical",
                    "message": "Interface GigabitEthernet1/0/1 is down",
                    "timestamp": "2023-11-01 14:30:22",
                    "status": "New",
                    "acknowledged_by": None,
                    "acknowledged_at": None,
                    "resolved_by": None,
                    "resolved_at": None
                },
                {
                    "id": 2,
                    "device_name": "Device-12",
                    "device_ip": "192.168.12.15",
                    "alert_type": "High CPU Usage",
                    "severity": "Major",
                    "message": "CPU usage is 95% (threshold 90%)",
                    "timestamp": "2023-11-01 13:45:10",
                    "status": "Acknowledged",
                    "acknowledged_by": "admin",
                    "acknowledged_at": "2023-11-01 13:50:00",
                    "resolved_by": None,
                    "resolved_at": None
                },
                {
                    "id": 3,
                    "device_name": "Device-8",
                    "device_ip": "192.168.8.20",
                    "alert_type": "High Memory Usage",
                    "severity": "Minor",
                    "message": "Memory usage is 85% (threshold 80%)",
                    "timestamp": "2023-11-01 12:20:55",
                    "status": "New",
                    "acknowledged_by": None,
                    "acknowledged_at": None,
                    "resolved_by": None,
                    "resolved_at": None
                },
                {
                    "id": 4,
                    "device_name": "Device-3",
                    "device_ip": "192.168.3.5",
                    "alert_type": "Link Flapping",
                    "severity": "Major",
                    "message": "Interface Ten-GigabitEthernet1/0/1 is flapping",
                    "timestamp": "2023-11-01 11:15:30",
                    "status": "Resolved",
                    "acknowledged_by": "admin",
                    "acknowledged_at": "2023-11-01 11:20:00",
                    "resolved_by": "admin",
                    "resolved_at": "2023-11-01 11:30:00"
                },
                {
                    "id": 5,
                    "device_name": "Device-18",
                    "device_ip": "192.168.18.25",
                    "alert_type": "Configuration Changed",
                    "severity": "Warning",
                    "message": "Device configuration has been changed",
                    "timestamp": "2023-11-01 10:05:45",
                    "status": "Acknowledged",
                    "acknowledged_by": "admin",
                    "acknowledged_at": "2023-11-01 10:10:00",
                    "resolved_by": None,
                    "resolved_at": None
                }
            ],
            "pagination": {
                "page": page,
                "pageSize": pageSize,
                "total": 5,
                "totalPages": 1
            }
        }