import os
import sys
import logging
import json
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.adapters.ruijie import RuijieAdapter
from app.services.adapter_manager import AdapterManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ruijie_adapter_direct(device_info: Dict[str, Any]):
    """直接测试RuijieAdapter类的连接和配置获取功能"""
    logger.info(f"\n===== 开始直接测试RuijieAdapter =====")
    logger.info(f"设备IP: {device_info['management_ip']}")
    logger.info(f"端口: {device_info.get('port', 23)}")
    logger.info(f"协议: {device_info.get('protocol', 'telnet')}")
    
    adapter = None
    try:
        # 1. 初始化适配器
        logger.info("初始化RuijieAdapter...")
        adapter = RuijieAdapter(device_info)
        
        # 2. 连接设备
        logger.info("尝试连接设备...")
        connected = adapter.connect()
        
        if not connected:
            logger.error("连接设备失败")
            return False
        
        logger.info("成功连接到设备")
        
        # 3. 尝试获取设备信息
        logger.info("尝试获取设备信息...")
        device_info_result = adapter.get_device_info()
        if device_info_result:
            logger.info(f"成功获取设备信息: {device_info_result.get('model', '未知型号')}")
            # 打印更多设备信息
            logger.info(f"厂商: {device_info_result.get('vendor', '未知')}")
            logger.info(f"软件版本: {device_info_result.get('version', '未知')}")
        else:
            logger.warning("未能获取设备详细信息")
        
        # 4. 尝试获取设备配置
        logger.info("尝试获取设备配置...")
        config = adapter.get_config()
        
        if config:
            logger.info(f"成功获取设备配置，配置大小: {len(config)} 字节")
            # 保存配置到临时文件
            config_filename = f"ruijie_config_backup_{device_info['management_ip']}.cfg"
            with open(config_filename, 'w', encoding='utf-8') as f:
                f.write(config)
            logger.info(f"配置已保存到文件: {config_filename}")
            
            # 打印配置的前几行作为预览
            config_lines = config.splitlines()[:5]
            logger.info(f"配置预览:\n{chr(10).join(config_lines)}")
            
            return True
        else:
            logger.error("未能获取设备配置")
            return False
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        # 打印完整异常堆栈
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 6. 断开连接
        if adapter:
            adapter.disconnect()
            logger.info("已断开与设备的连接")
    
    logger.info("===== 测试完成 =====")

if __name__ == "__main__":
    # 锐捷设备信息 - 使用测试成功的generic_telnet方式
    ruijie_device = {
        'management_ip': '192.168.121.51',  # 用户报告的故障设备IP
        'username': 'admin',  # 用户名
        'password': '520131xiao',  # 密码
        'port': 23,  # 端口号
        'protocol': 'telnet'  # 明确指定使用telnet协议
    }
    
    # 执行直接测试
    success = test_ruijie_adapter_direct(ruijie_device)
    
    if success:
        logger.info("✅ RuijieAdapter测试成功！配置备份功能正常工作。")
    else:
        logger.error("❌ RuijieAdapter测试失败！配置备份功能存在问题。")