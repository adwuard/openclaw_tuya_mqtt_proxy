#!/usr/bin/env python3
"""
MQTT 测试接收脚本
监听 AI_RET topic，接收 AI 返回的结果
"""

import paho.mqtt.client as mqtt
import json
import sys
import os

# MQTT 配置
# 支持从环境变量读取，或直接修改这里的值
# 可以使用 localhost、IP 地址（如 192.168.1.100）或域名
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_RET = os.getenv("MQTT_TOPIC_RET", "AI_RET")


def on_connect(client, userdata, flags, rc):
    """连接回调"""
    if rc == 0:
        print(f"✅ 已连接到 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        # 订阅 AI_RET topic
        client.subscribe(MQTT_TOPIC_RET, qos=1)
        print(f"📡 已订阅 topic: {MQTT_TOPIC_RET}")
        print("⏳ 等待接收消息...\n")
    else:
        print(f"❌ 连接失败，错误代码: {rc}")


def on_message(client, userdata, msg):
    """接收到消息的回调"""
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        print("=" * 60)
        print(f"📨 收到消息 - Topic: {topic}")
        print("=" * 60)
        
        # 尝试解析 JSON
        try:
            data = json.loads(payload)
            print(f"⏰ 时间戳: {data.get('timestamp', 'N/A')}")
            print(f"🆔 请求ID: {data.get('request_id', 'N/A')}")
            print(f"📝 原始指令: {data.get('message', 'N/A')}")
            print(f"✅ 状态: {data.get('status', 'N/A')}")
            print("\n📋 AI 响应:")
            print("-" * 60)
            response = data.get('response', '')
            print(response)
            print("-" * 60)
            
            if 'error' in data:
                print(f"\n❌ 错误信息: {data['error']}")
                
        except json.JSONDecodeError:
            # 如果不是 JSON，直接显示原始内容
            print("📋 响应内容:")
            print("-" * 60)
            print(payload)
            print("-" * 60)
        
        print()
        
    except Exception as e:
        print(f"❌ 处理消息时出错: {str(e)}")


def main():
    """主函数"""
    print("=" * 60)
    print("MQTT 测试接收工具")
    print("=" * 60)
    print(f"监听 Topic: {MQTT_TOPIC_RET}")
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print("=" * 60)
    print()
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        # 连接到 broker
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # 开始循环监听
        print("按 Ctrl+C 退出\n")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信号")
        client.disconnect()
        print("👋 已断开连接")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

