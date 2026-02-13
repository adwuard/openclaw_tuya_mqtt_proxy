#!/bin/bash
# 完整测试脚本 - 测试 MQTT-OpenClaw 桥接的完整流程

echo "=========================================="
echo "MQTT-OpenClaw 桥接完整测试"
echo "=========================================="
echo

# 检查依赖
echo "1. 检查依赖..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi
echo "✅ Python3 已安装"

if ! python3 -c "import paho.mqtt.client" 2>/dev/null; then
    echo "⚠️  paho-mqtt 未安装，正在安装..."
    pip3 install paho-mqtt
fi
echo "✅ paho-mqtt 已安装"

if ! command -v mosquitto &> /dev/null; then
    echo "⚠️  Mosquitto 未安装"
    echo "   请运行: sudo apt-get install mosquitto mosquitto-clients"
    echo "   或使用其他 MQTT broker"
else
    echo "✅ Mosquitto 已安装"
    
    # 检查 Mosquitto 是否运行
    if systemctl is-active --quiet mosquitto 2>/dev/null || pgrep mosquitto > /dev/null; then
        echo "✅ Mosquitto 服务正在运行"
    else
        echo "⚠️  Mosquitto 服务未运行，尝试启动..."
        sudo systemctl start mosquitto 2>/dev/null || echo "   请手动启动: sudo systemctl start mosquitto"
    fi
fi

if ! command -v openclaw &> /dev/null; then
    echo "❌ OpenClaw 未安装或不在 PATH 中"
    exit 1
fi
echo "✅ OpenClaw 已安装"

echo
echo "=========================================="
echo "测试说明："
echo "=========================================="
echo "1. 在一个终端运行: python3 mqtt_openclaw_bridge.py"
echo "2. 在另一个终端运行: python3 test_receiver.py"
echo "3. 在第三个终端运行: python3 test_sender.py '你的测试消息'"
echo
echo "或者使用 mosquitto 命令："
echo "  发送: mosquitto_pub -h localhost -t AI_CMD -m '你的消息'"
echo "  接收: mosquitto_sub -h localhost -t AI_RET"
echo
echo "=========================================="

