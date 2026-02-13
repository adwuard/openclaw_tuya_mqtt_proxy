#!/usr/bin/env python3
"""
MQTT 配置示例文件
复制此文件为 config.py 并修改配置，或直接使用环境变量
"""

# MQTT Broker 配置
# 方式 1: 使用 IP 地址（局域网部署推荐）
MQTT_BROKER = "192.168.254.129"  # 替换为你的 MQTT 服务器 IP

# 方式 2: 使用 localhost（本地部署）
# MQTT_BROKER = "localhost"

# 方式 3: 使用域名（如果有）
# MQTT_BROKER = "mqtt.example.com"

MQTT_PORT = 1883  # MQTT 端口，默认 1883

# Topic 配置
MQTT_TOPIC_CMD = "AI_CMD"  # 接收指令的 topic
MQTT_TOPIC_RET = "AI_RET"  # 发送结果的 topic

# 客户端 ID
MQTT_CLIENT_ID = "openclaw_bridge"

# 使用说明:
# 1. 直接修改上面的值
# 2. 或使用环境变量:
#    export MQTT_BROKER=192.168.254.129
#    export MQTT_PORT=1883
# 3. 或在代码中导入此配置（需要修改主程序）

