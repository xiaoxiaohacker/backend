import re
import time
from typing import Dict, Any, List
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException
from app.adapters.base import BaseAdapter


class HuaweiAdapter(BaseAdapter):
    """华为交换机适配器"""
    
    def __init__(self, device_info: Dict[str, Any]):
        """初始化华为交换机适配器"""
        super().__init__(device_info)
        self.connected = False
        self.start_time = None
        self.connection_time = None
    
    def connect(self) -> bool:
        """连接到华为交换机 - 增强版"""
        try:
            # 从device_info中获取连接信息
            ip = self.device_info.get('management_ip')
            username = self.device_info.get('username', '')
            password = self.device_info.get('password', '')
            # 根据端口自动选择协议
            port = self.device_info.get('port', 22)  # 默认使用22端口
            protocol = self.device_info.get('protocol')
            
            # 如果没有指定协议，根据端口自动判断
            if not protocol:
                protocol = 'telnet' if port == 23 else 'ssh'            
            
            # 验证必要的连接信息
            if not ip:
                raise ValueError("设备IP地址不能为空")
            if not username:
                raise ValueError("设备用户名不能为空")
            
            self.ip = ip
            self.port = port
            self.username = username
            self.password = password
            self.protocol = protocol
            self.start_time = time.time()  # 记录开始时间
            
            # 根据协议选择设备类型列表
            if protocol.lower() == "telnet":
                device_types = ['huawei_telnet', 'cisco_ios_telnet', 'generic_telnet']
            else:  # ssh
                device_types = ['huawei', 'huawei_ssh', 'cisco_ios', 'generic_ssh']
            
            # 基础连接参数
            base_params = {
                'ip': ip,
                'port': port,
                'username': username,
                'password': password,
                'global_delay_factor': 2,
                'read_timeout_override': 10,
                'banner_timeout': 15
            }
            
            # 尝试不同的设备类型
            error_messages = []
            for device_type in device_types:
                try:
                    print(f"尝试使用device_type: {device_type} 连接华为设备 {ip}:{port}")
                    # 复制基础参数并添加当前设备类型
                    params = base_params.copy()
                    params['device_type'] = device_type
                    
                    # 建立连接
                    self.connection = ConnectHandler(**params)
                    
                    # 验证连接是否成功
                    prompt = self.connection.find_prompt()
                    if prompt:
                        print(f"连接成功，设备提示符: {prompt}")
                        self.connected = True
                        
                        # 尝试进入系统视图模式
                        self._enter_system_view()
                        return True
                except Exception as e:
                    error_msg = f"使用device_type {device_type} 连接失败: {str(e)}"
                    print(error_msg)
                    error_messages.append(error_msg)
                    # 清理连接
                    self.connection = None
                    # 尝试下一个设备类型
                    continue
            
            # 如果所有设备类型都失败，抛出详细异常
            detailed_error = "\n".join(error_messages)
            raise ConnectionError(f"无法连接到华为设备 {ip}:{port}，已尝试所有支持的设备类型\n详细错误信息:\n{detailed_error}")
        except NetMikoTimeoutException:
            raise ConnectionError(f"连接华为设备 {ip}:{port} 超时")
        except NetMikoAuthenticationException:
            raise ConnectionError(f"华为设备 {ip}:{port} 认证失败")
        except Exception as e:
            raise ConnectionError(f"连接华为设备 {ip}:{port} 失败: {str(e)}")
        finally:
            # 记录连接时间
            if self.connected:
                self.connection_time = time.time() - self.start_time
                print(f"连接成功，耗时: {self.connection_time:.2f}秒")
    
    def disconnect(self) -> bool:
        """断开连接"""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
            return True
        return False
    
    def _enter_system_view(self) -> None:
        """进入系统视图模式"""
        try:
            self.connection.send_command('system-view', expect_string=r'\]')
            print("成功进入系统视图模式")
        except Exception as e:
            print(f"进入系统视图模式失败: {str(e)}")
    
    def _enter_privileged_mode(self) -> None:
        """尝试进入特权模式"""
        try:
            # 华为设备通常使用system-view命令进入特权配置模式
            # 先检查是否已经在系统视图
            prompt = self.connection.find_prompt()
            if ']' not in prompt:
                print("尝试进入系统视图模式...")
                self._enter_system_view()
                
            # 某些华为设备可能需要密码验证
            if hasattr(self, 'password') and self.password:
                # 检查是否有命令提示符变化或密码要求
                test_response = self.execute_command('display current-configuration | include sysname')
                if 'Error' in test_response or '权限不足' in test_response:
                    print("检测到权限问题，尝试使用密码验证...")
                    # 发送quit退出系统视图，然后尝试重新进入
                    self.execute_command('quit')
                    self.execute_command(f'su - {self.password}')
                    self._enter_system_view()
        except Exception as e:
            print(f"进入特权模式时发生错误: {str(e)}")
    
    def get_device_info(self) -> Dict[str, Any]:
        """获取华为交换机基本信息和系统状态 - 增强版"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            # 确保进入特权模式
            self._enter_privileged_mode()
            
            # 获取设备型号和版本信息
            info_commands = ['display version', 'display device', 'display system-info', 'display sys-info']
            version_output = ""
            
            for cmd in info_commands:
                try:
                    version_output = self.execute_command(cmd)
                    if version_output and len(version_output) > 10 and 'Invalid input' not in version_output and 'Unknown command' not in version_output:
                        break
                except Exception as cmd_e:
                    print(f"执行命令 {cmd} 失败: {str(cmd_e)}")
                    continue
            
            info = {
                'vendor': 'Huawei',
                'model': '',
                'version': '',
                'serial_number': '',
                'uptime': '',
                'memory_usage': {},
                'cpu_usage': {},
                'raw_output': version_output[:300]  # 保存部分原始输出用于调试
            }
            
            # 解析版本信息 - 根据用户提供的实际输出调整正则表达式模式
            # 匹配 Quidway S5700-28P-LI-AC 或类似型号
            model_match = re.search(r'(Quidway|Huawei)\s+(\S+)\s+', version_output)
            if model_match:
                info['model'] = f"{model_match.group(1)} {model_match.group(2)}"
            else:
                # 尝试其他可能的型号格式
                model_patterns = [
                    r'^Huawei Technologies\s+(\S+)',
                    r'Model\s*:\s*(\S+)',
                    r'Device\s+Model\s*:\s*(\S+)',
                    r'Switch\s+Model\s*:\s*(\S+)'
                ]
                
                for pattern in model_patterns:
                    model_match = re.search(pattern, version_output, re.M)
                    if model_match:
                        info['model'] = model_match.group(1)
                        break
            
            # 匹配完整的VRP版本，如 VRP (R) software, Version 5.130 (S5700 V200R003C00SPC300)
            version_match = re.search(r'VRP\s+\(R\)\s+software,\s+Version\s+([\d\.\w\(\)\s]+)', version_output, re.M)
            if version_match:
                info['version'] = version_match.group(1).strip()
            else:
                # 尝试其他可能的版本格式
                version_patterns = [
                    r'VRP\s+Version\s+([\d\.]+)',
                    r'Software\s+Version\s+([\w\.]+)',
                    r'System\s+Version\s*:\s*([\d\.]+)'
                ]
                
                for pattern in version_patterns:
                    version_match = re.search(pattern, version_output)
                    if version_match:
                        info['version'] = version_match.group(1)
                        break
            
            # 获取序列号
            serial_match = re.search(r'Serial\s+Number\s*:\s*(\S+)', version_output, re.M)
            if serial_match:
                info['serial_number'] = serial_match.group(1)
            
            # 获取系统运行时间 - 匹配多种格式
            uptime_patterns = [
                r'system\s+up\s+time:\s+(.*?)\n',
                r'uptime\s+is\s+(.*?)\n',
                r'router\s+uptime\s+is\s+(.*?)\n'
            ]
            
            for pattern in uptime_patterns:
                uptime_match = re.search(pattern, version_output, re.I | re.M)
                if uptime_match:
                    info['uptime'] = uptime_match.group(1).strip()
                    break
            
            # 获取运行内存信息
            try:
                memory_output = self.execute_command('display memory-usage')
                memory_total_match = re.search(r'Total\s+memory:\s+(\d+)\s+kbytes', memory_output, re.I)
                memory_used_match = re.search(r'Used\s+memory:\s+(\d+)\s+kbytes', memory_output, re.I)
                memory_percent_match = re.search(r'Memory\s+using:\s+(\d+)%', memory_output, re.I)
                
                if memory_total_match and memory_used_match and memory_percent_match:
                    info['memory_usage'] = {
                        'total': int(memory_total_match.group(1)),
                        'used': int(memory_used_match.group(1)),
                        'percent': int(memory_percent_match.group(1))
                    }
            except Exception as mem_e:
                print(f"获取内存信息失败: {str(mem_e)}")
            
            # 获取CPU使用率信息
            try:
                cpu_output = self.execute_command('display cpu-usage')
                cpu_1min_match = re.search(r'CPU\s+Usage\s+1\s+Min\s+Average:\s+(\d+)%', cpu_output, re.I)
                cpu_5min_match = re.search(r'CPU\s+Usage\s+5\s+Min\s+Average:\s+(\d+)%', cpu_output, re.I)
                cpu_15min_match = re.search(r'CPU\s+Usage\s+15\s+Min\s+Average:\s+(\d+)%', cpu_output, re.I)
                
                if cpu_1min_match and cpu_5min_match and cpu_15min_match:
                    info['cpu_usage'] = {
                        '1min': int(cpu_1min_match.group(1)),
                        '5min': int(cpu_5min_match.group(1)),
                        '15min': int(cpu_15min_match.group(1))
                    }
            except Exception as cpu_e:
                print(f"获取CPU信息失败: {str(cpu_e)}")
            
            print(f"华为设备信息解析结果: 型号={info['model']}, 版本={info['version']}, 序列号={info['serial_number']}, 运行时间={info['uptime']}")
            return info
        except Exception as e:
            error_msg = f"获取华为设备信息失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """获取所有接口信息 - 增强版"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            # 确保进入特权模式
            self._enter_privileged_mode()
            
            # 尝试多种可能的接口命令
            interface_commands = [
                'display interface brief',
                'show interfaces status',
                'display interfaces'
            ]
            
            interfaces = []
            output = ""
            
            for cmd in interface_commands:
                try:
                    output = self.execute_command(cmd)
                    if output and len(output) > 10 and 'Invalid input' not in output and 'Unknown command' not in output:
                        break
                except Exception as cmd_e:
                    print(f"执行命令 {cmd} 失败: {str(cmd_e)}")
                    continue
            
            # 如果获取到了输出，尝试解析
            if output and len(output) > 10 and 'Invalid input' not in output and 'Unknown command' not in output:
                print(f"接口命令输出长度: {len(output)} 字符")
                # 简单解析，根据不同命令的输出格式调整解析逻辑
                lines = output.split('\n')
                
                # 跳过前几行标题
                start_index = 0
                for i, line in enumerate(lines):
                    if line.strip() and (line.strip().startswith('Interface') or line.strip().startswith('接口') or line.strip().startswith('Port') or line.strip().startswith('Port Name')):
                        start_index = i + 1
                        break
                
                for line in lines[start_index:]:
                    line = line.strip()
                    if not line or line.startswith('%') or line.startswith('#') or line.startswith('--') or line.startswith('=='):
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 2:
                        # 简化的解析逻辑，根据实际输出格式调整
                        interface_info = {
                            'name': parts[0],
                            'status': parts[1] if len(parts) > 1 else 'unknown',
                            'raw_info': line  # 保存原始行用于调试
                        }
                        
                        # 如果有更多信息，尝试解析
                        if len(parts) >= 3:
                            interface_info['protocol'] = parts[2]
                        if len(parts) >= 4:
                            interface_info['description'] = ' '.join(parts[3:])
                        
                        interfaces.append(interface_info)
            
            print(f"解析到的接口数量: {len(interfaces)}")
            return interfaces
        except Exception as e:
            error_msg = f"获取华为接口信息失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_interface_status(self, interface: str) -> Dict[str, Any]:
        """获取指定接口状态 - 增强版"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            # 确保进入特权模式
            self._enter_privileged_mode()
            
            output = self.execute_command(f'display interface {interface}')
            
            status = {
                'interface': interface,
                'description': '',
                'admin_status': '',
                'oper_status': '',
                'speed': '',
                'duplex': '',
                'mtu': '',
                'in_packets': 0,
                'out_packets': 0,
                'in_bytes': 0,
                'out_bytes': 0,
                'errors': 0,
                'discards': 0
            }
            
            # 解析接口描述
            desc_match = re.search(r'Description:\s*(.*)', output)
            if desc_match:
                status['description'] = desc_match.group(1)
            
            # 解析操作状态
            status_match = re.search(r'current\s+state:\s*(\S+)', output, re.I)
            if status_match:
                status['oper_status'] = status_match.group(1)
            
            # 解析管理状态
            admin_match = re.search(r'Line\s+protocol\s+current\s+state:\s*(\S+)', output, re.I)
            if admin_match:
                status['admin_status'] = admin_match.group(1)
            
            # 解析速率和双工模式
            speed_duplex_match = re.search(r'Speed:\s*(\S+),\s+Duplex:\s*(\S+)', output, re.I)
            if speed_duplex_match:
                status['speed'] = speed_duplex_match.group(1)
                status['duplex'] = speed_duplex_match.group(2)
            
            # 解析MTU
            mtu_match = re.search(r'MTU\s+\d+\s+bytes', output, re.I)
            if mtu_match:
                status['mtu'] = mtu_match.group(0)
            
            # 解析数据包统计
            in_packets_match = re.search(r'Input\s+:\s+(\d+)\s+packets', output, re.I)
            if in_packets_match:
                status['in_packets'] = int(in_packets_match.group(1))
            
            out_packets_match = re.search(r'Output\s+:\s+(\d+)\s+packets', output, re.I)
            if out_packets_match:
                status['out_packets'] = int(out_packets_match.group(1))
            
            # 解析字节统计
            in_bytes_match = re.search(r'Input\s+bytes\s*:\s*(\d+)', output, re.I)
            if in_bytes_match:
                status['in_bytes'] = int(in_bytes_match.group(1))
            
            out_bytes_match = re.search(r'Output\s+bytes\s*:\s*(\d+)', output, re.I)
            if out_bytes_match:
                status['out_bytes'] = int(out_bytes_match.group(1))
            
            # 解析错误统计
            errors_match = re.search(r'Error\s+packets\s*:\s*(\d+)', output, re.I)
            if errors_match:
                status['errors'] = int(errors_match.group(1))
            
            return status
        except Exception as e:
            error_msg = f"获取华为接口状态失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_config(self) -> str:
        """获取设备配置 - 增强版（优化超时处理和命令兼容性）"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            # 确保进入特权模式
            self._enter_privileged_mode()
            
            # 尝试设置终端长度为0，避免分页（尝试多种命令，兼容性处理）
            terminal_length_commands = [
                'screen-length 0 temporary',
                'screen-length 0',
                'terminal length 0'
            ]
            
            terminal_length_set = False
            for terminal_cmd in terminal_length_commands:
                try:
                    print(f"尝试设置终端长度: {terminal_cmd}")
                    response = self.execute_command(terminal_cmd)
                    # 检查是否设置成功（有些设备可能没有明确的成功提示）
                    if response and 'Error' not in response and 'error' not in response:
                        terminal_length_set = True
                        print(f"终端长度设置成功: {terminal_cmd}")
                        break
                except Exception as e:
                    print(f"设置终端长度命令 {terminal_cmd} 失败: {str(e)}")
                    # 继续尝试下一个命令，不中断流程
                    continue
            
            # 尝试多种配置获取命令
            config_commands = [
                'display current-configuration',
                'show running-config',
                'display saved-configuration',
                'show startup-config'
            ]
            
            config = ""
            success_command = ""
            
            # 增加配置获取的超时时间（秒）
            config_timeout = 40  # 增加到40秒以处理大型配置
            
            for cmd in config_commands:
                try:
                    # 执行配置命令，使用增加的超时时间
                    print(f"尝试华为配置命令: {cmd} (超时: {config_timeout}秒)")
                    config = self.execute_command(cmd, timeout=config_timeout)
                    
                    # 检查是否成功获取配置
                    if config and len(config) > 50 and ('#' in config or '!' in config or 'sysname' in config):
                        print(f"成功使用命令 {cmd} 获取配置，配置长度: {len(config)} 字符")
                        success_command = cmd
                        break
                    else:
                        print(f"命令 {cmd} 未能获取有效配置")
                except Exception as cmd_e:
                    print(f"执行命令 {cmd} 失败: {str(cmd_e)}")
                    continue
            
            # 如果没有获取到配置，抛出异常
            if not config or len(config) < 50:
                error_commands = ', '.join(config_commands)
                raise ValueError(f"配置获取失败，已尝试命令: {error_commands}")
            
            return config
        except Exception as e:
            error_msg = f"获取华为设备配置失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def save_config(self) -> bool:
        """保存设备配置 - 增强版"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            # 确保进入特权模式
            self._enter_privileged_mode()
            
            # 华为设备保存配置的命令可能因型号而异
            save_commands = [
                ('save', r'Are you sure to save'),
                ('save configuration', r'Are you sure to save')
            ]
            
            for cmd, expect_prompt in save_commands:
                try:
                    print(f"尝试保存配置: {cmd}")
                    self.connection.send_command(cmd, expect_string=expect_prompt)
                    # 确认保存
                    result = self.connection.send_command('y')
                    
                    # 检查是否保存成功
                    if 'successfully' in result.lower() or '成功' in result:
                        print("配置保存成功")
                        return True
                except Exception as cmd_e:
                    print(f"执行保存命令 {cmd} 失败: {str(cmd_e)}")
                    continue
            
            # 如果所有命令都失败，抛出异常
            raise Exception("所有保存配置的命令都失败")
        except Exception as e:
            error_msg = f"保存华为设备配置失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def execute_command(self, command: str, timeout: int = 15) -> str:
        """执行任意命令 - 增强版（支持可配置超时时间）"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            print(f"执行命令: {command} (超时: {timeout}秒)")
            
            # 清除可能的缓冲区内容
            try:
                self.connection.read_channel()
            except:
                pass
            
            # 使用底层方法发送命令并读取响应
            self.connection.write_channel(command + '\n')
            
            # 等待命令执行完成
            time.sleep(1.5)  # 增加延迟以确保命令执行完成
            
            # 读取响应内容
            response = ""
            timeout_time = time.time() + timeout
            while time.time() < timeout_time:
                try:
                    chunk = self.connection.read_channel()
                    if chunk:
                        response += chunk
                        # 重置超时计时器
                        timeout_time = time.time() + timeout
                        # 如果检测到命令提示符，认为命令执行完成
                        if any(prompt in response for prompt in ['#', '>', '$', '%', ']', '<']):
                            break
                    else:
                        # 短暂暂停以避免CPU占用过高
                        time.sleep(0.2)
                except Exception as chunk_error:
                    print(f"读取响应块错误: {str(chunk_error)}")
                    break
            
            # 清理响应内容
            if response:
                # 去除命令回显
                if response.startswith(command):
                    response = response[len(command):]
                response = response.strip()
                
                # 检查是否存在访问权限问题，尝试进入特权模式
                if any(deny_keyword in response.lower() for deny_keyword in ['access denied', '权限不足', '未授权', 'privilege denied']):
                    print(f"检测到访问权限问题，尝试进入特权模式...")
                    
                    # 尝试进入特权模式
                    self._enter_privileged_mode()
                    
                    # 清除缓冲区
                    try:
                        self.connection.read_channel()
                    except:
                        pass
                    
                    # 重新执行命令
                    print(f"重新执行命令: {command}")
                    self.connection.write_channel(command + '\n')
                    time.sleep(1.5)
                    
                    # 重新读取响应
                    response = ""
                    retry_timeout = time.time() + timeout
                    while time.time() < retry_timeout:
                        try:
                            chunk = self.connection.read_channel()
                            if chunk:
                                response += chunk
                                retry_timeout = time.time() + timeout
                                # 增加华为设备特定提示符格式 <hostname>
                                if any(prompt in response for prompt in ['#', '>', '$', '%', ']', '<']):
                                    break
                            else:
                                time.sleep(0.2)
                        except:
                            break
                    
                    # 清理重新执行的响应
                    if response and response.startswith(command):
                        response = response[len(command):]
                    response = response.strip()
            
            print(f"命令执行结果长度: {len(response)} 字符")
            # 如果响应长度太短，打印前几个字符用于调试
            if len(response) < 100:
                print(f"命令执行结果: {response}")
            return response
        except Exception as e:
            error_msg = f"执行华为设备命令失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)