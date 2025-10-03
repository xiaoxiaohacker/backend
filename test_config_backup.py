import requests
import json
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('config_backup_test')

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 登录信息 - 请修改为您的实际用户名和密码
USERNAME = "admin"  # 用户名
PASSWORD = "520131xiao"  # 密码

# 提示用户修改登录信息
print("\n===== 配置备份功能测试 =====")
print("请确保在test_config_backup.py文件中修改为您的实际用户名和密码")
print(f"当前使用的用户名: {USERNAME}")
print("\n注意：如果您不知道正确的用户名和密码，可能需要先通过API注册一个新用户")
print("或联系系统管理员获取有效的登录凭据")
print("==========================\n")

class ConfigBackupTester:
    def __init__(self):
        self.access_token = None
        self.device_id = None
        self.backup_id = None
        
    def login(self):
        """登录获取访问令牌"""
        logger.info("尝试登录获取访问令牌...")
        url = f"{BASE_URL}/auth/login"
        
        try:
            # 发送登录请求
            response = requests.post(
                url,
                data={"username": USERNAME, "password": PASSWORD}
            )
            
            # 检查响应状态码
            if response.status_code == 200:
                # 解析响应内容
                result = response.json()
                self.access_token = result.get("access_token")
                logger.info("✓ 登录成功，已获取访问令牌")
                return True
            else:
                logger.error(f"✗ 登录失败，状态码: {response.status_code}, 响应内容: {response.text}")
                return False
        except Exception as e:
            logger.error(f"✗ 登录过程中发生错误: {str(e)}")
            return False
    
    def get_devices(self):
        """获取设备列表"""
        logger.info("获取设备列表...")
        url = f"{BASE_URL}/devices"
        
        try:
            # 发送获取设备列表请求
            response = requests.get(url)
            
            # 检查响应状态码
            if response.status_code == 200:
                # 解析响应内容
                devices = response.json()
                logger.info(f"✓ 成功获取设备列表，共 {len(devices)} 台设备")
                
                # 如果有设备，选择第一个设备的ID
                if devices:
                    self.device_id = devices[0]["id"]
                    logger.info(f"已选择测试设备，ID: {self.device_id}")
                    return True
                else:
                    logger.warning("✗ 没有找到设备，请先添加设备")
                    return False
            else:
                logger.error(f"✗ 获取设备列表失败，状态码: {response.status_code}, 响应内容: {response.text}")
                return False
        except Exception as e:
            logger.error(f"✗ 获取设备列表过程中发生错误: {str(e)}")
            return False
    
    def create_config_backup(self):
        """创建设备配置备份"""
        if not self.device_id or not self.access_token:
            logger.error("✗ 无法创建配置备份: 缺少设备ID或访问令牌")
            return False
            
        logger.info(f"为设备 {self.device_id} 创建配置备份...")
        url = f"{BASE_URL}/devices/{self.device_id}/config-backup"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # 配置备份数据
        config_data = {
            "device_id": self.device_id,
            "config": "这是一个测试配置备份内容",
            "description": f"测试配置备份 - {time.strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        try:
            # 发送创建配置备份请求
            response = requests.post(
                url,
                headers=headers,
                json=config_data
            )
            
            # 检查响应状态码
            if response.status_code == 200:
                # 解析响应内容
                backup = response.json()
                self.backup_id = backup.get("id")
                logger.info(f"✓ 成功创建配置备份，备份ID: {self.backup_id}")
                return True
            else:
                logger.error(f"✗ 创建配置备份失败，状态码: {response.status_code}, 响应内容: {response.text}")
                return False
        except Exception as e:
            logger.error(f"✗ 创建配置备份过程中发生错误: {str(e)}")
            return False
    
    def get_device_backups(self):
        """获取设备的所有配置备份"""
        if not self.device_id:
            logger.error("✗ 无法获取设备的配置备份: 缺少设备ID")
            return False
            
        logger.info(f"获取设备 {self.device_id} 的所有配置备份...")
        url = f"{BASE_URL}/devices/{self.device_id}/config-backups"
        
        try:
            # 发送获取配置备份列表请求
            response = requests.get(url)
            
            # 检查响应状态码
            if response.status_code == 200:
                # 解析响应内容
                backups = response.json()
                logger.info(f"✓ 成功获取设备的配置备份列表，共 {len(backups)} 个备份")
                return True
            else:
                logger.error(f"✗ 获取设备的配置备份列表失败，状态码: {response.status_code}, 响应内容: {response.text}")
                return False
        except Exception as e:
            logger.error(f"✗ 获取设备的配置备份列表过程中发生错误: {str(e)}")
            return False
    
    def get_latest_backup(self):
        """获取设备的最新配置备份"""
        if not self.device_id:
            logger.error("✗ 无法获取设备的最新配置备份: 缺少设备ID")
            return False
            
        logger.info(f"获取设备 {self.device_id} 的最新配置备份...")
        url = f"{BASE_URL}/devices/{self.device_id}/config-backup/latest"
        
        try:
            # 发送获取最新配置备份请求
            response = requests.get(url)
            
            # 检查响应状态码
            if response.status_code == 200:
                # 解析响应内容
                backup = response.json()
                logger.info(f"✓ 成功获取设备的最新配置备份，备份ID: {backup.get('id')}")
                return True
            else:
                logger.error(f"✗ 获取设备的最新配置备份失败，状态码: {response.status_code}, 响应内容: {response.text}")
                return False
        except Exception as e:
            logger.error(f"✗ 获取设备的最新配置备份过程中发生错误: {str(e)}")
            return False
    
    def get_backup(self):
        """获取指定的配置备份"""
        if not self.backup_id:
            logger.error("✗ 无法获取配置备份: 缺少备份ID")
            return False
            
        logger.info(f"获取配置备份 {self.backup_id} 的详细信息...")
        url = f"{BASE_URL}/devices/config-backups/{self.backup_id}"
        
        try:
            # 发送获取配置备份请求
            response = requests.get(url)
            
            # 检查响应状态码
            if response.status_code == 200:
                # 解析响应内容
                backup = response.json()
                logger.info(f"✓ 成功获取配置备份的详细信息，备份描述: {backup.get('description')}")
                return True
            else:
                logger.error(f"✗ 获取配置备份的详细信息失败，状态码: {response.status_code}, 响应内容: {response.text}")
                return False
        except Exception as e:
            logger.error(f"✗ 获取配置备份的详细信息过程中发生错误: {str(e)}")
            return False
    
    def delete_backup(self):
        """删除指定的配置备份"""
        if not self.backup_id or not self.access_token:
            logger.error("✗ 无法删除配置备份: 缺少备份ID或访问令牌")
            return False
            
        logger.info(f"删除配置备份 {self.backup_id}...")
        url = f"{BASE_URL}/devices/config-backups/{self.backup_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            # 发送删除配置备份请求
            response = requests.delete(
                url,
                headers=headers
            )
            
            # 检查响应状态码
            if response.status_code == 204:
                logger.info(f"✓ 成功删除配置备份 {self.backup_id}")
                return True
            else:
                logger.error(f"✗ 删除配置备份失败，状态码: {response.status_code}, 响应内容: {response.text}")
                return False
        except Exception as e:
            logger.error(f"✗ 删除配置备份过程中发生错误: {str(e)}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行配置备份功能测试...")
        
        # 按顺序运行测试
        tests = [
            (self.login, "登录获取访问令牌"),
            (self.get_devices, "获取设备列表"),
            (self.create_config_backup, "创建配置备份"),
            (self.get_device_backups, "获取设备的所有配置备份"),
            (self.get_latest_backup, "获取设备的最新配置备份"),
            (self.get_backup, "获取指定的配置备份"),
            (self.delete_backup, "删除配置备份")
        ]
        
        # 统计测试结果
        passed_count = 0
        
        # 运行测试
        for test_func, test_name in tests:
            # 打印测试分隔线
            logger.info(f"\n{'-' * 50}")
            logger.info(f"测试: {test_name}")
            logger.info(f"{'-' * 50}")
            
            # 运行测试
            result = test_func()
            
            # 统计结果
            if result:
                passed_count += 1
            else:
                # 如果测试失败，跳过后续测试
                logger.error(f"\n✗ 测试失败: {test_name}")
                logger.error(f"\n配置备份功能测试失败，已跳过后续测试")
                break
        
        # 打印测试总结
        logger.info(f"\n{'=' * 50}")
        logger.info(f"测试总结:")
        logger.info(f"运行测试数: {passed_count}/{len(tests)}")
        
        if passed_count == len(tests):
            logger.info(f"✓ 所有测试通过！配置备份功能正常工作")
        else:
            logger.error(f"✗ 测试未全部通过！配置备份功能存在问题")
        
        logger.info(f"{'=' * 50}")

if __name__ == "__main__":
    # 自动运行测试
    print("自动运行配置备份功能测试...")
    tester = ConfigBackupTester()
    tester.run_all_tests()