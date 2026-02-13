#!/usr/bin/env python3
"""
MQTT 测试发送脚本
模拟设备向 AI_CMD topic 发送指令
"""

import paho.mqtt.client as mqtt
import json
import time
import sys
import os

# MQTT 配置
# 支持从环境变量读取，或直接修改这里的值
# 可以使用 localhost、IP 地址（如 192.168.1.100）或域名
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_CMD = os.getenv("MQTT_TOPIC_CMD", "AI_CMD")


def on_connect(client, userdata, flags, rc):
    """连接回调"""
    if rc == 0:
        print(f"✅ 已连接到 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    else:
        print(f"❌ 连接失败，错误代码: {rc}")


def send_command(message, request_id=None):
    """
    发送指令到 AI_CMD topic
    
    Args:
        message: 要发送的指令文本
        request_id: 可选的请求 ID（用于追踪）
    """
    client = mqtt.Client()
    client.on_connect = on_connect
    
    try:
        # 连接到 broker
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        # 等待连接建立
        time.sleep(1)
        
        # 构建消息
        if request_id:
            payload = json.dumps({
                'message': message,
                'request_id': request_id
            }, ensure_ascii=False)
        else:
            payload = message  # 也可以发送纯文本
        
        # 发布消息
        print(f"📤 发送指令到 {MQTT_TOPIC_CMD}:")
        print(f"   消息: {message}")
        if request_id:
            print(f"   请求ID: {request_id}")
        
        result = client.publish(MQTT_TOPIC_CMD, payload, qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print("✅ 消息发送成功")
        else:
            print(f"❌ 消息发送失败，错误代码: {result.rc}")
        
        # 等待消息发送完成
        time.sleep(0.5)
        client.loop_stop()
        client.disconnect()
        
    except Exception as e:
        print(f"❌ 发送消息时出错: {str(e)}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 从命令行参数读取消息
        message = " ".join(sys.argv[1:])
        request_id = f"test_{int(time.time())}"
        send_command(message, request_id)
    else:
        # 交互式输入
        print("=" * 60)
        print("MQTT 测试发送工具")
        print("=" * 60)
        print(f"目标 Topic: {MQTT_TOPIC_CMD}")
        print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print("=" * 60)
        print()
        
        while True:
            try:
                message = input("\n请输入要发送的指令（输入 'quit' 退出）: ").strip()
                
                if not message:
                    continue
                    
                if message.lower() in ['quit', 'exit', 'q']:
                    print("👋 退出")
                    break
                
                request_id = f"test_{int(time.time())}"
                send_command(message, request_id)
                
            except KeyboardInterrupt:
                print("\n👋 退出")
                break
            except Exception as e:
                print(f"❌ 错误: {str(e)}")


if __name__ == "__main__":
    main()

