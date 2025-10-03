from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseAdapter(ABC):
    """交换机适配器基类，定义了所有交换机需要实现的接口"""
    
    def __init__(self, device_info: Dict[str, Any]):
        """
        初始化适配器
        
        Args:
            device_info: 设备信息，包含IP、用户名、密码等
        """
        self.device_info = device_info
        self.connection = None
    
    @abstractmethod
    def connect(self) -> bool:
        """连接到设备"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开连接"""
        pass
    
    @abstractmethod
    def get_device_info(self) -> Dict[str, Any]:
        """获取设备基本信息"""
        pass
    
    @abstractmethod
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """获取所有接口信息"""
        pass
    
    @abstractmethod
    def get_interface_status(self, interface: str) -> Dict[str, Any]:
        """获取指定接口状态"""
        pass
    
    @abstractmethod
    def get_config(self) -> str:
        """获取设备配置"""
        pass
    
    @abstractmethod
    def save_config(self) -> bool:
        """保存设备配置"""
        pass
    
    @abstractmethod
    def execute_command(self, command: str) -> str:
        """执行任意命令"""
        pass

    def _check_connection(self) -> bool:
        """检查连接状态"""
        if not self.connection:
            return self.connect()
        return True