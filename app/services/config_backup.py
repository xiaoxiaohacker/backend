import logging
from datetime import datetime
import os
import hashlib
from sqlalchemy.orm import Session
from typing import List, Optional, Dict

from app.services.models import Config, Device
from app.services.schemas import ConfigCreate, ConfigOut

# 配置备份文件存储路径
CONFIG_BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config_backups')

# 确保备份目录存在
os.makedirs(CONFIG_BACKUP_DIR, exist_ok=True)

# 配置日志记录器
logger = logging.getLogger(__name__)

def create_config_backup(db: Session, config_data: ConfigCreate) -> Config:
    """创建配置备份
    
    Args:
        db: 数据库会话
        config_data: 配置备份数据
    
    Returns:
        创建的配置备份对象
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == config_data.device_id).first()
    if not device:
        logger.warning(f"设备不存在，ID: {config_data.device_id}")
        raise ValueError(f"设备不存在，ID: {config_data.device_id}")
    
    # 检查配置内容是否存在
    if not config_data.config:
        logger.warning(f"配置内容为空，无法创建备份，设备ID: {config_data.device_id}")
        raise ValueError(f"配置内容为空，无法创建备份")
    
    # 生成唯一的文件名
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"{device.id}_{timestamp}.cfg"
    filepath = os.path.join(CONFIG_BACKUP_DIR, filename)
    
    # 计算配置内容的哈希值（使用SHA-256）
    config_bytes = config_data.config.encode('utf-8')
    config_hash = hashlib.sha256(config_bytes).hexdigest()
    
    # 保存配置文件到文件系统
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(config_data.config)
        file_size = os.path.getsize(filepath)
        logger.info(f"配置文件保存成功，路径: {filepath}, 大小: {file_size} 字节")
    except Exception as e:
        logger.error(f"保存配置文件失败，设备ID: {config_data.device_id}, 错误: {str(e)}")
        raise IOError(f"保存配置文件失败: {str(e)}")
    
    # 创建配置备份记录
    db_config = Config(
        device_id=config_data.device_id,
        filename=filename,
        file_size=file_size,
        hash=config_hash,
        taken_by=config_data.taken_by,
        description=config_data.description,
        created_at=datetime.utcnow()
    )
    
    # 保存到数据库
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    logger.info(f"创建配置备份成功，设备ID: {config_data.device_id}, 备份ID: {db_config.id}")
    return db_config

def get_config_file_content(filename: str) -> Optional[str]:
    """从文件系统读取配置文件内容
    
    Args:
        filename: 配置文件名
    
    Returns:
        配置文件内容，如果文件不存在或读取失败则返回None
    """
    filepath = os.path.join(CONFIG_BACKUP_DIR, filename)
    if not os.path.exists(filepath):
        logger.warning(f"配置文件不存在，路径: {filepath}")
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"读取配置文件成功，路径: {filepath}")
        return content
    except Exception as e:
        logger.error(f"读取配置文件失败，路径: {filepath}, 错误: {str(e)}")
        return None

def get_config_backup(db: Session, config_id: int) -> Optional[Dict]:
    """获取配置备份（包含文件内容）
    
    Args:
        db: 数据库会话
        config_id: 配置备份ID
    
    Returns:
        包含配置备份信息和文件内容的字典，如果不存在则返回None
    """
    config = db.query(Config).filter(Config.id == config_id).first()
    if not config:
        return None
    
    # 读取配置文件内容
    config_content = get_config_file_content(config.filename)
    
    # 构建包含文件内容的响应
    config_dict = {
        "id": config.id,
        "device_id": config.device_id,
        "filename": config.filename,
        "file_size": config.file_size,
        "hash": config.hash,
        "content": config_content,
        "taken_by": config.taken_by,
        "description": config.description,
        "created_at": config.created_at
    }
    
    return config_dict

def get_device_config_backups(db: Session, device_id: int, limit: int = 100) -> List[Dict]:
    """获取设备的配置备份列表（仅包含元数据）
    
    Args:
        db: 数据库会话
        device_id: 设备ID
        limit: 返回的最大记录数
    
    Returns:
        配置备份元数据列表
    """
    configs = db.query(Config).filter(Config.device_id == device_id).order_by(Config.created_at.desc()).limit(limit).all()
    
    # 转换为字典列表，仅包含元数据
    config_dicts = []
    for config in configs:
        config_dict = {
            "id": config.id,
            "device_id": config.device_id,
            "filename": config.filename,
            "file_size": config.file_size,
            "hash": config.hash,
            "taken_by": config.taken_by,
            "description": config.description,
            "created_at": config.created_at
        }
        config_dicts.append(config_dict)
    
    return config_dicts

def delete_config_backup(db: Session, config_id: int) -> bool:
    """删除配置备份（同时删除文件系统中的配置文件）
    
    Args:
        db: 数据库会话
        config_id: 配置备份ID
    
    Returns:
        删除成功返回True，失败返回False
    """
    config = db.query(Config).filter(Config.id == config_id).first()
    if not config:
        logger.warning(f"配置备份不存在，ID: {config_id}")
        return False
    
    # 保存文件名，用于后续删除
    filename = config.filename
    filepath = os.path.join(CONFIG_BACKUP_DIR, filename)
    
    # 删除数据库中的记录
    db.delete(config)
    db.commit()
    
    # 删除文件系统中的配置文件
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"删除配置文件成功，路径: {filepath}")
    except Exception as e:
        logger.error(f"删除配置文件失败，路径: {filepath}, 错误: {str(e)}")
        # 即使文件删除失败，数据库记录已经删除，仍返回True
    
    logger.info(f"删除配置备份成功，ID: {config_id}")
    return True

def get_latest_config_backup(db: Session, device_id: int) -> Optional[Config]:
    """获取指定设备的最新配置备份
    
    Args:
        db: 数据库会话
        device_id: 设备ID
    
    Returns:
        最新的配置备份对象，如果不存在则返回None
    """
    return db.query(Config).filter(Config.device_id == device_id).order_by(Config.created_at.desc()).first()