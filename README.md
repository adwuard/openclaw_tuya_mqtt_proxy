# MQTT-OpenClaw 桥接服务器

这是一个 MQTT 桥接服务，用于将其他设备通过 MQTT 协议与 OpenClaw AI 助手进行通信。

## 功能说明

- **监听 AI_CMD topic**：接收其他设备发送的指令
- **调用 OpenClaw**：将指令传递给 OpenClaw agent 处理
- **发布到 AI_RET topic**：将 AI 的响应结果发布到 MQTT

## 系统要求

- Python 3.6+
- MQTT Broker (如 Mosquitto)
- OpenClaw 已安装并配置

## 安装步骤

### 1. 安装 MQTT Broker (Mosquitto)

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients

# 启动 Mosquitto 服务
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

### 2. 安装 Python 依赖

**方法 1：使用用户安装（推荐）**
```bash
cd ~/mqtt_openclaw_bridge
pip3 install --user -r requirements.txt
```

**方法 2：使用系统包管理器**
```bash
sudo apt-get install python3-paho-mqtt
```

**方法 3：使用虚拟环境**
```bash
cd ~/mqtt_openclaw_bridge
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**方法 4：使用安装脚本**
```bash
cd ~/mqtt_openclaw_bridge
./install.sh
```

### 3. 确保 OpenClaw 可用

```bash
# 测试 OpenClaw 是否可用
openclaw --version
```

## 使用方法

### 启动桥接服务

```bash
cd ~/mqtt_openclaw_bridge
python3 mqtt_openclaw_bridge.py
```

服务启动后会：
- 连接到 MQTT Broker (默认: localhost:1883)
- 订阅 `AI_CMD` topic
- 等待接收指令

### 发送测试指令

**方法 1：使用测试脚本（交互式）**
```bash
python3 test_sender.py
```

**方法 2：使用测试脚本（命令行）**
```bash
python3 test_sender.py "帮我生成一个AI情报分析的文件夹放在桌面上"
```

**方法 3：使用 mosquitto_pub 命令**
```bash
mosquitto_pub -h localhost -t AI_CMD -m "帮我生成一个AI情报分析的文件夹放在桌面上"
```

### 接收 AI 响应

在另一个终端运行：
```bash
python3 test_receiver.py
```

或者使用 mosquitto_sub：
```bash
mosquitto_sub -h localhost -t AI_RET
```

## 消息格式

### 发送到 AI_CMD (支持两种格式)

**格式 1：纯文本**
```
帮我生成一个AI情报分析的文件夹放在桌面上
```

**格式 2：JSON 格式（推荐）**
```json
{
  "message": "帮我生成一个AI情报分析的文件夹放在桌面上",
  "request_id": "unique_request_id_123"
}
```

### 从 AI_RET 接收的格式

```json
{
  "timestamp": "2026-02-13T10:30:00.123456",
  "request_id": "unique_request_id_123",
  "message": "帮我生成一个AI情报分析的文件夹放在桌面上",
  "response": "AI 的完整响应内容...",
  "status": "success"
}
```

## 配置说明

可以在 `mqtt_openclaw_bridge.py` 中修改以下配置：

```python
MQTT_BROKER = "localhost"    # MQTT broker 地址
MQTT_PORT = 1883              # MQTT broker 端口
MQTT_TOPIC_CMD = "AI_CMD"    # 接收指令的 topic
MQTT_TOPIC_RET = "AI_RET"    # 发送结果的 topic
OPENCLAW_AGENT = "main"      # 使用的 agent ID
```

## 测试完整流程

### 终端 1：启动桥接服务
```bash
python3 mqtt_openclaw_bridge.py
```

### 终端 2：启动结果接收器
```bash
python3 test_receiver.py
```

### 终端 3：发送测试指令
```bash
python3 test_sender.py "今天深圳天气怎么样"
```

## 日志

服务运行日志会保存到 `mqtt_bridge.log` 文件中，同时也会输出到控制台。

## 故障排查

1. **无法连接到 MQTT Broker**
   - 检查 Mosquitto 是否运行：`sudo systemctl status mosquitto`
   - 检查端口是否被占用：`netstat -tlnp | grep 1883`

2. **OpenClaw 命令执行失败**
   - 检查 OpenClaw 是否安装：`which openclaw`
   - 检查 OpenClaw 配置：`openclaw status`

3. **消息发送但未收到响应**
   - 检查桥接服务是否正常运行
   - 查看日志文件：`tail -f mqtt_bridge.log`

## 许可证

MIT License

