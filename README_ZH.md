# MQTT-OpenClaw 桥接服务器

这是一个 MQTT 桥接服务，用于将 Tuya 硬件设备通过 MQTT 协议与 OpenClaw AI 助手进行通信。

English documentation: `README.md`

## 快速介绍

该服务是 TuyaOpen 硬件与 OpenClaw 之间的 MQTT 代理层。
TuyaOpen 硬件提供物理交互能力（麦克风 + 扬声器）和内置 ASR，把识别后的用户语音文本发布到 MQTT。
桥接服务从 `openclaw/device/user_speech_text` 读取用户提示词，转发给 OpenClaw agent，再把响应发布到 `openclaw/server/response` 供硬件侧播放。

## 功能说明

- **监听 openclaw/device/user_speech_text topic**：接收 Tuya 硬件设备发送的指令
- **调用 OpenClaw**：将指令传递给 OpenClaw agent 处理
- **发布到 openclaw/server/response topic**：将 AI 的响应结果发布到 MQTT

## 系统要求

- Python 3.6+
- MQTT Broker (如 Mosquitto)
- OpenClaw 已安装并配置

## Mosquitto 是什么？

Mosquitto 是一个轻量级 MQTT Broker（消息中枢）。  
在本项目中它负责转发消息：
- 桥接服务持续监听（monitor）`openclaw/device/user_speech_text`，Tuya 硬件设备向该 topic 发布指令
- 桥接服务读取指令并调用 OpenClaw
- 桥接服务把结果发布到 `openclaw/server/response`，设备再订阅接收

## 安装步骤

### 1. 用户权限安装（不需要 sudo）

安装 Python 依赖：

```bash
cd ~/mqtt_openclaw_bridge
pip3 install --user -r requirements.txt
```

### 2. 系统权限安装（需要 sudo）

安装并启动 MQTT Broker (Mosquitto)：

```bash
sudo bash install.sh install-mosquitto
```

手动等价命令：

```bash
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

如需让 Mosquitto 监听所有网卡（0.0.0.0:1883）：

```bash
sudo bash install.sh mosquitto-listen-all
```

对应模板文件位于：`configs/mosquitto_listen_all.conf`。

### 3. 其他 Python 安装方式（可选）

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

**方法 4：使用统一脚本（推荐）**
```bash
cd ~/mqtt_openclaw_bridge
bash install.sh
```

### 4. 确保 OpenClaw 可用

```bash
# 测试 OpenClaw 是否可用
openclaw --version
```

## 使用方法

### 启动桥接服务

```bash
cd ~/mqtt_openclaw_bridge
python3 openclaw_mqtt_bridge.py
```

服务启动后会：
- 连接到 MQTT Broker (默认: localhost:1883)
- 订阅 `openclaw/device/user_speech_text` topic
- 等待接收指令

### 发送测试指令

使用 `mosquitto_pub` 命令发送：
```bash
mosquitto_pub -h localhost -t openclaw/device/user_speech_text -m "帮我生成一个AI情报分析的文件夹放在桌面上"
```

### 接收 AI 响应

在另一个终端使用 `mosquitto_sub` 监听：
```bash
mosquitto_sub -h localhost -t openclaw/server/response
```

## 消息格式

### 发送到 openclaw/device/user_speech_text (支持两种格式)

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

### 从 openclaw/server/response 接收的格式

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

可以在 `openclaw_mqtt_bridge.py` 中修改以下配置：

```python
MQTT_BROKER = "localhost"    # MQTT broker 地址
MQTT_PORT = 1883              # MQTT broker 端口
MQTT_TOPIC_IN_COMMAND = "openclaw/device/user_speech_text"  # 接收指令的 topic
MQTT_TOPIC_OUT_RESULT = "openclaw/server/response"          # 发送结果的 topic
OPENCLAW_AGENT = "main"      # 使用的 agent ID
```

## 测试完整流程

### 终端 1：启动桥接服务
```bash
python3 openclaw_mqtt_bridge.py
```

### 终端 2：启动结果接收（CLI）
```bash
mosquitto_sub -h localhost -t openclaw/server/response -v
```

### 终端 3：发送测试指令（CLI）
```bash
mosquitto_pub -h localhost -t openclaw/device/user_speech_text -m "今天深圳天气怎么样"
```

也可以通过统一脚本查看测试命令：

```bash
bash install.sh test-help
```

## 日志

服务运行日志会保存到 `mqtt_bridge.log` 文件中，同时也会输出到控制台。

## 故障排查

1. **无法连接到 MQTT Broker**
   - 检查 Mosquitto 是否运行：`sudo systemctl status mosquitto`
   - 检查端口监听：`ss -tlnp | rg 1883`

2. **OpenClaw 命令执行失败**
   - 检查 OpenClaw 是否安装：`which openclaw`
   - 检查 OpenClaw 配置：`openclaw status`

3. **消息发送但未收到响应**
   - 检查桥接服务是否正常运行
   - 查看日志文件：`tail -f mqtt_bridge.log`

## 许可证

MIT License

