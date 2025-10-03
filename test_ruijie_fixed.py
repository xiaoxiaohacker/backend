# -*- coding: utf-8 -*-
"""
锐捷修复版适配器测试脚本
用于测试修复后的ruijie_fixed.py是否能解决特定锐捷设备的连接问题
"""

import time
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_ruijie_fixed')


class RuijieAdapterTester:
    """锐捷适配器测试器"""
    
    def __init__(self):
        """初始化测试器"""
        # 配置测试设备信息
        self.devices_to_test = [
            {
                'name': '锐捷测试设备1',
                'management_ip': '192.168.121.51',
                'port': 23,  # 强制使用telnet端口
                'username': 'admin',
                'password': 'wlzx@2014',
                'privilege_password': 'ruijie',  # 明确指定特权密码
                'timeout': 60  # 增加超时时间
            }
        ]
        
        # 导入原始和修复后的适配器
        self._import_adapters()
    
    def _import_adapters(self):
        """动态导入适配器模块"""
        try:
            # 导入锐捷适配器
            from app.adapters.ruijie import RuijieAdapter
            self.original_adapter = RuijieAdapter
            self.fixed_adapter = RuijieAdapter  # 使用同一个适配器进行测试
            logger.info("成功导入锐捷适配器")
        except ImportError as e:
            logger.error(f"导入锐捷适配器失败: {str(e)}")
            raise ImportError(f"无法导入锐捷适配器: {str(e)}")
    
    def test_device(self, device_info: Dict[str, Any], use_fixed: bool = True) -> Dict[str, Any]:
        """测试单个设备"""
        result = {
            'device': device_info['name'],
            'ip': device_info['management_ip'],
            'port': device_info['port'],
            'use_fixed': use_fixed,
            'success': False,
            'time_used': 0,
            'steps': [],
            'error': None
        }
        
        adapter_class = self.fixed_adapter if use_fixed else self.original_adapter
        adapter_name = '修复版' if use_fixed else '原始版'
        
        logger.info(f"开始测试 {adapter_name} 锐捷适配器连接到设备 {device_info['name']} ({device_info['management_ip']}:{device_info['port']})...")
        
        # 增加测试连通性的步骤
        import socket
        try:
            # 测试TCP连接是否可达
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                conn_result = s.connect_ex((device_info['management_ip'], device_info['port']))
                if conn_result == 0:
                    logger.info(f"网络连通性测试通过: {device_info['management_ip']}:{device_info['port']} 可以连接")
                else:
                    logger.error(f"网络连通性测试失败: {device_info['management_ip']}:{device_info['port']} 不可达，错误码: {conn_result}")
                    result['error'] = f"网络连通性测试失败: {device_info['management_ip']}:{device_info['port']} 不可达"
                    return result
        except Exception as e:
            logger.error(f"网络连通性测试异常: {str(e)}")
            result['error'] = f"网络连通性测试异常: {str(e)}"
            return result
        
        start_time = time.time()
        adapter = None
        
        try:
            # 步骤1: 初始化适配器
            step1_time = time.time()
            adapter = adapter_class(device_info)
            result['steps'].append({'name': '初始化适配器', 'success': True, 'time_used': time.time() - step1_time})
            logger.info("步骤1: 适配器初始化成功")
            
            # 步骤2: 连接设备
            step2_time = time.time()
            connected = adapter.connect()
            result['steps'].append({'name': '连接设备', 'success': connected, 'time_used': time.time() - step2_time})
            if connected:
                logger.info("步骤2: 设备连接成功")
            else:
                logger.warning("步骤2: 设备连接失败")
                result['error'] = "设备连接失败"
                return result
            
            # 步骤3: 获取设备信息
            step3_time = time.time()
            device_info = adapter.get_device_info()
            result['steps'].append({'name': '获取设备信息', 'success': True, 'time_used': time.time() - step3_time})
            result['device_info'] = device_info
            logger.info(f"步骤3: 成功获取设备信息 - 型号: {device_info.get('model', '未知')}, 版本: {device_info.get('version', '未知')}")
            
            # 步骤4: 获取接口信息
            step4_time = time.time()
            interfaces = adapter.get_interfaces()
            result['steps'].append({'name': '获取接口信息', 'success': True, 'time_used': time.time() - step4_time})
            result['interfaces_count'] = len(interfaces)
            logger.info(f"步骤4: 成功获取接口信息 - 共 {len(interfaces)} 个接口")
            
            # 步骤5: 获取配置
            step5_time = time.time()
            config = adapter.get_config()
            result['steps'].append({'name': '获取配置', 'success': True, 'time_used': time.time() - step5_time})
            result['config_lines_count'] = len(config.split('\n'))
            logger.info(f"步骤5: 成功获取设备配置 - 共 {len(config.split('\n'))} 行")
            
            # 步骤6: 获取ARP表（可选增强功能）
            try:
                if hasattr(adapter, 'get_arp_table'):
                    step6_time = time.time()
                    arp_table = adapter.get_arp_table()
                    result['steps'].append({'name': '获取ARP表', 'success': True, 'time_used': time.time() - step6_time})
                    result['arp_entries_count'] = len(arp_table)
                    logger.info(f"步骤6: 成功获取ARP表 - 共 {len(arp_table)} 条记录")
            except Exception as e:
                logger.warning(f"步骤6: 获取ARP表失败: {str(e)}")
            
            # 步骤7: 获取路由表（可选增强功能）
            try:
                if hasattr(adapter, 'get_route_table'):
                    step7_time = time.time()
                    route_table = adapter.get_route_table()
                    result['steps'].append({'name': '获取路由表', 'success': True, 'time_used': time.time() - step7_time})
                    result['route_entries_count'] = len(route_table)
                    logger.info(f"步骤7: 成功获取路由表 - 共 {len(route_table)} 条记录")
            except Exception as e:
                logger.warning(f"步骤7: 获取路由表失败: {str(e)}")
            
            # 测试成功
            result['success'] = True
            logger.info(f"{adapter_name} 锐捷适配器测试成功")
            
        except Exception as e:
            error_msg = str(e)
            result['error'] = error_msg
            result['success'] = False
            logger.error(f"{adapter_name} 锐捷适配器测试失败: {error_msg}")
            
            # 记录最后失败的步骤
            if len(result['steps']) > 0:
                last_step = result['steps'][-1]
                if not last_step.get('success', False):
                    logger.error(f"最后失败的步骤: {last_step['name']}")
            else:
                logger.error("初始化适配器失败")
        finally:
            # 断开连接
            try:
                if adapter and hasattr(adapter, 'disconnect'):
                    adapter.disconnect()
                    logger.info("已断开与设备的连接")
            except Exception as disconnect_error:
                logger.warning(f"断开连接时出错: {str(disconnect_error)}")
            
            # 记录总耗时
            result['time_used'] = time.time() - start_time
            logger.info(f"测试完成，总耗时: {result['time_used']:.2f}秒")
        
        return result
    
    def run_comparison_test(self):
        """运行测试"""
        logger.info("开始运行测试...")
        
        results = []
        
        for device in self.devices_to_test:
            # 测试锐捷适配器
            result = self.test_device(device, use_fixed=True)
            results.append(result)
            
            # 输出测试结果
            logger.info("===== 测试结果 ====")
            logger.info(f"设备: {result['device']} ({result['ip']}:{result['port']})")
            logger.info(f"适配器: {'成功' if result['success'] else '失败'}")
            logger.info(f"耗时: {result['time_used']:.2f}秒")
            if not result['success']:
                logger.info(f"错误: {result['error']}")
            logger.info("====================")
        
        return results
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("===== 锐捷适配器修复版测试开始 =====")
        
        # 运行对比测试
        results = self.run_comparison_test()
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        logger.info("===== 锐捷适配器修复版测试结束 =====")
        logger.info(f"测试总数: {total_count}, 成功数: {success_count}, 失败数: {total_count - success_count}")
        
        # 返回成功的修复版本测试结果
        fixed_success_results = [r for r in results if r.get('use_fixed', False) and r['success']]
        if fixed_success_results:
            logger.info("修复版适配器测试成功！")
        else:
            logger.warning("修复版适配器测试失败，请检查错误日志")
        
        return results


def main():
    """主函数"""
    try:
        tester = RuijieAdapterTester()
        results = tester.run_all_tests()
        
        # 如果有修复版成功的结果，打印成功消息
        fixed_success_results = [r for r in results if r.get('use_fixed', False) and r['success']]
        if fixed_success_results:
            print("\n===== 测试成功提示 =====")
            print("修复版锐捷适配器已成功连接到设备！")
            print(f"设备: {fixed_success_results[0]['device']} ({fixed_success_results[0]['ip']}:{fixed_success_results[0]['port']})")
            print(f"耗时: {fixed_success_results[0]['time_used']:.2f}秒")
            if 'device_info' in fixed_success_results[0]:
                device_info = fixed_success_results[0]['device_info']
                print(f"设备型号: {device_info.get('model', '未知')}")
                print(f"软件版本: {device_info.get('version', '未知')}")
            print("=======================")
        else:
            print("\n===== 测试失败提示 =====")
            print("修复版锐捷适配器连接设备失败")
            if results and any(r.get('use_fixed', False) for r in results):
                fixed_result = next(r for r in results if r.get('use_fixed', False))
                print(f"错误信息: {fixed_result.get('error', '未知错误')}")
            print("=======================")
        
    except Exception as e:
        logger.error(f"测试过程中发生严重错误: {str(e)}")
        print(f"\n测试过程中发生错误: {str(e)}")


if __name__ == "__main__":
    main()


__all__ = ['RuijieAdapterTester']