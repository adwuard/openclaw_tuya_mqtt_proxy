#!/usr/bin/env python3
"""
不使用外部 MQTT broker 的测试脚本
直接测试 OpenClaw 调用功能
"""

import subprocess
import json
from datetime import datetime

def test_openclaw_direct(message):
    """直接测试 OpenClaw 调用"""
    print("=" * 60)
    print("直接测试 OpenClaw 调用")
    print("=" * 60)
    print(f"📝 测试消息: {message}")
    print()
    
    try:
        cmd = [
            'openclaw',
            'agent',
            '--agent', 'main',
            '--message', message
        ]
        
        print(f"🔧 执行命令: {' '.join(cmd)}")
        print()
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            lines = output.split('\n')
            
            # 找到实际内容开始的位置
            content_start = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith('🦞') and 'OpenClaw' not in line:
                    content_start = i
                    break
            
            response = '\n'.join(lines[content_start:]).strip()
            
            print("✅ OpenClaw 调用成功")
            print()
            print("📋 AI 响应:")
            print("-" * 60)
            print(response)
            print("-" * 60)
            
            # 模拟 MQTT 响应格式
            mqtt_response = {
                'timestamp': datetime.now().isoformat(),
                'request_id': 'test_direct',
                'message': message,
                'response': response,
                'status': 'success'
            }
            
            print()
            print("📤 模拟 MQTT 响应格式:")
            print(json.dumps(mqtt_response, ensure_ascii=False, indent=2))
            
            return True
        else:
            print(f"❌ OpenClaw 执行失败")
            print(f"错误: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ OpenClaw 执行超时")
        return False
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        message = "帮我生成一个AI情报分析的文件夹放在桌面上"
    
    test_openclaw_direct(message)


