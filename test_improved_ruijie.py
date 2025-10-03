#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入锐捷适配器
from app.adapters.ruijie import RuijieAdapter

class RuijieAdapterTester:
    def __init__(self):
        # 设备连接信息 - 注意：RuijieAdapter接受device_info字典作为参数
        self.device_info = {
            'management_ip': '192.168.121.51',  # 使用management_ip而不是host
            'port': 23,  # 使用telnet端口
            'username': 'admin',
            'password': '520131xiao',
            'protocol': 'telnet',  # 使用telnet协议
            'vendor': 'ruijie'
        }
        
        # 初始化适配器
        self.adapter = None
        
        # 测试结果
        self.results = {
            'success': False,
            'steps': [],
            'error': None
        }
    
    def log_step(self, step_name, success=True, message=None):
        """记录测试步骤结果"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        self.results['steps'].append({
            'timestamp': timestamp,
            'name': step_name,
            'success': success,
            'message': message
        })
        
        status = '成功' if success else '失败'
        print(f"[{timestamp}] 步骤: {step_name} - {status}")
        if message:
            print(f"      信息: {message}")
    
    def initialize_adapter(self):
        """初始化适配器"""
        try:
            # RuijieAdapter接受device_info字典作为单个参数
            self.adapter = RuijieAdapter(self.device_info)
            self.log_step("初始化适配器", success=True, 
                         message=f"已初始化锐捷设备适配器，连接信息: {self.device_info['management_ip']}:{self.device_info['port']}")
            return True
        except Exception as e:
            self.log_step("初始化适配器", success=False, message=f"初始化失败: {str(e)}")
            self.results['error'] = str(e)
            return False
    
    def connect_to_device(self):
        """连接到设备"""
        try:
            start_time = time.time()
            print(f"连接参数 - 用户名: {self.device_info['username']}, 协议: {self.device_info['protocol']}")
            self.adapter.connect()
            elapsed_time = time.time() - start_time
            self.log_step("连接设备", success=True, 
                         message=f"成功连接到设备 {self.device_info['management_ip']}:{self.device_info['port']}，耗时: {elapsed_time:.2f}秒")
            
            # 检查连接状态并进行简单测试
            if hasattr(self.adapter, 'connection') and self.adapter.connection:
                try:
                    # 尝试一个简单的命令测试连接质量
                    print("连接成功后尝试执行'?'命令")
                    self.adapter.connection.write_channel('?' + '\n')
                    time.sleep(0.5)
                    response = self.adapter.connection.read_channel()
                    if response:
                        print(f"连接质量测试通过，收到响应长度: {len(response)}")
                    else:
                        print("连接质量测试: 未收到响应")
                except Exception as e:
                    print(f"连接质量测试异常: {str(e)}")
            
            return True
        except Exception as e:
            self.log_step("连接设备", success=False, message=f"连接失败: {str(e)}")
            self.results['error'] = str(e)
            return False
    
    def get_device_info(self):
        """获取设备信息"""
        try:
            device_info = self.adapter.get_device_info()
            # 打印部分关键信息
            if device_info:
                info_summary = f"型号: {device_info.get('model', '未知')}, 版本: {device_info.get('version', '未知')}"
                self.log_step("获取设备信息", success=True, message=info_summary)
                print(f"设备详细信息: {device_info}")
            return True
        except Exception as e:
            self.log_step("获取设备信息", success=False, message=f"获取失败: {str(e)}")
            return False
    
    def get_config(self):
        """获取设备配置"""
        try:
            start_time = time.time()
            config = self.adapter.get_config()
            elapsed_time = time.time() - start_time
            
            # 检查配置是否有效
            if config and isinstance(config, str) and len(config) > 100:
                self.log_step("获取设备配置", success=True, 
                             message=f"配置获取成功，长度: {len(config)} 字符，耗时: {elapsed_time:.2f}秒")
                
                # 保存配置到文件
                config_file = f"ruijie_config_{self.device_info['management_ip']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write(config)
                self.log_step("保存配置到文件", success=True, message=f"配置已保存到 {config_file}")
                
                # 打印配置的前100个字符作为预览
                config_preview = config[:200].replace('\n', '\\n')
                print(f"配置预览: {config_preview}...")
                return True
            else:
                self.log_step("获取设备配置", success=False, 
                             message=f"获取的配置无效或太短，长度: {len(config) if isinstance(config, str) else 0} 字符")
                return False
        except Exception as e:
            self.log_step("获取设备配置", success=False, message=f"获取失败: {str(e)}")
            self.results['error'] = str(e)
            return False
    
    def disconnect(self):
        """断开连接"""
        try:
            self.adapter.disconnect()
            self.log_step("断开连接", success=True, message="已成功断开与设备的连接")
            return True
        except Exception as e:
            self.log_step("断开连接", success=False, message=f"断开连接失败: {str(e)}")
            return False
    
    def test_execute_command(self):
        """测试执行命令功能"""
        try:
            commands_to_test = [
                'show version',
                'show interface brief',
                'show running-config | include hostname'
            ]
            
            for cmd in commands_to_test:
                print(f"\n测试命令: {cmd}")
                result = self.adapter.execute_command(cmd)
                if result and len(result) > 0:
                    print(f"命令执行成功，结果长度: {len(result)} 字符")
                    print(f"结果预览: {result[:150].replace('\n', '\\n')}...")
                else:
                    print(f"命令执行结果为空或无效")
            
            self.log_step("测试命令执行", success=True, message=f"成功测试了 {len(commands_to_test)} 个命令")
            return True
        except Exception as e:
            self.log_step("测试命令执行", success=False, message=f"测试失败: {str(e)}")
            return False
    
    def run_full_test(self):
        """运行完整测试流程"""
        print("\n========== 锐捷设备适配器测试开始 ==========")
        print(f"测试目标: {self.device_info['management_ip']}:{self.device_info['port']}")
        print(f"协议: {self.device_info['protocol']}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("==========================================")
        
        # 执行测试步骤
        steps = [
            self.initialize_adapter,
            self.connect_to_device,
            self.test_execute_command,
            self.get_device_info,
            self.get_config,
            self.disconnect
        ]
        
        # 执行每个步骤，如果失败则停止
        all_success = True
        for step in steps:
            if not step():
                all_success = False
                # 即使前面步骤失败，也要尝试断开连接
                if step != self.disconnect:
                    try:
                        if self.adapter:
                            self.adapter.disconnect()
                    except:
                        pass
                break
        
        # 测试总结
        print("\n========== 测试总结 ==========")
        if all_success:
            self.results['success'] = True
            print("✅ 所有测试步骤均成功完成！")
        else:
            self.results['success'] = False
            print(f"❌ 测试失败！错误信息: {self.results.get('error', '未知错误')}")
        
        print(f"总测试步骤数: {len(self.results['steps'])}")
        success_steps = sum(1 for step in self.results['steps'] if step['success'])
        print(f"成功步骤数: {success_steps}")
        print(f"失败步骤数: {len(self.results['steps']) - success_steps}")
        print("==========================================")
        
        return all_success

if __name__ == "__main__":
    tester = RuijieAdapterTester()
    success = tester.run_full_test()
    
    # 根据测试结果设置退出码
    sys.exit(0 if success else 1)