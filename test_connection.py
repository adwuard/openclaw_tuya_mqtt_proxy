#!/usr/bin/env python3
"""
MQTT 连接诊断脚本
用于测试 MQTT 连接问题
"""

import paho.mqtt.client as mqtt
import time
import sys
import os

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

def test_connection():
    """测试 MQTT 连接"""
    print(f"测试连接到 {MQTT_BROKER}:{MQTT_PORT}")
    print("=" * 60)
    
    # 使用唯一的客户端ID
    client_id = f"test_client_{int(time.time())}"
    print(f"客户端ID: {client_id}")
    
    client = mqtt.Client(client_id=client_id)
    
    connected = False
    disconnected = False
    
    def on_connect(client, userdata, flags, rc):
        nonlocal connected
        connected = True
        if rc == 0:
            print(f"✅ 连接成功！")
            print(f"   标志: {flags}")
        else:
            print(f"❌ 连接失败，错误代码: {rc}")
            error_messages = {
                1: "协议版本不正确",
                2: "客户端ID无效",
                3: "服务器不可用",
                4: "用户名或密码错误",
                5: "未授权"
            }
            print(f"   原因: {error_messages.get(rc, '未知错误')}")
    
    def on_disconnect(client, userdata, rc):
        nonlocal disconnected
        disconnected = True
        if rc == 0:
            print(f"🔌 正常断开连接")
        else:
            print(f"⚠️  意外断开，错误代码: {rc}")
            error_messages = {
                1: "网络错误",
                2: "协议错误",
                3: "连接丢失",
                4: "传输错误",
                5: "其他错误",
                6: "客户端错误",
                7: "服务器错误"
            }
            print(f"   原因: {error_messages.get(rc, '未知错误')}")
    
    def on_subscribe(client, userdata, mid, granted_qos):
        print(f"✅ 订阅成功，QoS: {granted_qos}")
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    
    try:
        print("\n正在连接...")
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()
        
        # 等待连接
        timeout = 5
        start_time = time.time()
        while not connected and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if not connected:
            print("❌ 连接超时")
            return False
        
        # 等待一下看是否立即断开
        time.sleep(2)
        
        if disconnected:
            print("❌ 连接后立即断开")
            return False
        
        # 尝试订阅
        print("\n尝试订阅 test topic...")
        result = client.subscribe("test", qos=1)
        time.sleep(1)
        
        # 尝试发布
        print("尝试发布测试消息...")
        result = client.publish("test", "hello", qos=1)
        time.sleep(1)
        
        print("\n✅ 连接测试成功！")
        print("   连接保持正常，可以订阅和发布")
        
        client.loop_stop()
        client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

