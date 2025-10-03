import logging
import os
import io
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.services.db import get_db
from app.services.models import Device as DeviceModel, Config
from app.services.schemas import ConfigCreate, ConfigOut
from app.services.config_backup import (
    create_config_backup,
    get_config_backup,
    get_device_config_backups,
    delete_config_backup,
    get_latest_config_backup
)
from app.adapters.huawei import HuaweiAdapter
from app.adapters.h3c import H3CAdapter
from app.api.v1.auth import oauth2_scheme, decode_access_token
from app.adapters.ruijie import RuijieAdapter

# 配置备份文件存储路径
CONFIG_BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'config_backups')

# 确保备份目录存在
os.makedirs(CONFIG_BACKUP_DIR, exist_ok=True)

# 配置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=ConfigOut)
def create_backup_task(
    config_data: ConfigCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """创建配置备份任务
    
    参数:
        config_data: 配置备份数据，包含device_id和配置信息
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
        device = db.query(DeviceModel).filter(DeviceModel.id == config_data.device_id).first()
        if not device:
            logger.warning(f"设备未找到，ID: {config_data.device_id}")
            raise HTTPException(status_code=404, detail="设备未找到")
        
        # 设置操作人
        config_data.taken_by = username
        
        # 如果配置内容为空，则从设备获取
        if not config_data.config:
            try:
                # 将DeviceModel对象转换为字典，包含连接设备所需的信息
                device_info = {
                    'id': device.id,
                    'name': device.name,
                    'management_ip': device.management_ip,
                    'username': device.username,
                    'password': device.password,
                    'enable_password': device.enable_password,
                    'port': device.port,
                    'vendor': device.vendor
                    # 不硬编码protocol，让适配器根据端口自动选择
                }
                
                # 根据设备厂商创建相应的适配器
                adapter = None
                if device.vendor.lower() == 'huawei':
                    adapter = HuaweiAdapter(device_info)
                elif device.vendor.lower() == 'h3c':
                    adapter = H3CAdapter(device_info)
                elif device.vendor.lower() == 'ruijie':
                    adapter = RuijieAdapter(device_info)
                else:
                    logger.warning(f"不支持的设备厂商: {device.vendor}")
                    raise HTTPException(status_code=400, detail=f"不支持的设备厂商: {device.vendor}")
                
                # 连接设备并获取配置
                if adapter.connect():
                    logger.info(f"成功连接到设备，ID: {device.id}")
                    config_data.config = adapter.get_config()
                    adapter.disconnect()
                    logger.info(f"从设备获取配置成功，设备ID: {device.id}")
                else:
                    logger.warning(f"连接设备失败，ID: {device.id}")
                    raise HTTPException(status_code=500, detail="连接设备失败")
                
                # 如果仍然没有获取到配置，报错
                if not config_data.config:
                    logger.warning(f"从设备获取配置失败，配置内容为空，设备ID: {device.id}")
                    raise HTTPException(status_code=500, detail="从设备获取配置失败")
            except ConnectionError as ce:
                logger.error(f"连接设备失败，ID: {device.id}, 错误: {str(ce)}")
                raise HTTPException(status_code=500, detail=f"连接设备失败: {str(ce)}")
            except Exception as e:
                logger.error(f"从设备获取配置失败，ID: {device.id}, 错误: {str(e)}")
                raise HTTPException(status_code=500, detail=f"从设备获取配置失败: {str(e)}")
        
        # 创建配置备份
        backup = create_config_backup(db, config_data)
        
        logger.info(f"备份设备配置成功，设备ID: {config_data.device_id}, 备份ID: {backup.id}, 用户: {username}")
        return backup
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"备份设备配置失败，设备ID: {config_data.device_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"备份设备配置失败: {str(e)}")

@router.get("/device/{device_id}", response_model=List[ConfigOut])
def get_device_backup_tasks(
    device_id: int,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取设备的所有配置备份任务
    
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

@router.get("/{task_id}", response_model=Dict)
def get_backup_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取指定的配置备份任务（包含文件内容）
    
    参数:
        task_id: 配置备份任务ID
    
    返回:
        配置备份对象
    
    异常:
        404: 配置备份未找到
        500: 获取配置备份失败
    """
    try:
        # 获取配置备份
        backup = get_config_backup(db, task_id)
        if not backup:
            logger.warning(f"配置备份未找到，ID: {task_id}")
            raise HTTPException(status_code=404, detail="配置备份未找到")
        
        logger.info(f"获取配置备份成功，ID: {task_id}")
        return backup
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取配置备份失败，ID: {task_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置备份失败: {str(e)}")

@router.get("/{task_id}/download")
def download_config_backup(
    task_id: int,
    db: Session = Depends(get_db)
):
    """下载配置备份文件
    
    参数:
        task_id: 配置备份任务ID
    
    返回:
        配置备份文件下载流
    
    异常:
        404: 配置备份未找到或文件不存在
        500: 下载配置备份文件失败
    """
    try:
        config = db.query(Config).filter(Config.id == task_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="配置备份任务不存在")
        
        filepath = os.path.join(CONFIG_BACKUP_DIR, config.filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="配置文件不存在")
        
        # 打开文件并返回文件内容 (使用二进制模式读取，避免编码问题)
        with open(filepath, 'rb') as f:
            file_content = f.read()
        
        # 获取设备名称用于文件名
        device = db.query(DeviceModel).filter(DeviceModel.id == config.device_id).first()
        device_name = device.name if device else f"device_{config.device_id}"
        
        # 获取设备IP地址
        device_ip = device.management_ip if device and device.management_ip else "unknown_ip"
        # 生成下载的文件名（包含设备名称和IP）
        download_filename = f"{device_name}_{device_ip}_{config.created_at.strftime('%Y%m%d_%H%M%S')}.cfg"
        
        # 使用Base64编码文件名，解决非ASCII字符在HTTP头中的编码问题
        import base64
        encoded_filename = base64.b64encode(download_filename.encode('utf-8')).decode('ascii')
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载配置备份文件失败，ID: {task_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载配置备份文件失败: {str(e)}")

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backup_task(
    task_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """删除指定的配置备份任务
    
    参数:
        task_id: 配置备份任务ID
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
        if not delete_config_backup(db, task_id):
            raise HTTPException(status_code=404, detail="配置备份未找到")
        
        logger.info(f"删除配置备份成功，ID: {task_id}, 用户: {username}")
        return None
    except HTTPException:
        # 重新抛出已定义的HTTP异常
        raise
    except Exception as e:
        logger.error(f"删除配置备份失败，ID: {task_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除配置备份失败: {str(e)}")

@router.get("/device/{device_id}/latest", response_model=ConfigOut)
def get_latest_device_backup_task(
    device_id: int,
    db: Session = Depends(get_db)
):
    """获取设备的最新配置备份任务
    
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

@router.get("/", response_model=List[Dict])
def get_all_backup_tasks(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """获取所有配置备份任务列表
    
    参数:
        limit: 返回的最大记录数
        offset: 偏移量
    
    返回:
        配置备份列表，包含设备名称
    
    异常:
        500: 获取配置备份列表失败
    """
    try:
        # 查询所有配置备份并关联设备信息
        # 使用join关联Device表，获取设备名称
        query = (
            db.query(Config, DeviceModel.name.label('device_name'))
            .join(DeviceModel, Config.device_id == DeviceModel.id)
            .order_by(Config.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        results = query.all()
        
        # 构建响应列表
        backup_list = []
        for config, device_name in results:
            # 获取配置文件内容的大小单位转换
            file_size_kb = config.file_size / 1024
            
            backup_info = {
                "id": config.id,
                "device_id": config.device_id,
                "device_name": device_name,
                "filename": config.filename,
                "file_size": round(file_size_kb, 2),
                "file_size_bytes": config.file_size,
                "description": config.description,
                "created_at": config.created_at,
                "taken_by": config.taken_by
            }
            backup_list.append(backup_info)
        
        logger.info(f"获取所有配置备份列表成功，共 {len(backup_list)} 条记录")
        return backup_list
    except Exception as e:
        logger.error(f"获取所有配置备份列表失败，错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置备份列表失败: {str(e)}")