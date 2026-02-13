#!/usr/bin/env python3
"""
MQTT-OpenClaw 桥接服务器
功能：
1. 监听 MQTT topic: AI_CMD，接收其他设备发送的指令
2. 将指令封装后调用 openclaw agent 命令
3. 将 AI 返回的结果发布到 MQTT topic: AI_RET
"""

import paho.mqtt.client as mqtt
import subprocess
import json
import logging
import sys
import os
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mqtt_bridge.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# MQTT 配置
# 支持从环境变量读取，或直接修改这里的值
# 可以使用 localhost、IP 地址（如 192.168.1.100）或域名
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")  # MQTT broker 地址
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))      # MQTT broker 端口
MQTT_TOPIC_CMD = os.getenv("MQTT_TOPIC_CMD", "AI_CMD")  # 接收指令的 topic
MQTT_TOPIC_RET = os.getenv("MQTT_TOPIC_RET", "AI_RET")  # 发送结果的 topic
# 使用唯一的客户端ID，避免冲突
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", f"openclaw_bridge_{os.getpid()}")

# OpenClaw 配置
OPENCLAW_AGENT = "main"   # 使用的 agent ID
OPENCLAW_CMD = "openclaw" # openclaw 命令路径


class OpenClawBridge:
    """MQTT-OpenClaw 桥接类"""
    
    def __init__(self):
        self.client = mqtt.Client(client_id=MQTT_CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
    def on_connect(self, client, userdata, flags, rc):
        """MQTT 连接回调"""
        if rc == 0:
            logger.info(f"✅ 成功连接到 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
            # 订阅 AI_CMD topic
            client.subscribe(MQTT_TOPIC_CMD, qos=1)
            logger.info(f"📡 已订阅 topic: {MQTT_TOPIC_CMD}")
        else:
            logger.error(f"❌ 连接失败，错误代码: {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        """MQTT 断开连接回调"""
        if rc != 0:
            logger.warning(f"⚠️  意外断开连接，错误代码: {rc}")
        else:
            logger.info("🔌 已断开 MQTT 连接")
            
    def on_message(self, client, userdata, msg):
        """接收到 MQTT 消息的回调"""
        try:
            # 解析接收到的消息
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            logger.info(f"📨 收到消息 - Topic: {topic}, Payload: {payload}")
            
            # 解析 JSON 格式的指令
            try:
                cmd_data = json.loads(payload)
                message = cmd_data.get('message', payload)  # 支持 JSON 格式或纯文本
                request_id = cmd_data.get('request_id', None)  # 可选的请求 ID
            except json.JSONDecodeError:
                # 如果不是 JSON，直接使用原始文本
                message = payload
                request_id = None
                logger.info("📝 收到纯文本消息，将直接作为指令处理")
            
            # 调用 OpenClaw 处理指令
            logger.info(f"🤖 正在调用 OpenClaw 处理指令: {message}")
            result = self.call_openclaw(message)
            
            # 构建返回数据
            response = {
                'timestamp': datetime.now().isoformat(),
                'request_id': request_id,
                'message': message,
                'response': result,
                'status': 'success' if result else 'error'
            }
            
            # 发布结果到 AI_RET topic
            response_json = json.dumps(response, ensure_ascii=False)
            client.publish(MQTT_TOPIC_RET, response_json, qos=1)
            logger.info(f"📤 已发布结果到 topic: {MQTT_TOPIC_RET}")
            logger.info(f"📋 返回内容: {result[:200]}..." if len(result) > 200 else f"📋 返回内容: {result}")
            
        except Exception as e:
            logger.error(f"❌ 处理消息时出错: {str(e)}", exc_info=True)
            # 发送错误响应
            error_response = {
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
            client.publish(MQTT_TOPIC_RET, json.dumps(error_response, ensure_ascii=False), qos=1)
    
    def call_openclaw(self, message):
        """
        调用 OpenClaw agent 处理消息
        返回 AI 的响应文本
        """
        try:
            # 构建 openclaw 命令
            cmd = [
                OPENCLAW_CMD,
                'agent',
                '--agent', OPENCLAW_AGENT,
                '--message', message
            ]
            
            logger.debug(f"🔧 执行命令: {' '.join(cmd)}")
            
            # 执行命令并捕获输出
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                check=False
            )
            
            if result.returncode == 0:
                # 提取 AI 的响应（去掉 OpenClaw 的提示信息）
                output = result.stdout.strip()
                # 移除 OpenClaw 的 banner 和格式字符
                lines = output.split('\n')
                # 找到实际内容开始的位置（通常在 banner 之后）
                content_start = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith('🦞') and 'OpenClaw' not in line:
                        content_start = i
                        break
                
                response = '\n'.join(lines[content_start:]).strip()
                return response if response else "处理完成，但未返回内容"
            else:
                error_msg = f"OpenClaw 执行失败: {result.stderr}"
                logger.error(error_msg)
                return f"错误: {error_msg}"
                
        except subprocess.TimeoutExpired:
            error_msg = "OpenClaw 执行超时（超过5分钟）"
            logger.error(error_msg)
            return f"错误: {error_msg}"
        except Exception as e:
            error_msg = f"调用 OpenClaw 时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"错误: {error_msg}"
    
    def start(self):
        """启动 MQTT 桥接服务"""
        try:
            logger.info(f"🚀 启动 MQTT-OpenClaw 桥接服务...")
            logger.info(f"📍 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
            logger.info(f"📥 监听 Topic: {MQTT_TOPIC_CMD}")
            logger.info(f"📤 发布 Topic: {MQTT_TOPIC_RET}")
            logger.info(f"🆔 客户端ID: {MQTT_CLIENT_ID}")
            
            # 连接到 MQTT broker
            try:
                self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            except Exception as e:
                logger.error(f"❌ 连接失败: {str(e)}")
                logger.error("   请检查:")
                logger.error("   1. Mosquitto 是否运行: sudo systemctl status mosquitto")
                logger.error("   2. 端口是否正确: netstat -tlnp | grep 1883")
                logger.error("   3. IP 地址是否正确")
                sys.exit(1)
            
            # 开始循环监听消息
            logger.info("⏳ 等待消息...")
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            logger.info("\n🛑 收到停止信号，正在关闭...")
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("👋 服务已停止")
        except Exception as e:
            logger.error(f"❌ 服务启动失败: {str(e)}", exc_info=True)
            sys.exit(1)


def main():
    """主函数"""
    bridge = OpenClawBridge()
    bridge.start()


if __name__ == "__main__":
    main()

