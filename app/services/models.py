from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.services.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)  # 设备名称
    management_ip = Column(String(50), unique=True, nullable=False)
    vendor = Column(String(50), nullable=False)  # 厂商：huawei, h3c, ruijie
    model = Column(String(50), nullable=True)  # 设备型号
    os_version = Column(String(100), nullable=True)  # 操作系统版本
    serial_number = Column(String(100), nullable=True)  # 序列号
    username = Column(String(50), nullable=False)
    password = Column(String(100), nullable=False)
    enable_password = Column(String(100), nullable=True)  # enable密码
    port = Column(Integer, default=22)
    device_type = Column(String(50), nullable=True)  # 设备类型：switch, router等
    location = Column(String(255), nullable=True)  # 设备位置
    status = Column(String(20), default="unknown")  # 设备状态：online, offline, unknown
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Config(Base):
    __tablename__ = "configs"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    filename = Column(String(255), nullable=False)  # 配置文件路径
    file_size = Column(Integer, nullable=False)  # 文件大小
    hash = Column(String(64), nullable=False)  # 文件哈希值
    taken_by = Column(String(50), nullable=True)
    description = Column(String(255), nullable=True)  # 配置描述
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class InterfaceStatus(Base):
    __tablename__ = "interface_status"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    interface_name = Column(String(100), nullable=False)
    admin_status = Column(String(20), nullable=True)  # up, down
    operational_status = Column(String(20), nullable=True)  # up, down
    mac_address = Column(String(50), nullable=True)
    ip_address = Column(String(50), nullable=True)
    speed = Column(String(50), nullable=True)
    last_seen = Column(DateTime, default=func.now())

class CommandLog(Base):
    __tablename__ = "command_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    command = Column(Text, nullable=False)
    output = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
