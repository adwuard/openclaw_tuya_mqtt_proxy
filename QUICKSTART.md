# 快速开始指南

## 一键安装（推荐）

```bash
cd ~/mqtt_openclaw_bridge
./install.sh
```

## 手动安装

### 1. 安装 MQTT Broker (Mosquitto)

```bash
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

### 2. 安装 Python 依赖

```bash
pip3 install --user paho-mqtt
# 或者
sudo apt-get install python3-paho-mqtt
```

## 使用步骤

### 步骤 1：启动桥接服务

在一个终端运行：
```bash
cd ~/mqtt_openclaw_bridge
python3 mqtt_openclaw_bridge.py
```

你会看到：
```
✅ 成功连接到 MQTT Broker: localhost:1883
📡 已订阅 topic: AI_CMD
⏳ 等待消息...
```

### 步骤 2：启动结果接收器（可选）

在另一个终端运行：
```bash
cd ~/mqtt_openclaw_bridge
python3 test_receiver.py
```

### 步骤 3：发送测试指令

在第三个终端运行：
```bash
cd ~/mqtt_openclaw_bridge
python3 test_sender.py "帮我生成一个AI情报分析的文件夹放在桌面上"
```

或者使用 mosquitto 命令：
```bash
mosquitto_pub -h localhost -t AI_CMD -m "帮我生成一个AI情报分析的文件夹放在桌面上"
```

### 步骤 4：查看响应

如果运行了 test_receiver.py，你会看到 AI 的响应。

或者使用 mosquitto 命令：
```bash
mosquitto_sub -h localhost -t AI_RET
```

## 测试完整流程

打开三个终端：

**终端 1 - 桥接服务：**
```bash
cd ~/mqtt_openclaw_bridge
python3 mqtt_openclaw_bridge.py
```

**终端 2 - 接收响应：**
```bash
cd ~/mqtt_openclaw_bridge
python3 test_receiver.py
```

**终端 3 - 发送指令：**
```bash
cd ~/mqtt_openclaw_bridge
python3 test_sender.py "今天深圳天气怎么样"
```

## 常见问题

### Q: 提示 "无法连接到 MQTT Broker"
A: 检查 Mosquitto 是否运行：
```bash
sudo systemctl status mosquitto
sudo systemctl start mosquitto
```

### Q: 提示 "paho-mqtt 未安装"
A: 安装依赖：
```bash
pip3 install --user paho-mqtt
```

### Q: 消息发送了但没有响应
A: 检查桥接服务是否正常运行，查看日志：
```bash
tail -f mqtt_bridge.log
```
