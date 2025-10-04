# 详细测试 pysnmp 7.1.21 的类导入路径
import pysnmp
print(f"pysnmp 版本: {pysnmp.__version__}\n")

# 测试每个类的导入路径
classes_to_test = [
    "SnmpEngine",
    "CommunityData",
    "UdpTransportTarget",
    "ContextData",
    "ObjectType",
    "ObjectIdentity",
    "getCmd",
    "nextCmd"
]

# 尝试不同的导入路径
paths_to_try = [
    "pysnmp",
    "pysnmp.hlapi",
    "pysnmp.hlapi.v3arch",
    "pysnmp.hlapi.v1arch",
    "pysnmp.entity.engine",
    "pysnmp.hlapi.v3arch.asyncio",
    "pysnmp.hlapi.v1arch.asyncio"
]

print("开始测试各个类的导入路径...\n")

for cls_name in classes_to_test:
    found = False
    print(f"测试 {cls_name} 的导入路径:")
    
    # 尝试直接从不同的模块导入
    for path in paths_to_try:
        try:
            exec(f"from {path} import {cls_name}")
            print(f"  ✓ 成功: from {path} import {cls_name}")
            found = True
            break
        except ImportError:
            # 尝试从子模块导入
            try:
                # 查看模块下有哪些子模块
                module = __import__(path)
                components = path.split('.')
                for comp in components[1:]:
                    module = getattr(module, comp)
                
                # 查看所有属性
                for attr_name in dir(module):
                    if not attr_name.startswith('_'):
                        try:
                            attr = getattr(module, attr_name)
                            if hasattr(attr, cls_name):
                                exec(f"from {path}.{attr_name} import {cls_name}")
                                print(f"  ✓ 成功: from {path}.{attr_name} import {cls_name}")
                                found = True
                                break
                        except (ImportError, AttributeError):
                            pass
                if found:
                    break
            except (ImportError, AttributeError):
                pass
    
    if not found:
        print(f"  ✗ 失败: 未找到 {cls_name} 的导入路径")
    print()

print("测试完成!")