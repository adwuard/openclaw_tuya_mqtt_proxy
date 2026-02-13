#!/bin/bash
# MQTT-OpenClaw 桥接安装脚本

echo "=========================================="
echo "MQTT-OpenClaw 桥接安装脚本"
echo "=========================================="
echo

# 安装 Python 依赖
echo "1. 安装 Python 依赖..."
echo "   尝试使用 pip3 安装..."
pip3 install --user -r requirements.txt 2>/dev/null || pip3 install --break-system-packages -r requirements.txt 2>/dev/null || {
    echo "⚠️  系统 pip 安装失败，尝试使用 apt 安装..."
    sudo apt-get update && sudo apt-get install -y python3-paho-mqtt 2>/dev/null || {
        echo "❌ 请手动安装: pip3 install --user paho-mqtt"
        echo "   或创建虚拟环境: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    }
}
if python3 -c "import paho.mqtt.client" 2>/dev/null; then
    echo "✅ Python 依赖安装成功"
else
    echo "⚠️  请手动安装 paho-mqtt: pip3 install --user paho-mqtt"
fi

# 检查 MQTT Broker
echo
echo "2. 检查 MQTT Broker..."
if command -v mosquitto &> /dev/null; then
    echo "✅ Mosquitto 已安装"
    
    # 检查服务状态
    if systemctl is-active --quiet mosquitto 2>/dev/null; then
        echo "✅ Mosquitto 服务正在运行"
    else
        echo "⚠️  Mosquitto 服务未运行"
        read -p "是否启动 Mosquitto 服务? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo systemctl start mosquitto
            sudo systemctl enable mosquitto
            echo "✅ Mosquitto 服务已启动并设置为开机自启"
        fi
    fi
else
    echo "⚠️  Mosquitto 未安装"
    echo "   安装命令: sudo apt-get install mosquitto mosquitto-clients"
    echo "   或者使用其他 MQTT broker"
fi

# 检查 OpenClaw
echo
echo "3. 检查 OpenClaw..."
if command -v openclaw &> /dev/null; then
    echo "✅ OpenClaw 已安装"
    openclaw --version | head -1
else
    echo "❌ OpenClaw 未安装或不在 PATH 中"
    exit 1
fi

echo
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo
echo "使用方法："
echo "1. 启动桥接服务:"
echo "   python3 mqtt_openclaw_bridge.py"
echo
echo "2. 发送测试消息（新终端）:"
echo "   python3 test_sender.py '你的消息'"
echo
echo "3. 接收响应（新终端）:"
echo "   python3 test_receiver.py"
echo

