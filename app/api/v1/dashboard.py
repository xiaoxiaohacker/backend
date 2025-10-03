from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.db import get_db
from app.services.models import Device, InterfaceStatus
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/test", response_model=Dict[str, Any])
def test_endpoint():
    """测试端点"""
    return {"message": "测试成功"}

@router.get("/stats", response_model=Dict[str, Any])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取仪表板统计数据
    
    返回:
        仪表板统计数据
    """
    try:
        # 查询设备统计数据
        total_devices = db.query(Device).count()
        online_devices = db.query(Device).filter(Device.status == "online").count()
        offline_devices = db.query(Device).filter(Device.status == "offline").count()
        unknown_devices = db.query(Device).filter(Device.status == "unknown").count()
        warning_devices = db.query(Device).filter(Device.status == "warning").count()
        
        # 查询接口状态统计
        total_ports = db.query(InterfaceStatus).count()
        up_ports = db.query(InterfaceStatus).filter(InterfaceStatus.operational_status == "up").count()
        down_ports = db.query(InterfaceStatus).filter(InterfaceStatus.operational_status == "down").count()
        warning_ports = db.query(InterfaceStatus).filter(InterfaceStatus.operational_status == "warning").count()
        
        # 模拟用户和告警数据（这些需要根据实际模型调整）
        total_users = 5
        active_users = 3
        total_alarms = 15
        unhandled_alarms = 3
        
        # 模拟性能数据
        bandwidth_usage = 45
        cpu_usage = 30
        memory_usage = 65
        uptime = 86400
        
        stats = {
            "totalDevices": total_devices,
            "onlineDevices": online_devices,
            "offlineDevices": offline_devices,
            "unknownDevices": unknown_devices,
            "warningDevices": warning_devices,
            "totalPorts": total_ports,
            "upPorts": up_ports,
            "downPorts": down_ports,
            "warningPorts": warning_ports,
            "totalUsers": total_users,
            "activeUsers": active_users,
            "totalAlarms": total_alarms,
            "unhandledAlarms": unhandled_alarms,
            "bandwidthUsage": bandwidth_usage,
            "cpuUsage": cpu_usage,
            "memoryUsage": memory_usage,
            "uptime": uptime
        }
        
        logger.debug(f"获取仪表板统计数据成功: {stats}")
        return stats
    except Exception as e:
        logger.error(f"获取仪表板统计数据失败: {str(e)}")
        # 出错时返回模拟数据
        return {
            "totalDevices": 3,
            "onlineDevices": 2,
            "offlineDevices": 0,
            "unknownDevices": 1,
            "warningDevices": 0,
            "totalPorts": 48,
            "upPorts": 40,
            "downPorts": 8,
            "warningPorts": 0,
            "totalUsers": 1,
            "activeUsers": 1,
            "totalAlarms": 0,
            "unhandledAlarms": 0,
            "bandwidthUsage": 30,
            "cpuUsage": 20,
            "memoryUsage": 50,
            "uptime": 3600
        }

@router.get("/performance", response_model=Dict[str, Any])
def get_performance_data(db: Session = Depends(get_db)):
    """获取设备性能数据
    
    返回:
        设备性能数据
    """
    try:
        # 这里可以根据实际需求查询设备性能数据
        # 由于没有专门的性能数据模型，我们先返回模拟数据
        performance = {
            "cpu": [
                {"time": "00:00", "usage": 20},
                {"time": "04:00", "usage": 15},
                {"time": "08:00", "usage": 30},
                {"time": "12:00", "usage": 45},
                {"time": "16:00", "usage": 40},
                {"time": "20:00", "usage": 25}
            ],
            "memory": [
                {"time": "00:00", "usage": 40},
                {"time": "04:00", "usage": 35},
                {"time": "08:00", "usage": 50},
                {"time": "12:00", "usage": 70},
                {"time": "16:00", "usage": 65},
                {"time": "20:00", "usage": 55}
            ],
            "bandwidth": [
                {"time": "00:00", "in": 10, "out": 5},
                {"time": "04:00", "in": 5, "out": 2},
                {"time": "08:00", "in": 30, "out": 15},
                {"time": "12:00", "in": 50, "out": 30},
                {"time": "16:00", "in": 45, "out": 25},
                {"time": "20:00", "in": 20, "out": 10}
            ]
        }
        
        logger.debug(f"获取设备性能数据成功")
        return performance
    except Exception as e:
        logger.error(f"获取设备性能数据失败: {str(e)}")
        # 返回默认的性能数据
        return {
            "cpu": [],
            "memory": [],
            "bandwidth": []
        }

@router.get("/warnings", response_model=List[Dict[str, Any]])
def get_warning_devices(db: Session = Depends(get_db)):
    """获取警告设备信息
    
    返回:
        警告设备列表
    """
    try:
        # 查询状态为warning的设备
        warning_devices = db.query(Device).filter(Device.status == "warning").all()
        
        # 如果没有warning设备，查询unknown设备作为备选
        if not warning_devices:
            warning_devices = db.query(Device).filter(Device.status == "unknown").all()
        
        result = []
        for device in warning_devices:
            result.append({
                "id": device.id,
                "name": device.name,
                "managementIp": device.management_ip,
                "vendor": device.vendor,
                "location": device.location,
                "status": device.status,
                "updatedAt": device.updated_at.isoformat() if device.updated_at else None
            })
        
        logger.debug(f"获取警告设备信息成功，共 {len(result)} 台设备")
        return result
    except Exception as e:
        logger.error(f"获取警告设备信息失败: {str(e)}")
        return []

@router.get("/device-status", response_model=Dict[str, Any])
def get_device_status_distribution(db: Session = Depends(get_db)):
    """获取设备状态分布
    
    返回:
        设备状态分布数据
    """
    try:
        # 查询各状态的设备数量
        status_counts = {
            "online": db.query(Device).filter(Device.status == "online").count(),
            "offline": db.query(Device).filter(Device.status == "offline").count(),
            "unknown": db.query(Device).filter(Device.status == "unknown").count(),
            "warning": db.query(Device).filter(Device.status == "warning").count()
        }
        
        # 查询各厂商的设备数量
        vendor_counts = {}
        vendors = db.query(Device.vendor).distinct().all()
        for vendor in vendors:
            vendor_name = vendor[0]
            vendor_counts[vendor_name] = db.query(Device).filter(Device.vendor == vendor_name).count()
        
        # 查询各类型的设备数量
        type_counts = {}
        device_types = db.query(Device.device_type).distinct().all()
        for device_type in device_types:
            type_name = device_type[0] if device_type[0] else "Unknown"
            type_counts[type_name] = db.query(Device).filter(Device.device_type == device_type[0]).count()
        
        result = {
            "status": status_counts,
            "vendor": vendor_counts,
            "type": type_counts
        }
        
        logger.debug(f"获取设备状态分布成功: {result}")
        return result
    except Exception as e:
        logger.error(f"获取设备状态分布失败: {str(e)}")
        # 返回默认的状态分布
        return {
            "status": {"online": 0, "offline": 0, "unknown": 0, "warning": 0},
            "vendor": {},
            "type": {}
        }