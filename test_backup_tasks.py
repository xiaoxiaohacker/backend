import requests
import json
import time
import requests

# API基础URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

# 用户登录信息
USERNAME = "admin"
PASSWORD = "520131xiao"

class BackupTasksTester:
    def __init__(self):
        self.token = None
        self.device_id = None
        self.backup_id = None
        
    def login(self):
        """登录获取认证令牌"""
        try:
            print("正在登录获取令牌...")
            response = requests.post(
                f"{BASE_URL}/auth/login",
                data={"username": USERNAME, "password": PASSWORD}
            )
            
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                print(f"✓ 登录成功，获取令牌成功")
                return True
            else:
                print(f"✗ 登录失败，状态码: {response.status_code}")
                print(f"  响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"✗ 登录过程中发生错误: {str(e)}")
            return False
    
    def get_devices(self):
        """获取设备列表"""
        if not self.token:
            print("✗ 未登录，无法获取设备列表")
            return False
        
        try:
            print("正在获取设备列表...")
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{BASE_URL}/devices", headers=headers)
            
            if response.status_code == 200:
                devices = response.json()
                if devices:
                    self.device_id = devices[0]["id"]
                    print(f"✓ 成功获取设备列表，共 {len(devices)} 台设备")
                    print(f"  已选择测试设备，ID: {self.device_id}")
                    return True
                else:
                    print("✗ 设备列表为空，请先添加设备")
                    return False
            else:
                print(f"✗ 获取设备列表失败，状态码: {response.status_code}")
                print(f"  响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"✗ 获取设备列表过程中发生错误: {str(e)}")
            return False
    
    def create_backup_task(self):
        """创建配置备份任务"""
        if not self.token or not self.device_id:
            print("✗ 未登录或未选择设备，无法创建配置备份任务")
            return False
        
        try:
            print(f"正在为设备 {self.device_id} 创建配置备份任务...")
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            config_data = {
                "device_id": self.device_id,
                "config": "这是一个测试配置备份内容",
                "description": f"测试配置备份任务 - {time.strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
            response = requests.post(
                f"{BASE_URL}/backup-tasks/",
                headers=headers,
                data=json.dumps(config_data)
            )
            
            if response.status_code == 200:
                backup_data = response.json()
                self.backup_id = backup_data["id"]
                print(f"✓ 成功创建配置备份任务，备份ID: {self.backup_id}")
                return True
            else:
                print(f"✗ 创建配置备份任务失败，状态码: {response.status_code}")
                print(f"  响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"✗ 创建配置备份任务过程中发生错误: {str(e)}")
            return False
    
    def get_device_backup_tasks(self):
        """获取设备的所有配置备份任务"""
        if not self.device_id:
            print("✗ 未选择设备，无法获取配置备份任务")
            return False
        
        try:
            print(f"正在获取设备 {self.device_id} 的所有配置备份任务...")
            response = requests.get(f"{BASE_URL}/backup-tasks/device/{self.device_id}")
            
            if response.status_code == 200:
                backups = response.json()
                print(f"✓ 成功获取设备的所有配置备份任务，共 {len(backups)} 条记录")
                return True
            else:
                print(f"✗ 获取设备的配置备份任务失败，状态码: {response.status_code}")
                print(f"  响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"✗ 获取设备的配置备份任务过程中发生错误: {str(e)}")
            return False
    
    def get_backup_task(self):
        """获取指定的配置备份任务"""
        if not self.backup_id:
            print("✗ 未创建配置备份任务，无法获取配置备份任务详情")
            return False
        
        try:
            print(f"正在获取配置备份任务 {self.backup_id} 的详细信息...")
            response = requests.get(f"{BASE_URL}/backup-tasks/{self.backup_id}")
            
            if response.status_code == 200:
                backup_data = response.json()
                print(f"✓ 成功获取配置备份任务的详细信息，备份描述: {backup_data.get('description', '无描述')}")
                return True
            else:
                print(f"✗ 获取配置备份任务详情失败，状态码: {response.status_code}")
                print(f"  响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"✗ 获取配置备份任务详情过程中发生错误: {str(e)}")
            return False
    
    def get_latest_backup_task(self):
        """获取设备的最新配置备份任务"""
        if not self.device_id:
            print("✗ 未选择设备，无法获取最新配置备份任务")
            return False
        
        try:
            print(f"正在获取设备 {self.device_id} 的最新配置备份任务...")
            response = requests.get(f"{BASE_URL}/backup-tasks/device/{self.device_id}/latest")
            
            if response.status_code == 200:
                backup_data = response.json()
                print(f"✓ 成功获取设备的最新配置备份任务，备份ID: {backup_data['id']}")
                return True
            else:
                print(f"✗ 获取设备的最新配置备份任务失败，状态码: {response.status_code}")
                print(f"  响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"✗ 获取设备的最新配置备份任务过程中发生错误: {str(e)}")
            return False
    
    def delete_backup_task(self):
        """删除配置备份任务"""
        if not self.token or not self.backup_id:
            print("✗ 未登录或未创建配置备份任务，无法删除配置备份任务")
            return False
        
        try:
            print(f"正在删除配置备份任务 {self.backup_id}...")
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.delete(f"{BASE_URL}/backup-tasks/{self.backup_id}", headers=headers)
            
            if response.status_code == 204:
                print(f"✓ 成功删除配置备份任务 {self.backup_id}")
                return True
            else:
                print(f"✗ 删除配置备份任务失败，状态码: {response.status_code}")
                print(f"  响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"✗ 删除配置备份任务过程中发生错误: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n===== 配置备份任务API测试 =====")
        
        tests = [
            ("登录获取令牌", self.login),
            ("获取设备列表", self.get_devices),
            ("创建配置备份任务", self.create_backup_task),
            ("获取设备的所有配置备份任务", self.get_device_backup_tasks),
            ("获取指定的配置备份任务", self.get_backup_task),
            ("获取设备的最新配置备份任务", self.get_latest_backup_task),
            ("删除配置备份任务", self.delete_backup_task)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for i, (test_name, test_func) in enumerate(tests, 1):
            print(f"\n[{i}/{total_tests}] {test_name}...")
            if test_func():
                passed_tests += 1
            else:
                print(f"✗ 测试失败: {test_name}")
                print("\n配置备份任务API测试失败，已跳过后续测试")
                break
        
        print("\n===== 测试总结 =====")
        print(f"运行测试数: {min(i, total_tests)}/{total_tests}")
        
        if passed_tests == total_tests:
            print("✓ 所有测试通过！配置备份任务API功能正常工作")
        else:
            print("✗ 测试未全部通过！配置备份任务API功能存在问题")
        
        print("==================\n")

if __name__ == "__main__":
    # 自动运行测试
    print("自动运行配置备份任务API测试...")
    tester = BackupTasksTester()
    tester.run_all_tests()