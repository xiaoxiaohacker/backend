import re
from typing import Dict, Any, List
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException
from app.adapters.base import BaseAdapter


class H3CAdapter(BaseAdapter):
    """华三交换机适配器"""
    
    def connect(self) -> bool:
        """连接到华三交换机"""
        try:
            # 根据协议选择设备类型，默认使用telnet
            protocol = self.device_info.get('protocol', 'telnet').lower()
            device_type = 'hp_comware_telnet'  # 默认使用telnet
            
            if protocol == 'ssh':
                device_type = 'hp_comware'
                port = self.device_info.get('port', 22)
            else:
                port = self.device_info.get('port', 23)
            
            device_params = {
                'device_type': device_type,
                'host': self.device_info.get('management_ip'),
                'username': self.device_info.get('username'),
                'password': self.device_info.get('password'),
                'port': port
            }
            
            self.connection = ConnectHandler(**device_params)
            return True
        except (NetMikoTimeoutException, NetMikoAuthenticationException) as e:
            error_msg = f"华三交换机连接失败: {str(e)}"
            print(error_msg)
            self.connection = None
            raise ConnectionError(error_msg)
    
    def disconnect(self) -> bool:
        """断开连接"""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
            return True
        return False
    
    def get_device_info(self) -> Dict[str, Any]:
        """获取华三交换机基本信息"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            # 获取设备型号和版本信息
            output = self.connection.send_command('display version')
            
            info = {
                'vendor': 'H3C',
                'model': '',
                'version': '',
                'serial_number': '',
                'uptime': ''
            }
            
            # 解析输出信息
            model_match = re.search(r'^H3C\s+(\S+)', output, re.M)
            if model_match:
                info['model'] = model_match.group(1)
            
            version_match = re.search(r'Comware\s+Software\s+Version\s+([\d\.]+)', output)
            if version_match:
                info['version'] = version_match.group(1)
            
            return info
        except Exception as e:
            error_msg = f"获取华三设备信息失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """获取所有接口信息"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            output = self.connection.send_command('display interface brief')
            interfaces = []
            
            # 解析接口信息
            lines = output.split('\n')[3:-1]  # 跳过头部和尾部
            for line in lines:
                parts = line.split()
                if len(parts) >= 4:
                    interfaces.append({
                        'name': parts[0],
                        'status': parts[1],
                        'protocol': parts[2],
                        'description': ' '.join(parts[3:]) if len(parts) > 3 else ''
                    })
            
            return interfaces
        except Exception as e:
            error_msg = f"获取华三接口信息失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_interface_status(self, interface: str) -> Dict[str, Any]:
        """获取指定接口状态"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            output = self.connection.send_command(f'display interface {interface}')
            
            status = {
                'interface': interface,
                'description': '',
                'admin_status': '',
                'oper_status': '',
                'speed': '',
                'duplex': '',
                'mtu': '',
                'in_packets': 0,
                'out_packets': 0
            }
            
            # 解析接口状态信息
            desc_match = re.search(r'Description:\s*(.*)', output)
            if desc_match:
                status['description'] = desc_match.group(1)
            
            status_match = re.search(r'current\s+state:\s*(\S+)', output, re.I)
            if status_match:
                status['oper_status'] = status_match.group(1)
            
            return status
        except Exception as e:
            error_msg = f"获取华三接口状态失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_config(self) -> str:
        """获取设备配置"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            config = self.connection.send_command('display current-configuration')
            if not config:
                raise ValueError("未获取到设备配置内容")
            return config
        except Exception as e:
            error_msg = f"获取华三设备配置失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def save_config(self) -> bool:
        """保存设备配置"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            self.connection.send_command('save', expect_string=r'Are you sure to save')
            self.connection.send_command('y')
            return True
        except Exception as e:
            error_msg = f"保存华三设备配置失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def execute_command(self, command: str) -> str:
        """执行任意命令"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            result = self.connection.send_command(command)
            return result
        except Exception as e:
            error_msg = f"执行华三设备命令失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)