import time
import time
import re
from typing import Dict, Any, List
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException
from app.adapters.base import BaseAdapter


class RuijieAdapter(BaseAdapter):
    """锐捷交换机适配器"""
    
    def __init__(self, device_info: Dict[str, Any]):
        """初始化锐捷交换机适配器"""
        super().__init__(device_info)
        self.connected = False
        self.start_time = None
        self.connection_time = None
        self.in_privileged_mode = False

    def connect(self) -> bool:
        """连接到锐捷交换机"""
        try:
            if self.connected:
                print("[警告] 已经连接到设备，不需要重新连接")
                return True
            
            # 从device_info中获取连接信息
            ip = self.device_info.get('management_ip')
            username = self.device_info.get('username', '')
            password = self.device_info.get('password', '')
            
            # 验证必要的连接信息
            if not ip:
                raise ValueError("设备IP地址不能为空")
            if not username:
                raise ValueError("设备用户名不能为空")
            
            self.ip = ip
            self.port = 23  # 强制使用telnet端口
            self.username = username
            self.password = password
            self.start_time = time.time()  # 记录开始时间
            print(f"[连接] 尝试连接锐捷设备 {self.ip}:{self.port}")
            
            # 使用generic_telnet设备类型
            device_type = 'generic_telnet'
            
            # 基础连接参数
            params = {
                'ip': self.ip,
                'port': self.port,
                'username': self.username,
                'password': self.password,
                'device_type': device_type,
                'global_delay_factor': 5,
                'read_timeout_override': 30,
                'banner_timeout': 30,
                'conn_timeout': 30
            }
            
            # 尝试连接，增加重试机制
            error_messages = []
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    retry_count += 1
                    print(f"[尝试 {retry_count}/{max_retries}] 使用device_type: {device_type} 连接锐捷设备")
                    
                    # 建立连接
                    self.connection = ConnectHandler(**params)
                    
                    # 尝试查找提示符确认连接成功
                    try:
                        prompt = self.connection.find_prompt()
                        print(f"初始设备提示符: {prompt}")
                            
                        # 检查是否有命令提示符或者用户名提示符
                        if prompt and any(p in prompt for p in ['>', '#', '$', '%']):
                            self.connected = True
                            
                            # 尝试进入特权模式
                            self._enter_privileged_mode()
                            return True
                        elif prompt and 'username' in prompt.lower():
                            print("检测到用户名提示符，尝试使用登录策略登录...")
                            
                            # 尝试使用三种登录策略
                            if self._login_strategy_direct(self.ip, self.port, self.username, self.password):
                                self.connected = True
                                self._enter_privileged_mode()
                                return True
                            elif self._login_strategy_explicit(self.ip, self.port, self.username, self.password):
                                self.connected = True
                                self._enter_privileged_mode()
                                return True
                            elif self._login_strategy_fallback(self.ip, self.port, self.username, self.password):
                                self.connected = True
                                self._enter_privileged_mode()
                                return True
                    except Exception as e:
                        print(f"查找提示符失败: {str(e)}")
                         
                        # 尝试发送简单命令测试连接
                        try:
                            print("尝试发送命令测试连接...")
                            test_response = self.connection.send_command_timing('?', delay_factor=2)
                            if test_response:
                                print(f"连接测试成功，收到响应: {test_response}")
                                self.connected = True
                                return True
                        except Exception as inner_e:
                            print(f"连接测试失败: {str(inner_e)}")
                    
                    # 如果当前设备类型没有成功，清理连接
                    self.connection = None
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
            raise ConnectionError(f"无法连接到锐捷设备 {self.ip}:{self.port}，已尝试所有支持的设备类型\n详细错误信息:\n{detailed_error}")
        except NetMikoTimeoutException:
            raise ConnectionError(f"连接锐捷设备 {self.ip}:{self.port} 超时")
        except NetMikoAuthenticationException:
            raise ConnectionError(f"锐捷设备 {self.ip}:{self.port} 认证失败")
        except Exception as e:
            raise ConnectionError(f"连接锐捷设备 {self.ip}:{self.port} 失败: {str(e)}")
        finally:
            # 记录连接时间
            if self.connected:
                self.connection_time = time.time() - self.start_time
                print(f"连接成功，耗时: {self.connection_time:.2f}秒")
    
    def disconnect(self) -> bool:
        """断开与锐捷交换机的连接"""
        try:
            if hasattr(self, 'connection') and self.connection:
                self.connection.disconnect()
                self.connection = None
                self.connected = False
                self.in_privileged_mode = False
                return True
            return False
        except Exception as e:
            print(f"断开锐捷设备连接失败: {str(e)}")
            return False
            
    def _login_strategy_direct(self, ip, port, username, password) -> bool:
        """直接登录策略：直接发送用户名和密码"""
        try:
            # 使用send_command_timing进行登录，简化逻辑
            print(f"使用标准API进行直接登录策略")
            
            # 尝试使用write_channel和read_channel方法代替send_command_timing
            print(f"发送用户名: {username}")
            self.connection.write_channel(username + '\r\n')
            time.sleep(1)  # 给设备时间响应
            
            # 读取响应
            user_response = self.connection.read_channel()
            print(f"发送用户名后响应: {user_response}")
            
            print(f"发送密码: ********")
            self.connection.write_channel(password + '\r\n')
            time.sleep(1)  # 给设备时间响应
            
            # 读取响应
            pass_response = self.connection.read_channel()
            print(f"发送密码后响应: {pass_response}")
            
            # 发送几个回车检查是否登录成功
            final_response = ""
            for i in range(3):
                self.connection.write_channel('\r\n')
                time.sleep(0.5)
                final_response += self.connection.read_channel()
                print(f"发送回车 {i+1}/3 后响应: {final_response}")
                
                # 更灵活的提示符检测
                if any(prompt in final_response for prompt in ['>', '#', '$', '%']):
                    print(f"直接登录策略成功: 检测到命令提示符")
                    return True
            
            # 如果没有检测到提示符但响应不为空，也尝试继续
            if final_response.strip():
                print(f"直接登录策略: 虽然未检测到标准提示符，但收到了响应，尝试继续")
                self.connected = True
                return True
            
            print("直接登录策略失败: 未检测到有效的命令提示符且响应为空")
            return False
        except Exception as e:
            print(f"直接登录策略异常: {str(e)}")
            return False
            
    def _login_strategy_explicit(self, ip, port, username, password) -> bool:
        """显式检测提示符登录策略：等待特定的用户名/密码提示符"""
        try:
            print(f"使用标准API进行显式登录策略")
            
            # 先尝试读取当前的提示符状态
            current_prompt = self.connection.read_channel()
            print(f"当前提示符: {current_prompt}")
            
            # 如果已经有用户名提示符，直接发送用户名
            if any(prompt in current_prompt.lower() for prompt in ['username:', 'login:', '用户名:']):
                print(f"检测到用户名提示符，发送用户名: {username}")
                self.connection.write_channel(username + '\r\n')
                time.sleep(1)  # 给设备时间响应
            else:
                # 否则直接发送用户名
                print(f"未检测到用户名提示符，直接发送用户名: {username}")
                self.connection.write_channel(username + '\r\n')
                time.sleep(1)  # 给设备时间响应
            
            # 读取用户名发送后的响应
            user_response = self.connection.read_channel()
            print(f"发送用户名后响应: {user_response}")
            
            # 发送密码
            print(f"发送密码: ********")
            self.connection.write_channel(password + '\r\n')
            time.sleep(1)  # 给设备时间响应
            
            # 读取密码发送后的响应
            pass_response = self.connection.read_channel()
            print(f"发送密码后响应: {pass_response}")
            
            # 发送几个回车检查是否登录成功
            final_response = ""
            for i in range(3):
                self.connection.write_channel('\r\n')
                time.sleep(0.5)
                final_response += self.connection.read_channel()
                print(f"发送回车 {i+1}/3 后响应: {final_response}")
                
                # 更灵活的提示符检测
                if any(prompt in final_response for prompt in ['>', '#', '$', '%']):
                    print(f"显式登录策略成功: 检测到命令提示符")
                    return True
            
            # 如果没有检测到提示符但响应不为空，也尝试继续
            if final_response.strip():
                print(f"显式登录策略: 虽然未检测到标准提示符，但收到了响应，尝试继续")
                self.connected = True
                return True
            
            print("显式登录策略失败: 未检测到有效的命令提示符且响应为空")
            return False
        except Exception as e:
            print(f"显式登录策略异常: {str(e)}")
            return False
            
    def _login_strategy_fallback(self, ip, port, username, password) -> bool:
        """备用登录策略：缓慢发送命令，增加等待时间"""
        try:
            print("使用write/read通道进行备用登录策略")
            
            # 1. 重置连接状态
            try:
                # 发送几个回车清理输入缓冲区
                self.connection.write_channel('\r\n\r\n')
                time.sleep(2)  # 给设备时间响应
                self.connection.read_channel()  # 清理缓冲区
            except Exception as e:
                print(f"重置连接状态失败: {str(e)}")
            
            # 2. 读取当前状态
            current_status = self.connection.read_channel()
            print(f"备用策略 - 当前状态: {current_status}")
            
            # 3. 发送用户名
            print(f"备用策略 - 发送用户名: {username}")
            self.connection.write_channel(username + '\r\n')
            time.sleep(1.5)  # 给设备时间响应
            
            # 读取用户名发送后的响应
            user_response = self.connection.read_channel()
            print(f"备用策略 - 发送用户名后响应: {user_response}")
            
            # 4. 发送密码
            print(f"备用策略 - 发送密码: ********")
            self.connection.write_channel(password + '\r\n')
            time.sleep(1.5)  # 给设备时间响应
            
            # 读取密码发送后的响应
            pass_response = self.connection.read_channel()
            print(f"备用策略 - 发送密码后响应: {pass_response}")
            
            # 5. 多次发送回车，尝试获取提示符
            final_response = ""
            for i in range(5):
                try:
                    time.sleep(0.8)  # 更长的延迟
                    self.connection.write_channel('\r\n')
                    time.sleep(0.8)
                    final_response += self.connection.read_channel()
                    print(f"备用策略 - 发送回车 {i+1}/5 后响应: {final_response}")
                    
                    # 更灵活的提示符检测
                    if any(prompt in final_response for prompt in ['>', '#', '$', '%']):
                        print(f"备用登录策略成功: 检测到命令提示符")
                        return True
                except Exception as e:
                    print(f"发送回车检测提示符失败: {str(e)}")
            
            # 如果没有检测到提示符但响应不为空，也尝试继续
            if final_response.strip():
                print(f"备用登录策略: 虽然未检测到标准提示符，但收到了响应，尝试继续")
                self.connected = True
                return True
            
            print("备用登录策略失败: 未检测到有效的命令提示符且响应为空")
            return False
        except Exception as e:
            print(f"备用登录策略异常: {str(e)}")
            return False
    
    def _enter_privileged_mode(self) -> bool:
        """尝试进入锐捷设备特权模式，返回是否成功"""
        try:
            # 检查是否已经在特权模式
            try:
                prompt = self.connection.find_prompt()
                if '#' in prompt:
                    print("设备已在特权模式")
                    self.in_privileged_mode = True
                    return True
            except Exception as e:
                print(f"获取当前提示符失败: {str(e)}")
            
            print("尝试进入特权模式...")
            
            # 先发送回车确保连接处于就绪状态
            print("发送回车清理缓冲区")
            self.connection.write_channel('\r\n')
            time.sleep(0.5)
            self.connection.read_channel()  # 清理缓冲区
            
            # 发送enable命令尝试进入特权模式，使用write/read方法更可靠
            print("发送enable命令")
            self.connection.write_channel('enable\r\n')
            time.sleep(1)  # 给设备时间响应
            
            # 读取enable命令的响应
            enable_response = self.connection.read_channel()
            print(f"enable命令响应: {enable_response}")
            
            # 检查是否需要密码
            if 'Password' in enable_response or 'password' in enable_response:
                print("需要特权模式密码")
                
                # 尝试使用设备密码作为特权模式密码
                if hasattr(self, 'password') and self.password:
                    print("尝试使用设备密码作为特权模式密码")
                    self.connection.write_channel(self.password + '\r\n')
                    time.sleep(1)
                    
                    # 检查是否成功进入特权模式
                    try:
                        time.sleep(1)  # 额外等待时间
                        self.connection.write_channel('\r\n')
                        time.sleep(0.5)
                        post_pass_prompt = self.connection.read_channel()
                        print(f"特权模式密码后响应: {post_pass_prompt}")
                        if '#' in post_pass_prompt:
                            print("特权模式切换成功")
                            self.in_privileged_mode = True
                            return True
                    except Exception as e:
                        print(f"检查特权模式提示符失败: {str(e)}")
                    
                # 如果设备密码失败，尝试默认密码
                print("尝试使用默认密码 'ruijie' 作为特权模式密码")
                self.connection.write_channel('ruijie\r\n')
                time.sleep(1)
                
                # 再次检查是否成功进入特权模式
                try:
                    time.sleep(1)  # 额外等待时间
                    self.connection.write_channel('\r\n')
                    time.sleep(0.5)
                    final_prompt = self.connection.read_channel()
                    print(f"默认密码后响应: {final_prompt}")
                    if '#' in final_prompt:
                        print("特权模式切换成功")
                        self.in_privileged_mode = True
                        return True
                    else:
                        print("特权模式切换失败，但继续尝试操作")
                        return False
                except Exception as e:
                    print(f"再次检查特权模式提示符失败: {str(e)}")
                    return False
            else:
                # 如果不需要密码，直接检查是否进入了特权模式
                try:
                    time.sleep(0.5)
                    self.connection.write_channel('\r\n')
                    time.sleep(0.5)
                    new_prompt = self.connection.read_channel()
                    print(f"无需密码时的响应: {new_prompt}")
                    if '#' in new_prompt:
                        print("特权模式切换成功")
                        self.in_privileged_mode = True
                        return True
                    else:
                        print("特权模式切换失败，但继续尝试操作")
                        return False
                except Exception as e:
                    print(f"检查特权模式提示符失败: {str(e)}")
                    return False
        except Exception as e:
            print(f"进入特权模式时发生错误: {str(e)}")
            return False
    
    def get_device_info(self) -> Dict[str, Any]:
        """获取锐捷交换机基本信息和系统状态 - 增强版"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            # 确保进入特权模式
            self._enter_privileged_mode()
            
            # 锐捷设备信息获取
            info_commands = ['show version', 'display version', 'show system-info', 'show tech-support', 'show inventory']
            version_output = ""
            
            # 尝试多种命令获取设备信息
            for cmd in info_commands:
                try:
                    version_output = self.execute_command(cmd)
                    if version_output and len(version_output) > 10 and 'Invalid input' not in version_output and 'Unknown command' not in version_output:
                        break
                except Exception as cmd_e:
                    print(f"执行命令 {cmd} 失败: {str(cmd_e)}")
                    continue
            
            # 打印原始输出用于调试
            print(f"设备信息命令执行结果 (前300字符): {version_output[:300]}")
            
            info = {
                'vendor': 'Ruijie',
                'model': '',
                'version': '',
                'serial_number': '',
                'uptime': '',
                'memory_usage': {},
                'cpu_usage': {},
                'raw_output': version_output[:500]  # 保存更多原始输出用于调试
            }
            
            # 解析型号信息 - 适配不同型号格式
            model_patterns = [
                r'^Model:\s*(\S+)',
                r'^Hardware\s+Version:\s*(\S+)',
                r'^Switch\s+Model:\s*(\S+)',
                r'^System\s+Model:\s*(\S+)',
                r'RGOS\s+software,\s+Version\s+[\d\.\w]+\s+\((\S+)\s+',
                r'Version\s+\S+\s+\((\S+)\)',  # 例如: Version 10.4(2b12)p2 (S2928G-E_180357)
                r'Product\s+Name:\s*(.+)',
                r'设备型号:\s*(.+)',
                r'型号:\s*(\S+)',
                r'Chassis\s+Type:\s*(.+)',  # 匹配类似"Chassis Type: S2928G-E"的格式
                r'System description\s*:\s*.*\((\S+)\)'  # 匹配类似"System description: Ruijie Full Gigabit Security & Intelligence Access Switch (S2928G-E) By Ruijie Networks"的格式
            ]
            
            for pattern in model_patterns:
                model_match = re.search(pattern, version_output, re.M | re.I)
                if model_match:
                    info['model'] = model_match.group(1).strip()
                    break
            
            # 解析软件版本信息
            version_patterns = [
                r'RGOS\s+software,\s+Version\s+([\d\.\w\(\)]+)',
                r'Software\s+Version\s*:\s*([\d\.\w]+)',
                r'Version\s+([\d\.\w\(\)]+)',
                r'Version\s+([\d\.]+[a-zA-Z]?)\s+\(\S+\)',  # 例如: Version 10.4(2b12)p2 (S2928G-E_180357)
                r'System\s+Software\s+Version:\s*([\d\.\w\(\)]+)',
                r'系统软件版本:\s*([\d\.\w\(\)]+)',
                r'System software version\s*:\s*(RGOS\s+[\d\.\w\(\)]+)'
            ]
            
            for pattern in version_patterns:
                version_match = re.search(pattern, version_output, re.M | re.I)
                if version_match:
                    info['version'] = version_match.group(1).strip()
                    break
            
            # 获取序列号
            serial_patterns = [
                r'Serial\s*Number:\s*(\S+)',
                r'SN:\s*(\S+)',
                r'Serial\s*No:\s*(\S+)',
                r'序列号:\s*(\S+)',
                r'Serial-Number:\s*(\S+)'
            ]
            
            for pattern in serial_patterns:
                serial_match = re.search(pattern, version_output, re.M | re.I)
                if serial_match:
                    info['serial_number'] = serial_match.group(1).strip()
                    break
            
            # 获取系统运行时间
            uptime_patterns = [
                r'system\s+uptime\s+is\s+(.*?)\n',
                r'uptime\s+is\s+(.*?)\n',
                r'router\s+uptime\s+is\s+(.*?)\n',
                r'system\s+running\s+time:\s+(.*?)\n',
                r'系统运行时间:\s+(.*?)\n',
                r'已运行时间:\s+(.*?)\n'
            ]
            
            for pattern in uptime_patterns:
                uptime_match = re.search(pattern, version_output, re.I | re.M)
                if uptime_match:
                    info['uptime'] = uptime_match.group(1).strip()
                    break
            
            # 添加额外的正则表达式模式来匹配设备描述中的型号信息
            if not info['model']:
                system_desc_match = re.search(r'System description\s*:\s*.*\((\S+)\)', version_output, re.M | re.I)
                if system_desc_match:
                    info['model'] = system_desc_match.group(1)
                    print(f"从系统描述提取设备型号: {info['model']}")
            
            # 获取内存信息
            try:
                memory_commands = ['show memory', 'display memory', 'show memory usage', 'display memory usage']
                memory_output = ""
                
                for mem_cmd in memory_commands:
                    try:
                        memory_output = self.execute_command(mem_cmd)
                        if memory_output and len(memory_output) > 10:
                            break
                    except Exception:
                        continue
                
                if memory_output:
                    memory_total_match = re.search(r'Total\s+memory:\s+(\d+)\s+KBytes', memory_output, re.I)
                    memory_used_match = re.search(r'Used\s+memory:\s+(\d+)\s+KBytes', memory_output, re.I)
                    memory_percent_match = re.search(r'Memory\s+usage:\s+(\d+)%', memory_output, re.I)
                    
                    if memory_total_match and memory_used_match:
                        total = int(memory_total_match.group(1))
                        used = int(memory_used_match.group(1))
                        percent = int(memory_percent_match.group(1)) if memory_percent_match else int((used / total) * 100) if total > 0 else 0
                        
                        info['memory_usage'] = {
                            'total': total,
                            'used': used,
                            'percent': percent
                        }
            except Exception as mem_e:
                print(f"获取内存信息失败: {str(mem_e)}")
            
            # 获取CPU使用率
            try:
                cpu_commands = ['show cpu', 'display cpu', 'show cpu-usage', 'display cpu-usage']
                cpu_output = ""
                
                for cpu_cmd in cpu_commands:
                    try:
                        cpu_output = self.execute_command(cpu_cmd)
                        if cpu_output and len(cpu_output) > 10:
                            break
                    except Exception:
                        continue
                
                if cpu_output:
                    cpu_1min_match = re.search(r'CPU\s+utilization\s+for\s+1\s+minute\s+is\s+(\d+)%', cpu_output, re.I)
                    cpu_5min_match = re.search(r'CPU\s+utilization\s+for\s+5\s+minutes\s+is\s+(\d+)%', cpu_output, re.I)
                    cpu_15min_match = re.search(r'CPU\s+utilization\s+for\s+15\s+minutes\s+is\s+(\d+)%', cpu_output, re.I)
                    
                    cpu_data = {}
                    if cpu_1min_match:
                        cpu_data['1min'] = int(cpu_1min_match.group(1))
                    if cpu_5min_match:
                        cpu_data['5min'] = int(cpu_5min_match.group(1))
                    if cpu_15min_match:
                        cpu_data['15min'] = int(cpu_15min_match.group(1))
                    
                    if cpu_data:
                        info['cpu_usage'] = cpu_data
            except Exception as cpu_e:
                print(f"获取CPU信息失败: {str(cpu_e)}")
            
            print(f"锐捷设备信息解析结果: 型号={info['model']}, 版本={info['version']}, 序列号={info['serial_number']}, 运行时间={info['uptime']}")
            return info
        except Exception as e:
            error_msg = f"获取锐捷设备信息失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """获取所有接口信息 - 增强版"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            # 确保进入特权模式
            self._enter_privileged_mode()
            
            # 锐捷设备接口命令列表，增加了更多可能的命令
            interface_commands = [
                'show interface status',
                'show interfaces status',
                'show interface brief',
                'display interface brief',
                'show interfaces',
                'display interfaces',
                'show ip interface brief',
                'display ip interface brief'
            ]
            
            interfaces = []
            output = ""
            used_command = ""
            
            # 首先尝试设置终端长度为0，避免分页
            try:
                self.execute_command('terminal length 0')
                time.sleep(0.5)
            except Exception:
                pass
            
            # 尝试多种命令获取接口信息
            for cmd in interface_commands:
                try:
                    print(f"尝试接口命令: {cmd}")
                    # 增加超时时间和禁用提示符检查，因为某些命令可能需要更多时间响应
                    output = self.execute_command(cmd, timeout=15, expect_prompt=False)
                    
                    # 检查输出是否有效
                    if output and isinstance(output, str) and len(output) > 10 and 'Invalid input' not in output and 'Unknown command' not in output:
                        used_command = cmd
                        print(f"使用命令 {cmd} 获取接口信息成功，输出长度: {len(output)} 字符")
                        
                        # 如果输出较短，可能是因为命令没有正确执行，继续尝试下一个命令
                        if len(output) < 50:
                            print(f"警告: 接口命令 {cmd} 的输出可能不完整，长度: {len(output)} 字符")
                            print(f"输出内容: {output}")
                            continue
                        
                        break
                except Exception as cmd_e:
                    print(f"执行命令 {cmd} 失败: {str(cmd_e)}")
                    continue
            
            # 如果获取到了输出，尝试解析
            if output and isinstance(output, str) and len(output) > 10:
                print(f"接口命令输出长度: {len(output)} 字符")
                
                # 打印部分输出用于调试
                if len(output) > 200:
                    print(f"接口命令输出前200字符: {output[:200]}...")
                else:
                    print(f"接口命令完整输出: {output}")
                
                # 简单解析，根据不同命令的输出格式调整解析逻辑
                lines = output.split('\n')
                
                # 跳过前几行标题
                start_index = 0
                header_patterns = ['Interface', '接口', 'Port', 'Port Name', 'Port-State', 'Vlan', 'IP-Address']
                for i, line in enumerate(lines):
                    if any(header in line.strip() for header in header_patterns):
                        start_index = i + 1
                        break
                
                # 定义接口名称正则表达式模式，支持带空格的格式
                interface_name_pattern = r'^(FastEthernet|GigabitEthernet|TenGigabitEthernet|Eth|Ethernet)\s+\d+(?:/\d+)*(?:\.\d+)?'
                
                for line in lines[start_index:]:
                    line = line.strip()
                    if not line or line.startswith('%') or line.startswith('#') or line.startswith('--') or line.startswith('==') or line.startswith('----'):
                        continue
                    
                    # 如果行中包含提示符，去除
                    if any(prompt in line for prompt in ['#', '>', '$', '%']):
                        for prompt in ['#', '>', '$', '%']:
                            if prompt in line:
                                line = line.split(prompt)[0].strip()
                    
                    # 专门处理带空格的接口名称格式
                    match = re.match(interface_name_pattern, line)
                    if match:
                        # 提取完整的接口名称
                        interface_name = match.group(0)
                        print(f"找到带空格的接口名称: {interface_name}")
                        
                        # 提取接口名称后面的信息
                        remaining_part = line[len(interface_name):].strip()
                        parts = remaining_part.split()
                        
                        # 构建接口信息
                        interface_info = {
                            'name': interface_name,
                            'status': parts[0] if parts else 'unknown',
                            'protocol': parts[1] if len(parts) >= 2 else 'unknown',
                            'description': ' '.join(parts[2:]) if len(parts) >= 3 else '',
                            'raw_info': line
                        }
                        
                        interfaces.append(interface_info)
                    else:
                        # 尝试常规的空格分割解析
                        parts = line.split()
                        if parts and len(parts) >= 2:
                            # 检查第一个部分是否是接口名称的一部分
                            simple_interface_pattern = r'^(FastEthernet|GigabitEthernet|TenGigabitEthernet|Eth|Ethernet)$'
                            if re.match(simple_interface_pattern, parts[0]):
                                # 这可能是一个带空格的接口名称
                                if len(parts) >= 2 and re.match(r'^\d+(?:/\d+)*(?:\.\d+)?$', parts[1]):
                                    interface_name = f"{parts[0]} {parts[1]}"
                                    print(f"组合接口名称: {interface_name}")
                                    
                                    remaining_parts = parts[2:]
                                    interface_info = {
                                        'name': interface_name,
                                        'status': remaining_parts[0] if remaining_parts else 'unknown',
                                        'protocol': remaining_parts[1] if len(remaining_parts) >= 2 else 'unknown',
                                        'description': ' '.join(remaining_parts[2:]) if len(remaining_parts) >= 3 else '',
                                        'raw_info': line
                                    }
                                    
                                    interfaces.append(interface_info)
            
            # 如果没有解析到接口信息，尝试更宽松的匹配模式
            if not interfaces and output and isinstance(output, str):
                print("尝试另一种更宽松的接口信息解析方式")
                # 尝试匹配每行以接口名称开头的模式（更宽松的匹配）- 支持带空格的格式
                interface_pattern = r'^(\S+Ethernet|Eth)\s+\d+'
                for line in output.split('\n'):
                    line = line.strip()
                    # 去除提示符
                    for prompt in ['#', '>', '$', '%']:
                        if prompt in line:
                            line = line.split(prompt)[0].strip()
                    
                    if line and not line.startswith('%') and not line.startswith('#') and not line.startswith('--'):
                        match = re.match(interface_pattern, line)
                        if match:
                            interface_name = match.group(0)
                            # 提取状态信息
                            remaining_part = line[len(interface_name):].strip()
                            status = remaining_part.split()[0] if remaining_part else 'unknown'
                            interfaces.append({
                                'name': interface_name,
                                'status': status,
                                'raw_info': line
                            })
            
            print(f"解析到的接口数量: {len(interfaces)}")
            
            # 如果还是没有解析到接口，尝试直接通过配置文件解析接口信息
            if not interfaces and hasattr(self, '_last_config') and self._last_config:
                print("尝试从配置文件中解析接口信息")
                config_lines = self._last_config.split('\n')
                interface_pattern = r'^interface\s+(\S+Ethernet|Eth)\s+\d+'
                for line in config_lines:
                    line = line.strip()
                    match = re.match(interface_pattern, line, re.I)
                    if match:
                        # 提取完整的接口名称
                        interface_name = ' '.join(line.split()[1:3])  # 提取interface后面的两个部分
                        # 检查接口是否已经存在
                        if not any(iface['name'] == interface_name for iface in interfaces):
                            interfaces.append({
                                'name': interface_name,
                                'status': 'unknown',
                                'source': 'config'
                            })
                
            print(f"最终解析到的接口数量: {len(interfaces)}")
            return interfaces
        except Exception as e:
            error_msg = f"获取锐捷接口信息失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_interface_status(self, interface: str) -> Dict[str, Any]:
        """获取指定接口状态 - 增强版"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            # 确保进入特权模式
            self._enter_privileged_mode()
            
            # 尝试多种接口状态命令
            interface_commands = [
                f'show interface {interface}',
                f'display interface {interface}',
                f'show interface {interface} status',
                f'show interfaces {interface}'
            ]
            
            output = ""
            
            for cmd in interface_commands:
                try:
                    output = self.execute_command(cmd)
                    if output and len(output) > 10 and 'Invalid input' not in output and 'Unknown command' not in output:
                        break
                except Exception:
                    continue
            
            if not output:
                raise Exception(f"无法获取接口 {interface} 的状态信息")
            
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
                'discards': 0,
                'input_errors': 0,
                'output_errors': 0,
                'last_clear': ''
            }
            
            # 解析接口描述
            desc_match = re.search(r'Description:\s*(.*?)\n', output)
            if desc_match:
                status['description'] = desc_match.group(1).strip()
            
            # 解析操作状态
            status_match = re.search(r'line\s+protocol\s+is\s+(\S+)', output, re.I)
            if status_match:
                status['oper_status'] = status_match.group(1)
            
            # 解析管理状态
            admin_match = re.search(r'\s+(administratively\s+)?down', output, re.I)
            if admin_match:
                if 'administratively' in admin_match.group(0).lower():
                    status['admin_status'] = 'admin down'
                else:
                    status['admin_status'] = 'down'
            else:
                status['admin_status'] = 'up'
            
            # 解析速率和双工模式
            speed_duplex_match = re.search(r'Speed:\s*(\S+),\s+Duplex:\s*(\S+)', output, re.I)
            if not speed_duplex_match:
                # 尝试其他格式
                speed_match = re.search(r'Speed:\s*(\S+)', output, re.I)
                duplex_match = re.search(r'Duplex:\s*(\S+)', output, re.I)
                if speed_match:
                    status['speed'] = speed_match.group(1)
                if duplex_match:
                    status['duplex'] = duplex_match.group(1)
            else:
                status['speed'] = speed_duplex_match.group(1)
                status['duplex'] = speed_duplex_match.group(2)
            
            # 解析MTU
            mtu_match = re.search(r'MTU\s+(\d+)', output, re.I)
            if mtu_match:
                status['mtu'] = mtu_match.group(1)
            
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
            input_errors_match = re.search(r'Input\s+errors:\s+(\d+)', output, re.I)
            output_errors_match = re.search(r'Output\s+errors:\s+(\d+)', output, re.I)
            
            if input_errors_match:
                status['input_errors'] = int(input_errors_match.group(1))
            if output_errors_match:
                status['output_errors'] = int(output_errors_match.group(1))
            
            # 总错误数
            status['errors'] = status['input_errors'] + status['output_errors']
            
            # 解析丢弃统计
            discards_match = re.search(r'Discard\s+packets\s*:\s*(\d+)', output, re.I)
            if discards_match:
                status['discards'] = int(discards_match.group(1))
            
            # 解析最后清空时间
            last_clear_match = re.search(r'Last\s+clear\s+of\s+counters:\s+(.*?)\n', output, re.I)
            if last_clear_match:
                status['last_clear'] = last_clear_match.group(1).strip()
            
            return status
        except Exception as e:
            error_msg = f"获取锐捷接口状态失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_config(self) -> str:
        """获取设备配置 - 增强版（优化超时处理和连接稳定性）"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            # 确保进入特权模式
            self._enter_privileged_mode()
            
            # 设置终端长度为0，避免分页 - 锐捷设备可能使用不同的命令
            term_length_commands = ['terminal length 0', 'screen-length 0 temporary']
            for term_cmd in term_length_commands:
                try:
                    self.execute_command(term_cmd)
                    print(f"成功设置终端长度: {term_cmd}")
                    break
                except Exception as term_e:
                    print(f"设置终端长度命令 '{term_cmd}' 失败: {str(term_e)}")
            
            # 锐捷设备获取配置的命令列表（按优先级排序）
            config_commands = [
                'show running-config',
                'display current-configuration',
                'show config',
                'show startup-config',
                'show startup-config all',
                'display current-configuration all'
            ]
            
            config = ""
            used_command = ""
            
            # 增加配置获取的超时时间（秒）
            config_timeout = 60  # 增加到60秒以处理大型配置
            
            # 尝试多种命令获取配置，增加重试机制
            max_cmd_retries = 2
            for cmd in config_commands:
                retry_count = 0
                while retry_count <= max_cmd_retries:
                    try:
                        # 执行配置命令，使用增加的超时时间
                        print(f"尝试锐捷配置命令: {cmd} (超时: {config_timeout}秒) [尝试 {retry_count+1}/{max_cmd_retries+1}]")
                        config = self.execute_command(cmd, timeout=config_timeout)
                        
                        # 对获取的配置进行更宽松的验证
                        if config and isinstance(config, str):
                            # 去除空白字符后检查长度
                            stripped_config = config.strip()
                            if len(stripped_config) > 50 and 'Invalid input' not in config and 'Unknown command' not in config:
                                used_command = cmd
                                print(f"使用命令 {cmd} 获取配置成功，配置长度: {len(config)} 字符")
                                return config
                            else:
                                print(f"配置不满足要求，长度: {len(stripped_config)} 字符")
                    except Exception as cmd_e:
                        print(f"执行命令 {cmd} 失败: {str(cmd_e)}")
                        # 如果是连接问题，尝试重新连接
                        if '远程主机强迫关闭' in str(cmd_e) or 'reset by peer' in str(cmd_e).lower():
                            print("检测到连接问题，尝试重新连接...")
                            try:
                                self.connect()
                                self._enter_privileged_mode()
                            except Exception as reconn_err:
                                print(f"重新连接失败: {str(reconn_err)}")
                    
                    retry_count += 1
                    if retry_count <= max_cmd_retries:
                        print(f"命令 {cmd} 准备重试...")
                        time.sleep(1)
                    else:
                        print(f"命令 {cmd} 达到最大重试次数")
            
            # 如果所有配置命令都失败，至少获取一些设备信息作为备选
            fallback_info = ""
            try:
                basic_info = self.execute_command('show version', timeout=15)
                if basic_info:
                    fallback_info = f"\n\n设备基础信息:\n{basic_info[:500]}..."
            except Exception:
                pass
            
            error_msg = f"获取的配置无效或为空，长度: {len(config) if isinstance(config, str) else 0} 字符"
            print(error_msg)
            raise Exception(error_msg + fallback_info)
            
            return config
        except Exception as e:
            error_msg = f"获取锐捷设备配置失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def save_config(self) -> bool:
        """保存设备配置 - 增强版"""
        if not self._check_connection():
            raise ConnectionError("设备连接失败")
        
        try:
            # 确保进入特权模式
            self._enter_privileged_mode()
            
            # 锐捷设备保存配置的命令
            save_commands = [
                'copy running-config startup-config',
                'write memory',
                'save',
                'save configuration'
            ]
            
            for cmd in save_commands:
                try:
                    print(f"尝试保存配置命令: {cmd}")
                    output = self.execute_command(cmd)
                    
                    # 检查保存是否成功
                    if output and isinstance(output, str):
                        # 锐捷设备的保存成功关键词
                        success_keywords = ['successfully', '成功', '已保存', 'complete']
                        
                        if any(keyword.lower() in output.lower() for keyword in success_keywords):
                            print(f"配置保存成功，使用命令: {cmd}")
                            return True
                        
                        # 有些设备可能需要确认保存
                        if 'confirm' in output.lower() or '确认' in output.lower():
                            print("需要确认保存，发送确认命令")
                            confirm_output = self.execute_command('y')
                            if any(keyword.lower() in confirm_output.lower() for keyword in success_keywords):
                                print("配置确认保存成功")
                                return True
                except Exception as cmd_e:
                    print(f"执行保存命令 {cmd} 失败: {str(cmd_e)}")
                    continue
            
            # 如果所有命令都失败，抛出异常
            raise Exception(f"保存配置失败，已尝试命令: {', '.join(save_commands)}")
        except Exception as e:
            error_msg = f"保存锐捷设备配置失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def execute_command(self, command: str, timeout: int = 10, expect_prompt: bool = True) -> str:
        """执行任意命令 - 增强版 (增强了连接稳定性和错误恢复能力)"""
        if not self._check_connection():
            # 尝试自动重新连接
            print("检测到连接已断开，尝试自动重新连接...")
            if not self.connect():
                raise ConnectionError("设备连接失败且无法重新连接")
        
        try:
            print(f"执行命令: {command} (超时: {timeout}秒)")
            
            # 清除可能的缓冲区内容
            try:
                self.connection.read_channel()
            except:
                pass
            
            # 首先尝试直接进入特权模式，防止后续命令执行失败
            self._enter_privileged_mode()
            
            # 记录开始时间，用于性能监控
            start_time = time.time()
            
            # 特殊处理连接稳定性问题 - 增加重试次数和更智能的错误处理
            max_retries = 3
            retry_count = 0
            response = ""
            
            while retry_count <= max_retries:
                try:
                    # 在执行命令前，先检查连接是否仍然有效
                    try:
                        # 发送一个无害的命令或回车来测试连接
                        self.connection.write_channel('\n')
                        time.sleep(0.2)
                        test_response = self.connection.read_channel()
                        if not test_response:
                            print("连接测试无响应，尝试重新初始化连接...")
                            self.connection = None
                            self.connected = False
                            if not self.connect():
                                raise ConnectionError("设备连接已失效且无法重新连接")
                            self._enter_privileged_mode()
                    except:
                        print("连接测试失败，尝试重新连接...")
                        self.connection = None
                        self.connected = False
                        if not self.connect():
                            raise ConnectionError("设备连接已失效且无法重新连接")
                        self._enter_privileged_mode()
                    
                    # 使用底层方法发送命令并读取响应
                    self.connection.write_channel(command + '\n')
                    
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
                                if expect_prompt and any(prompt in response for prompt in ['#', '>', '$', '%', '锐捷>', '锐捷#']):
                                    break
                            else:
                                # 短暂暂停以避免CPU占用过高
                                time.sleep(0.2)
                        except Exception as chunk_error:
                            print(f"读取响应块错误: {str(chunk_error)}")
                            # 如果是连接被重置的错误，尝试重新连接
                            if '远程主机强迫关闭' in str(chunk_error) or 'WinError 10054' in str(chunk_error) or 'reset by peer' in str(chunk_error).lower():
                                print("检测到连接被远程主机关闭，尝试重新连接...")
                                # 重置连接状态
                                self.connection = None
                                self.connected = False
                                if self.connect():
                                    print("重新连接成功，重新进入特权模式...")
                                    self._enter_privileged_mode()
                                else:
                                    print("重新连接失败，继续重试...")
                                retry_count += 1
                                break
                            break
                    
                    # 如果获取到了有效的响应，跳出重试循环
                    if response and len(response) > 0:
                        break
                    
                    retry_count += 1
                    if retry_count <= max_retries:
                        print(f"命令执行失败，准备第 {retry_count} 次重试...")
                        time.sleep(1)  # 等待1秒后重试
                except Exception as retry_error:
                    print(f"命令执行出错: {str(retry_error)}")
                    retry_count += 1
                    if retry_count <= max_retries:
                        print(f"准备第 {retry_count} 次重试...")
                        time.sleep(1)
                    else:
                        raise
            
            # 计算执行时间
            exec_time = time.time() - start_time
            
            # 清理响应内容
            if response:
                # 去除命令回显
                if response.startswith(command):
                    response = response[len(command):]
                
                # 去除尾部提示符
                if expect_prompt:
                    prompt_patterns = [
                        r'\s*[>%#]\s*$', 
                        r'\s*[>%#][^\n]*$',
                        r'\s*[\r\n]+[>%#]\s*$'
                    ]
                    for pattern in prompt_patterns:
                        response = re.sub(pattern, '', response, flags=re.MULTILINE)
                
                # 去除多余的空行和空白字符
                response = '\n'.join([line.strip() for line in response.split('\n') if line.strip()])
                
                # 检查是否存在访问权限问题，再次尝试进入特权模式
                if any(deny_keyword in response.lower() for deny_keyword in ['access denied', '权限不足', '未授权', 'privilege denied']):
                    print(f"检测到访问权限问题，再次尝试进入特权模式...")
                    
                    # 再次尝试进入特权模式
                    self._enter_privileged_mode()
                    
                    # 清除缓冲区
                    try:
                        self.connection.read_channel()
                    except:
                        pass
                    
                    # 重新执行命令
                    print(f"重新执行命令: {command}")
                    self.connection.write_channel(command + '\n')
                    
                    # 重新读取响应
                    response = ""
                    retry_timeout = time.time() + timeout
                    while time.time() < retry_timeout:
                        try:
                            chunk = self.connection.read_channel()
                            if chunk:
                                response += chunk
                                retry_timeout = time.time() + timeout
                                if expect_prompt and any(prompt in response for prompt in ['#', '>', '$', '%']):
                                    break
                            else:
                                time.sleep(0.2)
                        except:
                            break
                    
                    # 清理重新执行的响应
                    if response:
                        if response.startswith(command):
                            response = response[len(command):]
                        response = '\n'.join([line.strip() for line in response.split('\n') if line.strip()])
            
            print(f"命令执行结果长度: {len(response)} 字符, 执行时间: {exec_time:.2f}秒")
            # 如果响应长度太短，打印前几个字符用于调试
            if len(response) < 100:
                print(f"命令执行结果: {response}")
            
            return response
        except Exception as e:
            # 特殊处理常见错误
            error_msg = str(e)
            if 'timed out' in error_msg.lower():
                print(f"命令 '{command}' 执行超时，请检查设备响应或增加超时时间")
            elif 'permission denied' in error_msg.lower() or 'not authorized' in error_msg.lower():
                print(f"命令 '{command}' 权限不足，尝试重新进入特权模式...")
                # 尝试重新进入特权模式
                try:
                    self._enter_privileged_mode()
                    # 重试命令
                    return self.execute_command(command, timeout, expect_prompt)
                except:
                    pass
            
            error_msg = f"执行锐捷设备命令失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)