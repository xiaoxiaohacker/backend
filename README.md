# NetMgr 交换机管理系统

## 项目介绍
NetMgr是一个基于FastAPI框架开发的交换机管理后端系统，主要用于管理华为、华三、锐捷等厂商的网络交换机设备。系统提供了统一的API接口，实现了对不同厂商交换机的统一管理和监控。

## 主要功能
- 用户认证系统（注册、登录、JWT认证）
- 设备管理（添加、查询、更新、删除设备）
- 设备信息获取（型号、版本、序列号等）
- 接口状态监控
- 配置管理（查看、保存配置）
- 命令执行（在设备上执行任意命令）

## 技术栈
- **Web框架**: FastAPI
- **数据库**: MySQL + SQLAlchemy
- **认证**: JWT (python-jose) + PassLib
- **网络设备连接**: Netmiko
- **任务队列**: Celery + Redis（计划中）
- **容器化**: Docker

## 项目结构
```
app/
├── adapters/          # 交换机适配器（不同厂商的实现）
│   ├── base.py        # 适配器基类
│   ├── huawei.py      # 华为交换机适配器
│   ├── h3c.py         # 华三交换机适配器
│   └── ruijie.py      # 锐捷交换机适配器
├── api/               # API路由
│   └── v1/            # v1版本API
│       ├── auth.py    # 认证相关接口
│       └── devices.py # 设备管理相关接口
├── models/            # 数据库模型
├── schemas/           # Pydantic数据模型
├── services/          # 业务逻辑层
│   ├── adapter_manager.py  # 适配器管理器
│   ├── auth.py        # 认证服务
│   ├── config.py      # 配置信息
│   ├── db.py          # 数据库连接
│   └── models.py      # 服务层数据模型
├── main.py            # 应用程序入口
└── tasks.py           # 异步任务（计划中）
```

## 安装和部署

### 本地开发
1. 克隆项目代码
2. 创建虚拟环境：`python -m venv .venv`
3. 激活虚拟环境：`source .venv/bin/activate`（Linux/Mac）或 `.venv\Scripts\activate`（Windows）
4. 安装依赖：`pip install -r requirements.txt`
5. 配置数据库连接（在`app/services/config.py`中）
6. 运行应用：`uvicorn app.main:app --reload`

### Docker部署
1. 构建镜像：`docker build -t netmgr-backend .`
2. 运行容器：`docker run -p 8000:8000 netmgr-backend`

## API文档
项目启动后，可以通过以下地址访问自动生成的API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 支持的设备厂商
- 华为（Huawei）
- 华三（H3C）
- 锐捷（Ruijie）

## 注意事项
1. 系统需要与交换机进行网络连接，请确保网络可达
2. 为了安全起见，建议在生产环境中修改默认的SECRET_KEY
3. 目前系统仅支持通过SSH协议管理交换机
4. 后续版本将添加更多功能，如批量操作、配置比较、告警功能等

## License
MIT