from typing import Dict, Any, List
from pysnmp.hlapi.v3arch import SnmpEngine
from pysnmp.hlapi.v3arch import CommunityData, UdpTransportTarget
from pysnmp.hlapi.v3arch import ContextData, ObjectType, ObjectIdentity
from pysnmp.hlapi.v3arch.asyncio.cmdgen import get_cmd as getCmd
from pysnmp.hlapi.v3arch.asyncio.cmdgen import next_cmd as nextCmd
from pysnmp.error import PySnmpError
from app.adapters.base import BaseAdapter
import re


class SNMPAdapter(BaseAdapter):
    """SNMP适配器，用于通过SNMP协议与网络设备交互"""
    
    # SNMP OID常量定义
    SYS_DESCRIPTION = '1.3.6.1.2.1.1.1.0'  # 系统描述
    SYS_NAME = '1.3.6.1.2.1.1.5.0'  # 系统名称
    SYS_UPTIME = '1.3.6.1.2.1.1.3.0'  # 系统运行时间
    IF_NUMBER = '1.3.6.1.2.1.2.1.0'  # 接口数量
    IF_DESCR = '1.3.6.1.2.1.2.2.1.2'  # 接口描述
    IF_TYPE = '1.3.6.1.2.1.2.2.1.3'  # 接口类型
    IF_MTU = '1.3.6.1.2.1.2.2.1.4'  # 接口MTU
    IF_SPEED = '1.3.6.1.2.1.2.2.1.5'  # 接口速率
    IF_PHYS_ADDRESS = '1.3.6.1.2.1.2.2.1.6'  # 接口物理地址
    IF_ADMIN_STATUS = '1.3.6.1.2.1.2.2.1.7'  # 接口管理状态
    IF_OPER_STATUS = '1.3.6.1.2.1.2.2.1.8'  # 接口操作状态
    IF_IN_OCTETS = '1.3.6.1.2.1.2.2.1.10'  # 接口入站字节数
    IF_IN_UCAST_PKTS = '1.3.6.1.2.1.2.2.1.11'  # 接口入站单播包数
    IF_IN_ERRORS = '1.3.6.1.2.1.2.2.1.14'  # 接口入站错误数
    IF_OUT_OCTETS = '1.3.6.1.2.1.2.2.1.16'  # 接口出站字节数
    IF_OUT_UCAST_PKTS = '1.3.6.1.2.1.2.2.1.17'  # 接口出站单播包数
    IF_OUT_ERRORS = '1.3.6.1.2.1.2.2.1.20'  # 接口出站错误数
    HOST_RESOURCES_CPULOAD1 = '1.3.6.1.2.1.25.3.3.1.2.1'  # CPU 1分钟负载
    HOST_RESOURCES_CPULOAD5 = '1.3.6.1.2.1.25.3.3.1.2.2'  # CPU 5分钟负载
    HOST_RESOURCES_CPULOAD15 = '1.3.6.1.2.1.25.3.3.1.2.3'  # CPU 15分钟负载
    HOST_RESOURCES_MEM_TOTAL = '1.3.6.1.2.1.25.2.3.1.5.1'  # 总内存
    HOST_RESOURCES_MEM_USED = '1.3.6.1.2.1.25.2.3.1.6.1'  # 已用内存
    
    def __init__(self, device_info: Dict[str, Any]):
        """初始化SNMP适配器"""
        super().__init__(device_info)
        self.community = device_info.get('snmp_community', 'public')
        self.port = device_info.get('snmp_port', 161)
        self.version = device_info.get('snmp_version', 2)
        self.engine = SnmpEngine()
        self.transport = None
        self.context = ContextData()
        
    def connect(self) -> bool:
        """连接到SNMP设备"""
        try:
            ip = self.device_info.get('management_ip')
            if not ip:
                raise ValueError("设备IP地址不能为空")
            
            # 创建传输目标
            self.transport = UdpTransportTarget((ip, self.port))
            
            # 测试连接
            test_result = self._get_snmp_value(self.SYS_DESCRIPTION)
            if test_result:
                return True
            else:
                raise ConnectionError("SNMP连接测试失败")
        except PySnmpError as e:
            error_msg = f"SNMP连接失败: {str(e)}"
            print(error_msg)
            raise ConnectionError(error_msg)
        except Exception as e:
            error_msg = f"SNMP连接异常: {str(e)}"
            print(error_msg)
            raise ConnectionError(error_msg)
    
    def disconnect(self) -> bool:
        """断开SNMP连接（SNMP是无状态协议，这里只是清理资源）"""
        self.transport = None
        return True
    
    def get_device_info(self) -> Dict[str, Any]:
        """获取设备基本信息"""
        try:
            info = {
                'vendor': 'generic_snmp',
                'model': '',
                'version': '',
                'serial_number': '',
                'uptime': ''
            }
            
            # 获取系统描述
            sys_desc = self._get_snmp_value(self.SYS_DESCRIPTION)
            if sys_desc:
                info['model'] = self._extract_model_from_description(sys_desc)
                info['version'] = self._extract_version_from_description(sys_desc)
            
            # 获取系统名称
            sys_name = self._get_snmp_value(self.SYS_NAME)
            if sys_name:
                info['name'] = sys_name
            
            # 获取系统运行时间
            uptime = self._get_snmp_value(self.SYS_UPTIME)
            if uptime:
                info['uptime'] = self._format_uptime(int(uptime))
            
            return info
        except Exception as e:
            error_msg = f"获取SNMP设备信息失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """获取所有接口信息"""
        try:
            interfaces = []
            
            # 使用SNMP walk获取接口描述和状态
            if_descriptions = self._walk_snmp_table(self.IF_DESCR)
            if_oper_status = self._walk_snmp_table(self.IF_OPER_STATUS)
            
            # 合并接口信息
            for if_index, description in if_descriptions.items():
                status = if_oper_status.get(if_index, 'unknown')
                interfaces.append({
                    'name': description,
                    'status': 'up' if status == 1 else 'down' if status == 2 else 'other',
                    'protocol': 'unknown',
                    'description': description
                })
            
            return interfaces
        except Exception as e:
            error_msg = f"获取SNMP接口信息失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_interface_status(self, interface: str) -> Dict[str, Any]:
        """获取指定接口状态"""
        try:
            # 查找接口索引
            if_index = self._get_interface_index(interface)
            if not if_index:
                raise ValueError(f"未找到接口: {interface}")
            
            status = {
                'interface': interface,
                'description': self._get_snmp_value(f"{self.IF_DESCR}.{if_index}"),
                'admin_status': self._map_admin_status(self._get_snmp_value(f"{self.IF_ADMIN_STATUS}.{if_index}")),
                'oper_status': self._map_oper_status(self._get_snmp_value(f"{self.IF_OPER_STATUS}.{if_index}")),
                'speed': self._format_speed(self._get_snmp_value(f"{self.IF_SPEED}.{if_index}")),
                'duplex': 'unknown',  # SNMP中没有直接的双工信息
                'mtu': self._get_snmp_value(f"{self.IF_MTU}.{if_index}"),
                'in_packets': self._get_snmp_value(f"{self.IF_IN_UCAST_PKTS}.{if_index}"),
                'out_packets': self._get_snmp_value(f"{self.IF_OUT_UCAST_PKTS}.{if_index}"),
                'in_octets': self._get_snmp_value(f"{self.IF_IN_OCTETS}.{if_index}"),
                'out_octets': self._get_snmp_value(f"{self.IF_OUT_OCTETS}.{if_index}")
            }
            
            return status
        except Exception as e:
            error_msg = f"获取SNMP接口状态失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_config(self) -> str:
        """获取设备配置（SNMP通常不用于获取完整配置，这里返回设备信息）"""
        device_info = self.get_device_info()
        interfaces = self.get_interfaces()
        
        config = f"# SNMP Device Information\n"
        config += f"# Vendor: {device_info.get('vendor', 'unknown')}\n"
        config += f"# Model: {device_info.get('model', 'unknown')}\n"
        config += f"# Version: {device_info.get('version', 'unknown')}\n"
        config += f"# Uptime: {device_info.get('uptime', 'unknown')}\n"
        config += f"\n# Interfaces ({len(interfaces)} interfaces found):\n"
        
        for interface in interfaces[:10]:  # 只显示前10个接口
            config += f"# - {interface.get('name', 'unknown')} ({interface.get('status', 'unknown')})\n"
        
        if len(interfaces) > 10:
            config += f"# ... and {len(interfaces) - 10} more interfaces\n"
        
        return config
    
    def save_config(self) -> bool:
        """保存设备配置（SNMP通常不用于保存配置，这里返回不支持）"""
        print("警告: SNMP协议不支持直接保存设备配置")
        return False
    
    def execute_command(self, command: str) -> str:
        """执行任意命令（SNMP不支持执行命令，这里返回不支持）"""
        print(f"警告: SNMP协议不支持执行命令 '{command}'")
        return "SNMP协议不支持执行命令"
    
    def _get_snmp_value(self, oid: str) -> Any:
        """获取单个SNMP OID的值"""
        try:
            if not self.transport:
                self.connect()
            
            error_indication, error_status, error_index, var_binds = next(
                getCmd(self.engine,
                       CommunityData(self.community),
                       self.transport,
                       self.context,
                       ObjectType(ObjectIdentity(oid)))
            )
            
            if error_indication:
                print(f"SNMP错误: {error_indication}")
                return None
            elif error_status:
                print(f"SNMP错误: {error_status.prettyPrint()}")
                return None
            else:
                for var_bind in var_binds:
                    return str(var_bind[1])
            
            return None
        except Exception as e:
            print(f"获取SNMP值失败: {str(e)}")
            return None
    
    def _walk_snmp_table(self, oid: str) -> Dict[str, Any]:
        """执行SNMP walk操作，获取表格数据"""
        result = {}
        
        try:
            if not self.transport:
                self.connect()
            
            for (error_indication, error_status, error_index, var_binds) in (
                    nextCmd(self.engine,
                            CommunityData(self.community),
                            self.transport,
                            self.context,
                            ObjectType(ObjectIdentity(oid)))):
                
                if error_indication:
                    print(f"SNMP walk错误: {error_indication}")
                    break
                elif error_status:
                    print(f"SNMP walk错误: {error_status.prettyPrint()}")
                    break
                else:
                    for var_bind in var_binds:
                        # 提取OID索引部分
                        oid_parts = str(var_bind[0]).split('.')
                        if_index = oid_parts[-1] if len(oid_parts) > 1 else '0'
                        result[if_index] = str(var_bind[1])
            
            return result
        except Exception as e:
            print(f"SNMP walk操作失败: {str(e)}")
            return result
    
    def _get_interface_index(self, interface_name: str) -> str:
        """根据接口名称获取接口索引"""
        if_descriptions = self._walk_snmp_table(self.IF_DESCR)
        for if_index, description in if_descriptions.items():
            if interface_name in description or description in interface_name:
                return if_index
        return None
    
    def _format_uptime(self, uptime_ticks: int) -> str:
        """格式化SNMP运行时间"""
        # SNMP时间以1/100秒为单位
        seconds = uptime_ticks // 100
        days = seconds // (24 * 3600)
        seconds %= (24 * 3600)
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        
        if days > 0:
            return f"{days}天 {hours}小时 {minutes}分钟 {seconds}秒"
        elif hours > 0:
            return f"{hours}小时 {minutes}分钟 {seconds}秒"
        elif minutes > 0:
            return f"{minutes}分钟 {seconds}秒"
        else:
            return f"{seconds}秒"
    
    def _format_speed(self, speed: str) -> str:
        """格式化接口速率"""
        try:
            speed_value = int(speed)
            if speed_value >= 1000000000:
                return f"{speed_value / 1000000000:.2f} Gbps"
            elif speed_value >= 1000000:
                return f"{speed_value / 1000000:.2f} Mbps"
            elif speed_value >= 1000:
                return f"{speed_value / 1000:.2f} Kbps"
            else:
                return f"{speed_value} bps"
        except (ValueError, TypeError):
            return "unknown"
    
    def _map_admin_status(self, status: str) -> str:
        """映射管理状态值"""
        status_map = {
            '1': 'up',
            '2': 'down',
            '3': 'testing'
        }
        return status_map.get(status, 'unknown')
    
    def _map_oper_status(self, status: str) -> str:
        """映射操作状态值"""
        status_map = {
            '1': 'up',
            '2': 'down',
            '3': 'testing',
            '4': 'unknown',
            '5': 'dormant',
            '6': 'notPresent',
            '7': 'lowerLayerDown'
        }
        return status_map.get(status, 'unknown')
    
    def _extract_model_from_description(self, description: str) -> str:
        """从系统描述中提取设备型号"""
        # 简单的模式匹配，实际应用中可能需要更复杂的逻辑
        patterns = [
            r'Cisco\s+(\S+)',
            r'Huawei\s+(\S+)',
            r'H3C\s+(\S+)',
            r'Ruijie\s+(\S+)',
            r'Juniper\s+(\S+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.I)
            if match:
                return match.group(1)
        
        # 如果没有匹配到特定厂商，返回前30个字符作为型号信息
        return description[:30].strip()
    
    def _extract_version_from_description(self, description: str) -> str:
        """从系统描述中提取软件版本"""
        # 简单的模式匹配，实际应用中可能需要更复杂的逻辑
        patterns = [
            r'Version\s+([\d\.]+)',
            r'Release\s+([\d\.]+)',
            r'VRP\s+([\d\.]+)',
            r'Comware\s+([\d\.]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.I)
            if match:
                return match.group(1)
        
        return "unknown"