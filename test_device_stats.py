import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000/api/v1/device-stats"

# 测试函数
def test_device_overview():
    """测试设备概览统计端点"""
    url = f"{BASE_URL}/overview"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("✅ 设备概览统计测试通过:")
            print(f"  - 设备总数: {data.get('total_devices', 0)}")
            print(f"  - 在线设备数: {data.get('online_devices', 0)}")
            print(f"  - 离线设备数: {data.get('offline_devices', 0)}")
            print(f"  - 厂商分布: {data.get('vendor_distribution', {})}")
            return True
        else:
            print(f"❌ 设备概览统计测试失败: 状态码 {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 设备概览统计测试异常: {str(e)}")
        return False

def test_traffic_monitoring():
    """测试流量监控数据端点"""
    url = f"{BASE_URL}/traffic-monitoring"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("✅ 流量监控数据测试通过:")
            print(f"  - 入站流量数据点数量: {len(data.get('inbound_traffic', []))}")
            print(f"  - 出站流量数据点数量: {len(data.get('outbound_traffic', []))}")
            if data.get('inbound_traffic') and data['inbound_traffic']:
                print(f"  - 第一个数据点示例: {data['inbound_traffic'][0]}")
            return True
        else:
            print(f"❌ 流量监控数据测试失败: 状态码 {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 流量监控数据测试异常: {str(e)}")
        return False

def test_device_types():
    """测试设备类型统计端点"""
    url = f"{BASE_URL}/device-types"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("✅ 设备类型统计测试通过:")
            print(f"  - 设备类型分布: {data.get('type_distribution', {})}")
            print(f"  - 厂商-类型二维分布: {data.get('vendor_type_distribution', {})}")
            return True
        else:
            print(f"❌ 设备类型统计测试失败: 状态码 {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 设备类型统计测试异常: {str(e)}")
        return False

def test_recent_alerts():
    """测试最近告警信息端点"""
    url = f"{BASE_URL}/recent-alerts"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("✅ 最近告警信息测试通过:")
            print(f"  - 告警数量: {len(data)}")
            if data:
                print(f"  - 第一条告警示例: {data[0]}")
            return True
        else:
            print(f"❌ 最近告警信息测试失败: 状态码 {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 最近告警信息测试异常: {str(e)}")
        return False

def test_device_health():
    """测试设备健康状态端点"""
    url = f"{BASE_URL}/device-health"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("✅ 设备健康状态测试通过:")
            print(f"  - CPU使用率数据点数量: {len(data.get('cpu_usage', []))}")
            print(f"  - 内存使用率数据点数量: {len(data.get('memory_usage', []))}")
            if data.get('cpu_usage') and data['cpu_usage']:
                print(f"  - 第一个CPU使用率数据点示例: {data['cpu_usage'][0]}")
            return True
        else:
            print(f"❌ 设备健康状态测试失败: 状态码 {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 设备健康状态测试异常: {str(e)}")
        return False

# 主函数
def main():
    """运行所有测试"""
    print("开始测试设备统计数据端点...\n")
    
    # 运行所有测试
    tests = [
        ("设备概览统计", test_device_overview),
        ("流量监控数据", test_traffic_monitoring),
        ("设备类型统计", test_device_types),
        ("最近告警信息", test_recent_alerts),
        ("设备健康状态", test_device_health)
    ]
    
    passed_tests = 0
    
    for name, test_func in tests:
        print(f"\n测试: {name}")
        print("=" * 50)
        if test_func():
            passed_tests += 1
    
    # 打印测试结果汇总
    print(f"\n\n测试汇总:")
    print(f"总测试数: {len(tests)}")
    print(f"通过测试数: {passed_tests}")
    print(f"通过率: {(passed_tests / len(tests)) * 100:.2f}%")
    
    if passed_tests == len(tests):
        print("\n🎉 所有设备统计数据端点测试通过！")
    else:
        print("\n⚠️ 有测试未通过，请检查问题。")

if __name__ == "__main__":
    main()