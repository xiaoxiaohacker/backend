import time
import subprocess
import platform
import re
import logging
import io
import csv
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.services.db import get_db
from app.services.models import Device as DeviceModel, User, Config
from app.services.schemas import (
    DeviceCreate, 
    DeviceOut, 
    DeviceUpdate, 
    CommandRequest, 
    CommandResponse,
    ConfigCreate, 
    ConfigOut
)
from app.services.config_backup import (
    create_config_backup,
    get_config_backup,
    get_device_config_backups,
    delete_config_backup,
    get_latest_config_backup,
    CONFIG_BACKUP_DIR
)
from app.services.adapter_manager import AdapterManager
from app.services.auth import decode_access_token, authenticate_user
from app.api.v1.auth import oauth2_scheme

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/batch-import", response_model=Dict[str, Any])
def batch_import_devices(
    file: UploadFile = File(...),
    encoding: str = "utf-8",
    db: Session = Depends(get_db)
):
    """批量导入设备
    
    参数:
        file: 包含设备信息的CSV文件
        encoding: 文件编码格式，默认为utf-8
    
    返回:
        导入结果，包含成功和失败的设备数量
    
    异常:
        400: 文件格式错误或数据验证失败
        500: 服务器内部错误
    """
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="请上传CSV格式文件")
        
        # 读取CSV文件内容，支持不同编码格式
        file_content = file.file.read()
        
        # 尝试使用指定的编码格式解码文件内容
        try:
            content = file_content.decode(encoding).splitlines()
        except UnicodeDecodeError:
            # 如果指定编码失败，尝试检测BOM或常用编码
            if file_content.startswith(b'\xef\xbb\xbf'):
                content = file_content[3:].decode('utf-8').splitlines()
            elif file_content.startswith(b'\xff\xfe'):
                content = file_content.decode('utf-16le').splitlines()
            elif file_content.startswith(b'\xfe\xff'):
                content = file_content.decode('utf-16be').splitlines()
            else:
                # 尝试其他常见编码
                try:
                    content = file_content.decode('gbk').splitlines()
                except UnicodeDecodeError:
                    try:
                        content = file_content.decode('latin-1').splitlines()
                    except UnicodeDecodeError:
                        raise HTTPException(status_code=400, detail="无法解码文件内容，请检查文件编码格式")
        
        if not content:
            raise HTTPException(status_code=400, detail="CSV文件为空")
        
        # 解析CSV文件
        csv_reader = csv.reader(content)
        devices_data = list(csv_reader)
        
        # 准备结果数据
        result = {
            "total": len(devices_data),
            "success": 0,
            "failed": 0,
            "failed_devices": []
        }
        
        # 处理每台设备
        for index, device_row in enumerate(devices_data):
            try:
                # 检查行数据是否完整
                if len(device_row) < 5:
                    raise ValueError("缺少必需的字段")
                
                # 创建设备数据 - 根据用户提供的CSV文件格式说明调整字段映射
                # CSV字段顺序：1.设备名称, 2.管理IP, 3.厂商, 4.用户名, 5.密码, 6.特权密码(可选), 7.端口(可选), 8.设备型号(可选), 9.软件版本(可选), 10.序列号(可选), 11.位置(可选), 12.设备类型(可选)
                device_data = {
                    "name": device_row[0].strip() or None,
                    "management_ip": device_row[1].strip(),
                    "vendor": device_row[2].strip(),
                    "username": device_row[3].strip(),
                    "password": device_row[4].strip(),
                    "enable_password": device_row[5].strip() or None if len(device_row) > 5 else None,  # 特权密码在第6列
                    "port": 22,  # 默认端口
                    "model": device_row[7].strip() or None if len(device_row) > 7 else None,  # 设备型号在第8列
                    "os_version": device_row[8].strip() or None if len(device_row) > 8 else None,  # 软件版本在第9列
                    "serial_number": device_row[9].strip() or None if len(device_row) > 9 else None,  # 序列号在第10列
                    "location": device_row[10].strip() or None if len(device_row) > 10 else None,  # 位置在第11列
                    "device_type": device_row[11].strip() or None if len(device_row) > 11 else None  # 设备类型在第12列
                }
                
                # 如果有端口号数据，使用它
                if len(device_row) > 6 and device_row[6].strip():
                    try:
                        device_data["port"] = int(device_row[6].strip())
                    except ValueError:
                        pass
                
                # 验证设备数据
                device_create = DeviceCreate(**device_data)
                
                # 检查IP是否已存在
                existing_device = db.query(DeviceModel).filter(
                    DeviceModel.management_ip == device_create.management_ip
                ).first()
                
                if existing_device:
                    raise ValueError(f"IP地址 {device_create.management_ip} 已存在")
                
                # 创建设备记录
                device = DeviceModel(**device_create.dict())
                db.add(device)
                db.commit()
                db.refresh(device)
                
                result["success"] += 1
                logger.info(f"成功导入设备: {device.name or device.management_ip}")
                
            except Exception as e:
                result["failed"] += 1
                result["failed_devices"].append({
                    "row": index + 1,
                    "error": str(e)
                })
                logger.error(f"导入设备失败，行号: {index + 1}, 错误: {str(e)}")
                # 回滚当前设备的事务
                db.rollback()
        
        logger.info(f"批量导入设备完成，总计: {result['total']}, 成功: {result['success']}, 失败: {result['failed']}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量导入设备时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量导入设备失败: {str(e)}")

# 执行ping命令检测设备连通性
def ping_host(ip: str) -> dict:
    """执行ping命令检测设备连通性
    
    Args:
        ip: 设备IP地址
        
    Returns:
        dict: 包含ip、is_reachable和response_time的字典
    """
    # 根据操作系统选择ping命令参数
    param = '-n 1' if platform.system().lower() == 'windows' else '-c 1'
    
    try:
        # 执行ping命令
        if platform.system().lower() == 'windows':
            # 在Windows上，整个命令作为一个字符串传递
            command = f'ping {param} {ip}'
            result = subprocess.run(
                command,  # 整个命令作为一个字符串
                shell=True,  # 使用shell执行
                capture_output=True,
                text=True,
                timeout=2
            )
        else:
            # 在Linux/macOS上，参数拆分成列表项
            command_parts = ['ping', param, ip]
            result = subprocess.run(
                command_parts,
                capture_output=True,
                text=True,
                timeout=2
            )
        
        # 检查ping是否成功
        is_reachable = False
        if platform.system().lower() == 'windows':
            # Windows的ping命令输出中包含"来自 xxx.xxx.xxx.xxx 的回复"表示成功
            is_reachable = "来自" in result.stdout and "的回复" in result.stdout
        else:
            # Linux/macOS使用返回码判断
            is_reachable = result.returncode == 0
        
        # 尝试提取响应时间
        response_time = None
        if is_reachable:
            # 匹配Windows和Linux/macOS的ping输出格式
            if platform.system().lower() == 'windows':
                # Windows格式: "时间<1ms" 或 "时间=32ms"
                match = re.search(r'时间[<|=](\d+)ms', result.stdout)
            else:
                # Linux/macOS格式: "time=32 ms"
                match = re.search(r'time=(\d+)\s+ms', result.stdout)
            
            if match:
                response_time = int(match.group(1))
        
        logger.debug(f"Ping {ip} 结果: 可达={is_reachable}, 响应时间={response_time}ms, 输出={result.stdout}")
        
        return {
            "ip": ip,
            "is_reachable": is_reachable,
            "response_time": response_time
        }
    except Exception as e:
        logger.error(f"Ping {ip} 失败: {str(e)}")
        return {
            "ip": ip,
            "is_reachable": False,
            "response_time": None
        }


@router.get("/check-connectivity", response_model=dict)
def check_connectivity(
    request: Request
):
    """检查设备连通性
    
    返回:
        包含ip、is_reachable和response_time的字典
    
    异常:
        500: 检查失败
    """
    try:
        # 从查询参数中获取IP
        ip = request.query_params.get("ip")
        if not ip:
            raise HTTPException(status_code=400, detail="请提供IP地址")
            
        logger.info(f"检查设备连通性: {ip}")
        
        # 执行ping命令
        result = ping_host(ip)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查设备连通性失败: {ip}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail="检查设备连通性失败，请稍后重试")


@router.get("/", response_model=List[DeviceOut])
def get_devices(db: Session = Depends(get_db)):
    """获取所有设备列表
    
    返回:
        设备列表
    
    异常:
        500: 服务器内部错误
    """
    try:
        devices = db.query(DeviceModel).all()
        logger.debug(f"获取设备列表成功，共 {len(devices)} 台设备")
        return devices
    except Exception as e:
        logger.error(f"获取设备列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取设备列表失败，请稍后重试"
        )


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(device_id: int, db: Session = Depends(get_db)):
    """获取指定设备的详细信息
    
    参数:
        device_id: 设备ID
    
    返回:
        设备详细信息
    
    异常:
        404: 设备未找到
        500: 服务器内部错误
    """
    try:
        device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not device:
            logger.warning(f"设备未找到，ID: {device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        logger.debug(f"获取设备信息成功，ID: {device_id}")
        return device
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取设备信息失败，ID: {device_id}, 错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取设备信息失败，请稍后重试"
        )


@router.post("/", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def add_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """添加新设备
    
    参数:
        device: 设备创建数据
    
    返回:
        创建成功的设备信息
    
    异常:
        400: 不支持的厂商或IP地址已存在
        500: 服务器内部错误
    """
    try:
        # 检查厂商是否支持
        if not AdapterManager.is_vendor_supported(device.vendor):
            supported = ", ".join(AdapterManager.get_supported_vendors())
            logger.warning(f"不支持的厂商: {device.vendor}")
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的厂商: {device.vendor}，支持的厂商有: {supported}"
            )
        
        # 检查IP是否已存在
        existing_device = db.query(DeviceModel).filter(
            DeviceModel.management_ip == device.management_ip
        ).first()
        if existing_device:
            logger.warning(f"IP地址已存在: {device.management_ip}")
            raise HTTPException(status_code=400, detail="该IP地址的设备已存在")
        
        # 创建新设备
        db_device = DeviceModel(
            name=device.name,
            management_ip=device.management_ip,
            vendor=device.vendor,
            model=device.model,
            os_version=device.os_version,
            serial_number=device.serial_number,
            username=device.username,
            password=device.password,
            enable_password=device.enable_password,
            port=device.port,
            device_type=device.device_type,
            location=device.location,
            status=device.status
        )
        
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        
        logger.info(f"添加设备成功，IP: {device.management_ip}")
        return db_device
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"添加设备失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加设备失败，请稍后重试"
        )


@router.put("/{device_id}", response_model=DeviceOut)
def update_device(device_id: int, device: DeviceUpdate, db: Session = Depends(get_db)):
    """更新设备信息
    
    参数:
        device_id: 设备ID
        device: 设备更新数据
    
    返回:
        更新后的设备信息
    
    异常:
        404: 设备未找到
        400: 不支持的厂商或IP地址已被其他设备使用
        500: 服务器内部错误
    """
    try:
        db_device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not db_device:
            logger.warning(f"设备未找到，ID: {device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        # 检查厂商是否支持
        if device.vendor and not AdapterManager.is_vendor_supported(device.vendor):
            supported = ", ".join(AdapterManager.get_supported_vendors())
            logger.warning(f"不支持的厂商: {device.vendor}")
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的厂商: {device.vendor}，支持的厂商有: {supported}"
            )
        
        # 检查IP是否被其他设备使用
        if device.management_ip and device.management_ip != db_device.management_ip:
            existing_device = db.query(DeviceModel).filter(
                DeviceModel.management_ip == device.management_ip,
                DeviceModel.id != device_id
            ).first()
            if existing_device:
                logger.warning(f"IP地址已被其他设备使用: {device.management_ip}")
                raise HTTPException(status_code=400, detail="该IP地址已被其他设备使用")
        
        # 更新设备信息
        for field, value in device.dict(exclude_unset=True).items():
            if field == "password" and value is None:
                # 如果密码为None，不更新密码
                continue
            setattr(db_device, field, value)
        
        db.commit()
        db.refresh(db_device)
        
        logger.info(f"更新设备成功，ID: {device_id}")
        return db_device
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"更新设备失败，ID: {device_id}, 错误: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新设备失败，请稍后重试"
        )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: int, db: Session = Depends(get_db)):
    """删除设备
    
    参数:
        device_id: 设备ID
    
    返回:
        无
    
    异常:
        404: 设备未找到
        500: 服务器内部错误
    """
    try:
        db_device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not db_device:
            logger.warning(f"设备未找到，ID: {device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        db.delete(db_device)
        db.commit()
        
        logger.info(f"删除设备成功，ID: {device_id}")
        return None
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"删除设备失败，ID: {device_id}, 错误: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除设备失败，请稍后重试"
        )


@router.get("/{device_id}/info", response_model=Dict[str, Any])
def get_device_info(device_id: int, db: Session = Depends(get_db)):
    """获取设备详细信息（通过适配器）
    
    参数:
        device_id: 设备ID
    
    返回:
        设备详细信息
    
    异常:
        404: 设备未找到
        500: 获取设备信息失败
    """
    try:
        device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not device:
            logger.warning(f"设备未找到，ID: {device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        # 准备基本设备信息（从数据库）
        basic_info = {
            "id": device.id,
            "name": device.name,
            "management_ip": device.management_ip,
            "vendor": device.vendor,
            "model": device.model,
            "os_version": device.os_version,
            "serial_number": device.serial_number,
            "username": device.username,
            "port": device.port,
            "device_type": device.device_type,
            "location": device.location,
            "status": device.status,
            "created_at": device.created_at,
            "updated_at": device.updated_at,
            "connection_status": "disconnected",
            "info_source": "database"
        }
        
        try:
            # 尝试通过适配器连接设备获取实时信息
            device_info = {
                'management_ip': device.management_ip,
                'vendor': device.vendor,
                'username': device.username,
                'password': device.password,
                'port': device.port
            }
            
            # 如果有enable密码，也添加进去
            if device.enable_password:
                device_info['enable_password'] = device.enable_password
            
            # 创建适配器
            adapter = AdapterManager.get_adapter(device_info)
            
            # 获取设备信息
            realtime_info = adapter.get_device_info()
            adapter.disconnect()
            
            if realtime_info:
                # 合并实时信息和基本信息
                result = {**basic_info, **realtime_info}
                result["connection_status"] = "connected"
                result["info_source"] = "device"
                logger.info(f"获取设备详细信息成功，ID: {device_id}")
                return result
        except Exception as e:
            # 捕获连接或获取信息时的异常，但不中断流程
            logger.warning(f"获取设备实时信息失败，ID: {device_id}, 错误: {str(e)}")
            
        # 如果无法获取实时信息，返回数据库中的基本信息
        logger.info(f"返回数据库中的设备基本信息，ID: {device_id}")
        return basic_info
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"处理设备信息请求时出错，ID: {device_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail="获取设备信息时发生错误")


@router.get("/{device_id}/interfaces", response_model=Dict[str, List[Dict[str, Any]]])
def get_device_interfaces(device_id: int, db: Session = Depends(get_db)):
    """获取设备所有接口信息
    
    参数:
        device_id: 设备ID
    
    返回:
        接口信息列表
    
    异常:
        404: 设备未找到
        500: 获取接口信息失败
    """
    try:
        device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not device:
            logger.warning(f"设备未找到，ID: {device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        # 创建设备连接信息字典
        device_info = {
            'management_ip': device.management_ip,
            'vendor': device.vendor,
            'username': device.username,
            'password': device.password,
            'port': device.port
        }
        
        # 如果有enable密码，也添加进去
        if device.enable_password:
            device_info['enable_password'] = device.enable_password
        
        # 创建适配器
        adapter = AdapterManager.get_adapter(device_info)
        
        # 获取接口信息
        interfaces = adapter.get_interfaces()
        adapter.disconnect()
        
        if interfaces is None:
            logger.warning(f"获取接口信息失败，ID: {device_id}")
            raise HTTPException(status_code=500, detail="获取接口信息失败")
        
        logger.info(f"获取设备接口列表成功，ID: {device_id}, 共 {len(interfaces)} 个接口")
        return {"interfaces": interfaces}
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取接口信息失败，ID: {device_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/interface/{interface_name}", response_model=Dict[str, Any])
def get_device_interface_status(device_id: int, interface_name: str, db: Session = Depends(get_db)):
    """获取指定接口状态
    
    参数:
        device_id: 设备ID
        interface_name: 接口名称
    
    返回:
        接口状态信息
    
    异常:
        404: 设备未找到
        500: 获取接口状态失败
    """
    try:
        device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not device:
            logger.warning(f"设备未找到，ID: {device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        # 创建设备连接信息字典
        device_info = {
            'management_ip': device.management_ip,
            'vendor': device.vendor,
            'username': device.username,
            'password': device.password,
            'port': device.port
        }
        
        # 如果有enable密码，也添加进去
        if device.enable_password:
            device_info['enable_password'] = device.enable_password
        
        # 创建适配器
        adapter = AdapterManager.get_adapter(device_info)
        
        # 获取接口状态
        status = adapter.get_interface_status(interface_name)
        adapter.disconnect()
        
        if not status:
            logger.warning(f"获取接口 {interface_name} 状态失败，设备ID: {device_id}")
            raise HTTPException(status_code=500, detail=f"获取接口 {interface_name} 状态失败")
        
        logger.info(f"获取接口状态成功，设备ID: {device_id}, 接口: {interface_name}")
        return status
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取接口状态失败，设备ID: {device_id}, 接口: {interface_name}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/config", response_model=Dict[str, str])
def get_device_config(device_id: int, db: Session = Depends(get_db)):
    """获取设备配置
    
    参数:
        device_id: 设备ID
    
    返回:
        设备配置文本
    
    异常:
        404: 设备未找到
        500: 获取设备配置失败
    """
    try:
        device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not device:
            logger.warning(f"设备未找到，ID: {device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        logger.info(f"尝试获取设备配置，ID: {device_id}, IP: {device.management_ip}, 厂商: {device.vendor}")
        
        # 创建设备连接信息字典
        device_info = {
            'management_ip': device.management_ip,
            'vendor': device.vendor,
            'username': device.username,
            'password': device.password,
            'port': device.port
        }
        
        # 如果有enable密码，也添加进去
        if device.enable_password:
            device_info['enable_password'] = device.enable_password
        
        # 创建适配器
        adapter = AdapterManager.get_adapter(device_info)
        
        # 获取配置
        config = adapter.get_config()
        adapter.disconnect()
        
        if not config:
            logger.warning(f"获取设备配置失败，ID: {device_id}")
            raise HTTPException(status_code=500, detail="获取设备配置失败")
        
        logger.info(f"获取设备配置成功，ID: {device_id}")
        return {"config": config}
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取设备配置失败，ID: {device_id}, 错误: {str(e)}, 详细错误类型: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"获取设备配置失败: {str(e)}")


@router.post("/{device_id}/save-config", response_model=Dict[str, str])
def save_device_config(device_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """保存设备配置
    
    参数:
        device_id: 设备ID
        token: 用户访问令牌
    
    返回:
        操作结果消息
    
    异常:
        401: 无效的令牌
        404: 设备未找到
        500: 保存配置失败
    """
    try:
        device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not device:
            logger.warning(f"设备未找到，ID: {device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 创建设备连接信息字典
        device_info = {
            'management_ip': device.management_ip,
            'vendor': device.vendor,
            'username': device.username,
            'password': device.password,
            'port': device.port
        }
        
        # 如果有enable密码，也添加进去
        if device.enable_password:
            device_info['enable_password'] = device.enable_password
        
        # 创建适配器
        adapter = AdapterManager.get_adapter(device_info)
        
        # 保存配置
        result = adapter.save_config()
        adapter.disconnect()
        
        if not result:
            logger.warning(f"保存配置失败，设备ID: {device_id}")
            raise HTTPException(status_code=500, detail="保存配置失败")
        
        logger.info(f"保存设备配置成功，设备ID: {device_id}, 用户: {username}")
        return {"msg": "配置保存成功"}
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"保存配置失败，设备ID: {device_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/execute", response_model=CommandResponse)
def execute_device_command(device_id: int, command_req: CommandRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """执行设备命令
    
    参数:
        device_id: 设备ID
        command_req: 包含命令文本的请求模型
        token: 用户访问令牌
    
    返回:
        命令执行结果
    
    异常:
        401: 无效的令牌
        404: 设备未找到
        500: 命令执行失败
    """
    try:
        device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not device:
            logger.warning(f"设备未找到，ID: {device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 记录执行的命令（注意：不要记录密码等敏感信息）
        logger.info(f"用户 {username} 请求执行命令，设备ID: {device_id}, 命令: {command_req.command}")
        
        # 创建设备连接信息字典
        device_info = {
            'management_ip': device.management_ip,
            'vendor': device.vendor,
            'username': device.username,
            'password': device.password,
            'port': device.port
        }
        
        # 如果有enable密码，也添加进去
        if device.enable_password:
            device_info['enable_password'] = device.enable_password
        
        # 创建适配器
        adapter = AdapterManager.get_adapter(device_info)
        
        # 执行命令
        output = adapter.execute_command(command_req.command)
        adapter.disconnect()
        
        # 记录命令执行成功
        logger.info(f"命令执行成功，设备ID: {device_id}")
        
        from datetime import datetime
        return CommandResponse(
            command=command_req.command,
            output=output,
            success=True,
            executed_at=datetime.utcnow()
        )
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"命令执行失败，设备ID: {device_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== 配置备份相关API端点 =====

@router.post("/{device_id}/config-backup", response_model=ConfigOut)
def backup_device_config(
    device_id: int,
    config_data: ConfigCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """备份设备配置到数据库
    
    参数:
        device_id: 设备ID
        config_data: 配置备份数据
        token: 用户访问令牌
    
    返回:
        创建的配置备份对象
    
    异常:
        401: 无效的令牌
        404: 设备未找到
        500: 备份配置失败
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 检查设备是否存在
        device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not device:
            logger.warning(f"设备未找到，ID: {device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        # 确保传入的device_id与路径参数一致
        config_data.device_id = device_id
        config_data.taken_by = username
        
        # 如果配置内容为空，则从设备获取
        if not config_data.config:
            # 创建设备连接信息字典
            device_info = {
                'management_ip': device.management_ip,
                'vendor': device.vendor,
                'username': device.username,
                'password': device.password,
                'port': device.port
            }
            
            # 如果有enable密码，也添加进去
            if device.enable_password:
                device_info['enable_password'] = device.enable_password
            
            # 创建适配器
            adapter = AdapterManager.get_adapter(device_info)
            
            # 获取配置
            config = adapter.get_config()
            adapter.disconnect()
            
            if not config:
                logger.warning(f"获取设备配置失败，ID: {device_id}")
                raise HTTPException(status_code=500, detail="获取设备配置失败")
            
            config_data.config = config
        
        # 创建配置备份
        backup = create_config_backup(db, config_data)
        
        logger.info(f"备份设备配置成功，设备ID: {device_id}, 备份ID: {backup.id}, 用户: {username}")
        return backup
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"备份设备配置失败，设备ID: {device_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"备份设备配置失败: {str(e)}")

@router.get("/{device_id}/config-backups", response_model=List[ConfigOut])
def get_device_backups(
    device_id: int,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取设备的所有配置备份
    
    参数:
        device_id: 设备ID
        limit: 返回的最大记录数
    
    返回:
        配置备份列表
    
    异常:
        404: 设备未找到
        500: 获取配置备份失败
    """
    try:
        # 检查设备是否存在
        device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not device:
            logger.warning(f"设备未找到，ID: {device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        # 获取配置备份列表
        backups = get_device_config_backups(db, device_id, limit)
        
        logger.info(f"获取设备配置备份列表成功，设备ID: {device_id}, 共 {len(backups)} 条记录")
        return backups
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取设备配置备份列表失败，设备ID: {device_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置备份失败: {str(e)}")

@router.get("/config-backups/{backup_id}", response_model=ConfigOut)
def get_backup(
    backup_id: int,
    db: Session = Depends(get_db)
):
    """获取指定的配置备份
    
    参数:
        backup_id: 配置备份ID
    
    返回:
        配置备份对象
    
    异常:
        404: 配置备份未找到
        500: 获取配置备份失败
    """
    try:
        # 获取配置备份
        backup = get_config_backup(db, backup_id)
        if not backup:
            logger.warning(f"配置备份未找到，ID: {backup_id}")
            raise HTTPException(status_code=404, detail="配置备份未找到")
        
        logger.info(f"获取配置备份成功，ID: {backup_id}")
        return backup
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取配置备份失败，ID: {backup_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置备份失败: {str(e)}")

@router.delete("/config-backups/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backup(
    backup_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """删除指定的配置备份
    
    参数:
        backup_id: 配置备份ID
        token: 用户访问令牌
    
    返回:
        无
    
    异常:
        401: 无效的令牌
        404: 配置备份未找到
        500: 删除配置备份失败
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 删除配置备份
        if not delete_config_backup(db, backup_id):
            raise HTTPException(status_code=404, detail="配置备份未找到")
        
        logger.info(f"删除配置备份成功，ID: {backup_id}, 用户: {username}")
        return None
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"删除配置备份失败，ID: {backup_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除配置备份失败: {str(e)}")

@router.get("/{device_id}/config-backup/latest", response_model=ConfigOut)
def get_latest_backup(
    device_id: int,
    db: Session = Depends(get_db)
):
    """获取设备的最新配置备份
    
    参数:
        device_id: 设备ID
    
    返回:
        最新的配置备份对象
    
    异常:
        404: 设备未找到或没有配置备份
        500: 获取配置备份失败
    """
    try:
        # 检查设备是否存在
        device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not device:
            logger.warning(f"设备未找到，ID: {device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        # 获取最新的配置备份
        backup = get_latest_config_backup(db, device_id)
        if not backup:
            logger.warning(f"未找到设备的配置备份，ID: {device_id}")
            raise HTTPException(status_code=404, detail="未找到设备的配置备份")
        
        logger.info(f"获取设备最新配置备份成功，设备ID: {device_id}, 备份ID: {backup.id}")
        return backup
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取设备最新配置备份失败，设备ID: {device_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置备份失败: {str(e)}")


@router.get("/{device_id}/config/download")
def download_device_config(
    device_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """下载设备当前配置
    
    参数:
        device_id: 设备ID
        token: 用户访问令牌
    
    返回:
        设备配置文件下载流
    
    异常:
        401: 无效的令牌
        404: 设备未找到
        500: 获取设备配置失败或下载失败
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        # 检查设备是否存在
        device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if not device:
            logger.warning(f"设备未找到，ID: {device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        logger.info(f"用户 {username} 请求下载设备配置，设备ID: {device_id}, IP: {device.management_ip}")
        
        # 创建设备连接信息字典
        device_info = {
            'management_ip': device.management_ip,
            'vendor': device.vendor,
            'username': device.username,
            'password': device.password,
            'port': device.port
        }
        
        # 如果有enable密码，也添加进去
        if device.enable_password:
            device_info['enable_password'] = device.enable_password
        
        # 创建适配器
        adapter = AdapterManager.get_adapter(device_info)
        
        # 获取配置
        config = adapter.get_config()
        adapter.disconnect()
        
        if not config:
            logger.warning(f"获取设备配置失败，ID: {device_id}")
            raise HTTPException(status_code=500, detail="获取设备配置失败")
        
        # 生成下载的文件名
        from datetime import datetime
        download_filename = f"{device.name}_{device.management_ip}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cfg"
        
        logger.info(f"下载设备配置成功，设备ID: {device_id}, 文件名: {download_filename}")
        
        # 返回文件下载流
        return StreamingResponse(
            io.StringIO(config),
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={download_filename}"
            }
        )
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"下载设备配置失败，设备ID: {device_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载设备配置失败: {str(e)}")


@router.get("/config-backups/{backup_id}/download")
def download_config_backup(
    backup_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """下载配置备份文件
    
    参数:
        backup_id: 配置备份ID
        token: 用户访问令牌
    
    返回:
        配置备份文件下载流
    
    异常:
        401: 无效的令牌
        404: 配置备份未找到或文件不存在
        500: 下载配置备份文件失败
    """
    try:
        # 获取当前用户
        username = decode_access_token(token)
        if not username:
            logger.warning("无效的访问令牌")
            raise HTTPException(status_code=401, detail="无效的Token")
        
        config = db.query(Config).filter(Config.id == backup_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="配置备份不存在")
        
        filepath = os.path.join(CONFIG_BACKUP_DIR, config.filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="配置文件不存在")
        
        # 打开文件并返回文件内容
        with open(filepath, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # 获取设备名称用于文件名
        device = db.query(DeviceModel).filter(DeviceModel.id == config.device_id).first()
        device_name = device.name if device else f"device_{config.device_id}"
        
        # 生成下载的文件名
        download_filename = f"{device_name}_backup_{config.created_at.strftime('%Y%m%d_%H%M%S')}.cfg"
        
        logger.info(f"用户 {username} 下载配置备份成功，备份ID: {backup_id}, 文件名: {download_filename}")
        
        return StreamingResponse(
            io.StringIO(file_content),
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={download_filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载配置备份文件失败，ID: {backup_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载配置备份文件失败: {str(e)}")
