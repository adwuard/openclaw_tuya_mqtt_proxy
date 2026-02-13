#!/usr/bin/env python3
"""
完整的 MQTT-OpenClaw 集成测试
测试桥接服务的完整功能
"""

import time
import threading
import subprocess
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("❌ 请先安装 paho-mqtt: pip3 install --break-system-packages paho-mqtt")
    sys.exit(1)

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_CMD = "AI_CMD"
MQTT_TOPIC_RET = "AI_RET"

class IntegrationTest:
    def __init__(self):
        self.received_response = None
        self.test_complete = False
        self.client = None
        
    def on_connect(self, client, userdata, flags, rc):
        """MQTT 连接回调"""
        if rc == 0:
            print("✅ 测试客户端已连接到 MQTT Broker")
            client.subscribe(MQTT_TOPIC_RET, qos=1)
            print(f"📡 已订阅响应 topic: {MQTT_TOPIC_RET}")
        else:
            print(f"❌ 连接失败，错误代码: {rc}")
            
    def on_message(self, client, userdata, msg):
        """接收到消息的回调"""
        try:
            import json
            data = json.loads(msg.payload.decode('utf-8'))
            self.received_response = data
            self.test_complete = True
            print("\n" + "=" * 60)
            print("📨 收到 AI 响应！")
            print("=" * 60)
            print(f"⏰ 时间戳: {data.get('timestamp', 'N/A')}")
            print(f"📝 原始指令: {data.get('message', 'N/A')}")
            print(f"✅ 状态: {data.get('status', 'N/A')}")
            print("\n📋 AI 响应内容:")
            print("-" * 60)
            response_text = data.get('response', '')
            # 只显示前500个字符
            if len(response_text) > 500:
                print(response_text[:500] + "...")
            else:
                print(response_text)
            print("-" * 60)
        except Exception as e:
            print(f"❌ 解析响应时出错: {str(e)}")
            self.test_complete = True
            
    def test_mqtt_connection(self):
        """测试 MQTT 连接"""
        print("=" * 60)
        print("步骤 1: 测试 MQTT Broker 连接")
        print("=" * 60)
        
        test_client = mqtt.Client()
        try:
            test_client.connect(MQTT_BROKER, MQTT_PORT, 10)
            test_client.disconnect()
            print(f"✅ MQTT Broker ({MQTT_BROKER}:{MQTT_PORT}) 连接成功")
            return True
        except Exception as e:
            print(f"❌ MQTT Broker 连接失败: {str(e)}")
            print("\n💡 提示: 请先安装并启动 Mosquitto:")
            print("   sudo apt-get install mosquitto mosquitto-clients")
            print("   sudo systemctl start mosquitto")
            return False
            
    def test_bridge_service(self):
        """测试桥接服务"""
        print("\n" + "=" * 60)
        print("步骤 2: 检查桥接服务代码")
        print("=" * 60)
        
        bridge_file = os.path.join(os.path.dirname(__file__), 'mqtt_openclaw_bridge.py')
        if os.path.exists(bridge_file):
            print("✅ 桥接服务文件存在")
            # 检查代码语法
            result = subprocess.run(
                ['python3', '-m', 'py_compile', bridge_file],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ 桥接服务代码语法正确")
                return True
            else:
                print(f"❌ 代码语法错误: {result.stderr}")
                return False
        else:
            print("❌ 桥接服务文件不存在")
            return False
            
    def test_openclaw(self):
        """测试 OpenClaw"""
        print("\n" + "=" * 60)
        print("步骤 3: 测试 OpenClaw 调用")
        print("=" * 60)
        
        try:
            result = subprocess.run(
                ['openclaw', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print("✅ OpenClaw 可用")
                version = result.stdout.strip().split('\n')[0]
                print(f"   版本: {version}")
                return True
            else:
                print("❌ OpenClaw 不可用")
                return False
        except FileNotFoundError:
            print("❌ OpenClaw 未安装或不在 PATH 中")
            return False
        except Exception as e:
            print(f"❌ 测试 OpenClaw 时出错: {str(e)}")
            return False
            
    def run_full_test(self, test_message="今天深圳天气怎么样"):
        """运行完整测试"""
        print("\n" + "=" * 60)
        print("MQTT-OpenClaw 桥接集成测试")
        print("=" * 60)
        print()
        
        # 步骤 1: 测试 MQTT 连接
        if not self.test_mqtt_connection():
            print("\n⚠️  MQTT Broker 未运行，无法进行完整测试")
            print("   但可以测试 OpenClaw 功能（见 test_without_broker.py）")
            return False
            
        # 步骤 2: 测试桥接服务
        if not self.test_bridge_service():
            return False
            
        # 步骤 3: 测试 OpenClaw
        if not self.test_openclaw():
            return False
            
        # 步骤 4: 完整流程测试
        print("\n" + "=" * 60)
        print("步骤 4: 完整流程测试")
        print("=" * 60)
        print("⚠️  注意: 此测试需要桥接服务正在运行")
        print("   请先在一个终端运行: python3 mqtt_openclaw_bridge.py")
        print()
        
        response = input("桥接服务是否已启动? (y/n): ").strip().lower()
        if response != 'y':
            print("请先启动桥接服务，然后重新运行此测试")
            return False
            
        # 创建 MQTT 客户端接收响应
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            # 等待连接建立
            time.sleep(2)
            
            # 发送测试消息
            print(f"\n📤 发送测试消息到 {MQTT_TOPIC_CMD}:")
            print(f"   消息: {test_message}")
            
            payload = json.dumps({
                'message': test_message,
                'request_id': f'test_{int(time.time())}'
            }, ensure_ascii=False)
            
            self.client.publish(MQTT_TOPIC_CMD, payload, qos=1)
            print("✅ 消息已发送，等待响应...")
            
            # 等待响应（最多30秒）
            timeout = 30
            start_time = time.time()
            while not self.test_complete and (time.time() - start_time) < timeout:
                time.sleep(0.5)
                
            if self.test_complete:
                print("\n✅ 测试完成！")
                return True
            else:
                print(f"\n⚠️  超时（{timeout}秒）未收到响应")
                print("   请检查桥接服务是否正常运行")
                return False
                
        except Exception as e:
            print(f"\n❌ 测试过程中出错: {str(e)}")
            return False
        finally:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()

if __name__ == "__main__":
    import json
    
    test = IntegrationTest()
    
    # 从命令行参数获取测试消息
    if len(sys.argv) > 1:
        test_message = " ".join(sys.argv[1:])
    else:
        test_message = "今天深圳天气怎么样"
        
    success = test.run_full_test(test_message)
    sys.exit(0 if success else 1)


