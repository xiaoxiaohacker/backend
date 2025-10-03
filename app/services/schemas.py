from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

# 认证相关模型
class Token(BaseModel):
    access_token: str
    token_type: str

# 用户相关模型
class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=100)
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=10)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

# 设备相关模型
class DeviceBase(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    management_ip: str = Field(..., max_length=50)
    vendor: str = Field(..., max_length=50)
    model: Optional[str] = Field(None, max_length=50)
    os_version: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    username: str = Field(..., max_length=50)
    port: Optional[int] = 22
    device_type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = "unknown"

class DeviceCreate(DeviceBase):
    password: str
    enable_password: Optional[str] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    management_ip: Optional[str] = Field(None, max_length=50)
    vendor: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=50)
    os_version: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    username: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = None
    enable_password: Optional[str] = None
    port: Optional[int] = None
    device_type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None

class DeviceOut(DeviceBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 配置相关模型
class ConfigBase(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    taken_by: Optional[str] = Field(None, max_length=50)

class ConfigCreate(ConfigBase):
    device_id: int
    config: Optional[str] = None  # 配置内容，可选，系统可以自动从设备获取

class ConfigOut(ConfigBase):
    id: int
    device_id: int
    filename: str
    file_size: int
    hash: str
    created_at: datetime

    class Config:
        from_attributes = True

# 接口状态模型
class InterfaceStatusBase(BaseModel):
    interface_name: str = Field(..., max_length=100)
    admin_status: Optional[str] = None
    operational_status: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    speed: Optional[str] = None

class InterfaceStatusCreate(InterfaceStatusBase):
    device_id: int

class InterfaceStatusOut(InterfaceStatusBase):
    id: int
    device_id: int
    last_seen: datetime

    class Config:
        from_attributes = True

# 命令执行模型
class CommandRequest(BaseModel):
    command: str

class CommandResponse(BaseModel):
    command: str
    output: str
    success: bool
    executed_at: datetime

# 批量操作模型
class BulkDeviceCreate(BaseModel):
    devices: List[DeviceCreate]
