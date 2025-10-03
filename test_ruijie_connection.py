#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试锐捷设备连接 - 使用修改后的RuijieAdapter"""

import sys
import os
import time
from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.adapters.ruijie import RuijieAdapter

# 锐捷设备信息
ruijie_device = {
    'management_ip': '192.168.121.51',  # 用户报告的故障设备IP
    'username': 'admin',  # 用户名
    'password': '520131xiao',  # 用户提到的密码
    'port': 23  # 端口号
}

def test_with_ruijie_adapter(device_info):
    """使用修改后的RuijieAdapter测试连接"""
    print(f"\n=== 使用修改后的RuijieAdapter测试连接: {device_info['management_ip']}:{device_info['port']} ===")
    
    success = False
    
    try:
        # 创建RuijieAdapter实例
        adapter = RuijieAdapter(device_info)
        
        start_time = time.time()
        
        # 尝试连接设备
        print(f"尝试连接到设备...")
        success = adapter.connect()
        
        if success:
            print(f"✅ 连接成功！耗时: {time.time() - start_time:.2f}秒")
            
            # 尝试获取设备信息
            try:
                print("\n尝试获取设备信息...")
                device_info_result = adapter.get_device_info()
                print(f"✅ 设备信息获取成功")
                print(f"设备型号: {device_info_result.get('model', '未知')}")
                print(f"软件版本: {device_info_result.get('version', '未知')}")
            except Exception as e:
                print(f"❌ 获取设备信息时发生错误: {str(e)}")
                
            # 尝试获取接口列表
            try:
                print("\n尝试获取接口列表...")
                interfaces = adapter.get_interfaces()
                print(f"✅ 接口列表获取成功，共 {len(interfaces)} 个接口")
                # 打印前5个接口
                for i, interface in enumerate(interfaces[:5]):
                    print(f"  {i+1}. {interface.get('name', '未知')} - {interface.get('description', '无描述')}")
            except Exception as e:
                print(f"❌ 获取接口列表时发生错误: {str(e)}")
                
            # 断开连接
            adapter.disconnect()
            print("\n设备连接已断开")
        else:
            print(f"❌ 设备连接失败！耗时: {time.time() - start_time:.2f}秒")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n=== RuijieAdapter测试完成 ===")
    return success

def test_with_netmiko(device_info):
    """使用netmiko直接测试锐捷设备连接（对比测试）"""
    print(f"\n=== 使用netmiko直接测试连接: {device_info['management_ip']}:{device_info['port']} ===")
    
    # 定义要尝试的设备类型组合
    test_combinations = [
        ('telnet', 23, 'generic_telnet'),
        ('telnet', 23, 'ruijie_os'),
        ('telnet', 23, 'cisco_ios_telnet'),
    ]
    
    # 基础连接参数
    base_params = {
        'ip': device_info['management_ip'],
        'username': device_info['username'],
        'password': device_info['password'],
        'global_delay_factor': 2,
        'read_timeout_override': 10,
        'banner_timeout': 15
    }
    
    success = False
    
    for protocol, port, device_type in test_combinations:
        try:
            params = base_params.copy()
            params['port'] = port
            params['device_type'] = device_type
            
            print(f"\n尝试连接: 协议={protocol}, 端口={port}, 设备类型={device_type}")
            start_time = time.time()
            
            # 建立连接
            connection = ConnectHandler(**params)
            
            # 验证连接是否成功
            prompt = connection.find_prompt()
            if prompt:
                print(f"✅ 连接成功！设备提示符: {prompt}")
                print(f"连接耗时: {time.time() - start_time:.2f}秒")
                
                # 尝试获取设备信息
                try:
                    output = connection.send_command('show version', read_timeout=10)
                    print(f"\n设备信息预览:")
                    for line in output.split('\n')[:5]:
                        print(f"  {line.strip()}")
                except Exception as cmd_e:
                    print(f"执行命令失败: {str(cmd_e)}")
                
                connection.disconnect()
                success = True
                break
        except NetMikoTimeoutException:
            print(f"❌ 连接超时")
        except NetMikoAuthenticationException:
            print(f"❌ 认证失败")
        except Exception as e:
            print(f"❌ 连接失败: {str(e)}")
    
    if not success:
        print(f"\n❌ 所有netmiko连接方式均失败")
    
    print("\n=== netmiko测试完成 ===")
    return success


if __name__ == "__main__":
    print("\n=====================================================================")
    print("锐捷设备连接测试套件 - 验证修改后的RuijieAdapter是否解决连接问题")
    print("=====================================================================")
    
    # 先使用修改后的RuijieAdapter测试
    adapter_success = test_with_ruijie_adapter(ruijie_device)
    
    # 然后使用netmiko直接测试作为对比
    netmiko_success = test_with_netmiko(ruijie_device)
    
    print("\n=====================================================================")
    print("测试结果汇总:")
    print(f"- RuijieAdapter连接: {'成功' if adapter_success else '失败'}")
    print(f"- netmiko直接连接: {'成功' if netmiko_success else '失败'}")
    print("=====================================================================")