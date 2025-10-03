# -*- coding: utf-8 -*-
"""
基础Telnet连接测试脚本
用于直接测试锐捷设备的网络连接和Telnet端口状态，绕过适配器的复杂性
"""

import socket
import time
import logging
import subprocess
from typing import Dict, Tuple, Optional, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_telnet_connection')


class TelnetConnectionTester:
    """Telnet连接测试器"""
    
    def __init__(self):
        """初始化测试器"""
        # 测试设备信息
        self.devices_to_test = [
            {
                'name': '锐捷测试设备1',
                'ip': '192.168.121.51',
                'port': 23,
                'timeout': 5  # 5秒超时
            }
        ]
    
    def ping_host(self, ip: str, count: int = 4) -> bool:
        """
        使用系统ping命令测试主机连通性
        
        Args:
            ip: 目标IP地址
            count: ping次数
            
        Returns:
            是否能够ping通
        """
        logger.info(f"开始ping测试: {ip}")
        
        try:
            # 根据操作系统构建ping命令
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', str(count), ip]
            else:
                cmd = ['ping', '-c', str(count), ip]
            
            # 执行ping命令
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            # 检查ping结果
            if result.returncode == 0:
                logger.info(f"ping {ip} 成功")
                return True
            else:
                logger.warning(f"ping {ip} 失败，返回码: {result.returncode}")
                logger.debug(f"ping输出: {result.stdout}")
                return False
        except subprocess.TimeoutExpired:
            logger.error(f"ping {ip} 超时")
            return False
        except Exception as e:
            logger.error(f"ping {ip} 时发生错误: {str(e)}")
            return False
    
    def test_tcp_port(self, ip: str, port: int, timeout: int = 3) -> Tuple[bool, Optional[str]]:
        """
        测试TCP端口是否开放
        
        Args:
            ip: 目标IP地址
            port: 目标端口
            timeout: 超时时间（秒）
            
        Returns:
            (是否开放, 错误信息)
        """
        logger.info(f"开始测试TCP端口: {ip}:{port}")
        
        sock = None
        try:
            # 创建TCP套接字
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            # 记录开始时间
            start_time = time.time()
            
            # 尝试连接
            result = sock.connect_ex((ip, port))
            
            # 计算连接时间
            connect_time = time.time() - start_time
            
            # 检查结果
            if result == 0:
                logger.info(f"TCP端口 {ip}:{port} 开放，连接时间: {connect_time:.3f}秒")
                return True, None
            else:
                error_msg = f"TCP端口 {ip}:{port} 关闭或被阻止，错误码: {result}"
                logger.warning(error_msg)
                return False, error_msg
        except socket.timeout:
            error_msg = f"连接TCP端口 {ip}:{port} 超时"
            logger.error(error_msg)
            return False, error_msg
        except socket.error as e:
            error_msg = f"连接TCP端口 {ip}:{port} 时发生套接字错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"测试TCP端口 {ip}:{port} 时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    def test_raw_telnet_connection(self, ip: str, port: int, timeout: int = 5) -> Dict[str, Any]:
        """
        测试原始Telnet连接，获取初始响应
        
        Args:
            ip: 目标IP地址
            port: 目标端口
            timeout: 超时时间（秒）
            
        Returns:
            测试结果
        """
        result = {
            'success': False,
            'response': '',
            'time_used': 0,
            'error': None
        }
        
        logger.info(f"开始原始Telnet连接测试: {ip}:{port}")
        
        sock = None
        try:
            # 创建TCP套接字
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            # 记录开始时间
            start_time = time.time()
            
            # 尝试连接
            sock.connect((ip, port))
            logger.info(f"成功连接到 {ip}:{port}")
            
            # 设置接收缓冲区大小
            sock.settimeout(timeout)
            
            # 尝试接收初始响应
            # 注意：这里我们只读取最多1024字节的初始数据，实际的Telnet协议要复杂得多
            # 这只是一个基本的连通性和响应测试
            response = b''
            try:
                # 有些设备可能需要先发送一个回车才能获取响应
                sock.send(b'\r\n')
                time.sleep(0.5)
                
                # 尝试多次读取，确保获取到足够的响应
                for _ in range(3):
                    try:
                        chunk = sock.recv(1024)
                        if not chunk:
                            break
                        response += chunk
                    except socket.timeout:
                        break
                    time.sleep(0.2)
            except Exception as e:
                logger.warning(f"接收初始响应时出错: {str(e)}")
            
            # 解析响应
            try:
                # 尝试以UTF-8编码解析，如果失败则使用Latin-1
                decoded_response = response.decode('utf-8')
            except UnicodeDecodeError:
                decoded_response = response.decode('latin-1')
            
            # 记录结果
            result['success'] = True
            result['response'] = decoded_response.strip()
            result['time_used'] = time.time() - start_time
            
            logger.info(f"原始Telnet连接测试成功，响应: {repr(result['response'])}")
            logger.debug(f"完整响应长度: {len(response)}字节")
            
        except socket.timeout:
            error_msg = f"原始Telnet连接 {ip}:{port} 超时"
            logger.error(error_msg)
            result['error'] = error_msg
        except socket.error as e:
            error_msg = f"原始Telnet连接 {ip}:{port} 时发生套接字错误: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
        except Exception as e:
            error_msg = f"原始Telnet连接测试时发生错误: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
        
        return result
    
    def test_device(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个设备"""
        result = {
            'device': device,
            'tests': [],
            'summary': {
                'all_tests_passed': False,
                'passed_count': 0,
                'total_count': 3  # ping, tcp_port, raw_telnet
            }
        }
        
        ip = device['ip']
        port = device['port']
        
        logger.info(f"开始测试设备: {device['name']} ({ip}:{port})")
        
        # 1. Ping测试
        ping_result = {
            'name': 'Ping测试',
            'success': False,
            'details': ''
        }
        success = self.ping_host(ip)
        ping_result['success'] = success
        ping_result['details'] = f"{'成功' if success else '失败'}"
        result['tests'].append(ping_result)
        
        # 只有Ping成功才进行后续测试
        if success:
            # 2. TCP端口测试
            tcp_result = {
                'name': 'TCP端口测试',
                'success': False,
                'details': ''
            }
            port_success, port_error = self.test_tcp_port(ip, port)
            tcp_result['success'] = port_success
            tcp_result['details'] = f"{'成功' if port_success else f'失败: {port_error}'}"
            result['tests'].append(tcp_result)
            
            # 3. 原始Telnet连接测试
            if port_success:
                raw_telnet_result = {
                    'name': '原始Telnet连接测试',
                    'success': False,
                    'details': ''
                }
                raw_result = self.test_raw_telnet_connection(ip, port, device['timeout'])
                raw_telnet_result['success'] = raw_result['success']
                if raw_result['success']:
                    # 截断过长的响应
                    response_preview = (raw_result['response'][:100] + '...') if len(raw_result['response']) > 100 else raw_result['response']
                    raw_telnet_result['details'] = f"成功，响应预览: {repr(response_preview)}, 耗时: {raw_result['time_used']:.3f}秒"
                else:
                    raw_telnet_result['details'] = f"失败: {raw_result.get('error', '未知错误')}"
                result['tests'].append(raw_telnet_result)
        
        # 计算统计信息
        passed_count = sum(1 for test in result['tests'] if test['success'])
        result['summary']['passed_count'] = passed_count
        result['summary']['all_tests_passed'] = passed_count == result['summary']['total_count']
        
        # 打印测试结果
        self._print_test_result(result)
        
        return result
    
    def _print_test_result(self, result: Dict[str, Any]):
        """打印测试结果"""
        device = result['device']
        logger.info(f"\n===== 设备测试结果: {device['name']} ({device['ip']}:{device['port']}) =====")
        
        for test in result['tests']:
            status = "✅ 成功" if test['success'] else "❌ 失败"
            logger.info(f"{status} - {test['name']}: {test['details']}")
        
        summary = result['summary']
        overall_status = "✅ 所有测试通过" if summary['all_tests_passed'] else "❌ 测试未全部通过"
        logger.info(f"\n总体结果: {overall_status}")
        logger.info(f"通过测试数: {summary['passed_count']}/{summary['total_count']}")
        logger.info("=========================================")
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("===== 开始Telnet连接测试 ====")
        
        results = []
        for device in self.devices_to_test:
            result = self.test_device(device)
            results.append(result)
        
        logger.info("===== Telnet连接测试结束 ====")
        
        return results


def main():
    """主函数"""
    try:
        tester = TelnetConnectionTester()
        results = tester.run_all_tests()
        
        # 检查是否有测试结果
        if results:
            # 获取第一个设备的测试结果
            first_result = results[0]
            summary = first_result['summary']
            device = first_result['device']
            
            print("\n===== Telnet连接测试报告 =====")
            print(f"设备: {device['name']} ({device['ip']}:{device['port']})")
            print(f"测试结果: {'通过' if summary['all_tests_passed'] else '未通过'}")
            print(f"通过测试数: {summary['passed_count']}/{summary['total_count']}")
            
            # 打印详细测试结果
            print("\n详细测试结果:")
            for test in first_result['tests']:
                status = "成功" if test['success'] else "失败"
                print(f"- {test['name']}: {status}")
                print(f"  {test['details']}")
            
            # 分析问题
            print("\n===== 问题分析 =====")
            
            # 检查ping测试
            ping_test = next((t for t in first_result['tests'] if t['name'] == 'Ping测试'), None)
            if ping_test and not ping_test['success']:
                print("1. 网络连通性问题：")
                print("   - 设备可能已关机或断开网络连接")
                print("   - 网络中可能存在防火墙阻止ICMP流量")
                print("   - IP地址配置错误")
            else:
                print("1. 网络连通性正常")
                
                # 检查TCP端口测试
                tcp_test = next((t for t in first_result['tests'] if t['name'] == 'TCP端口测试'), None)
                if tcp_test and not tcp_test['success']:
                    print("2. Telnet服务问题：")
                    print("   - 设备上的Telnet服务可能未启用")
                    print("   - 网络中可能存在防火墙阻止TCP 23端口流量")
                    print("   - 设备可能配置为只允许特定IP访问Telnet")
                else:
                    print("2. Telnet端口连接正常")
                    
                    # 检查原始Telnet连接测试
                    raw_telnet_test = next((t for t in first_result['tests'] if t['name'] == '原始Telnet连接测试'), None)
                    if raw_telnet_test and not raw_telnet_test['success']:
                        print("3. Telnet协议问题：")
                        print("   - 设备的Telnet服务可能使用了特殊的认证方式或协议变体")
                        print("   - 设备可能配置了访问控制列表限制连接")
                    else:
                        print("3. 原始Telnet连接测试通过")
                        print("\n建议：")
                        print("- 如果所有测试都通过，但适配器仍然无法连接，可能是适配器的认证流程与设备不匹配")
                        print("- 请检查设备的Telnet配置和认证方式")
                        print("- 可能需要修改适配器的认证逻辑或设备类型设置")
            
            print("======================")
        
    except Exception as e:
        logger.error(f"测试过程中发生严重错误: {str(e)}")
        print(f"\n测试过程中发生错误: {str(e)}")


# 导入platform模块（移到这里以避免在导入时出错）
import platform


if __name__ == "__main__":
    main()


__all__ = ['TelnetConnectionTester']