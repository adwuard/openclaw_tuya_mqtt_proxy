# 局域网部署指南

## 使用 IP 地址配置 MQTT Broker

MQTT 完全支持使用 IP 地址连接，非常适合局域网部署。

## 配置方法

### 方法 1: 直接修改代码（最简单）

编辑 `mqtt_openclaw_bridge.py`，修改第 29 行：

```python
MQTT_BROKER = "192.168.254.129"  # 替换为你的 MQTT 服务器 IP
```

同样修改 `test_sender.py` 和 `test_receiver.py` 中的 `MQTT_BROKER`。

### 方法 2: 使用环境变量（推荐）

**在桥接服务器上：**
```bash
export MQTT_BROKER=192.168.254.129
export MQTT_PORT=1883
python3 mqtt_openclaw_bridge.py
```

**在客户端设备上：**
```bash
export MQTT_BROKER=192.168.254.129
export MQTT_PORT=1883
python3 test_sender.py "你的消息"
```

### 方法 3: 创建配置文件

创建 `config.py` 文件（参考 `config_example.py`），然后修改主程序导入配置。

## 获取服务器 IP 地址

在 MQTT 服务器上运行：
```bash
ip addr show | grep -E "inet " | grep -v "127.0.0.1"
```

或者：
```bash
hostname -I
```

## 局域网部署注意事项

### 1. 防火墙配置

确保 MQTT 端口（默认 1883）未被防火墙阻止：

```bash
# Ubuntu/Debian
sudo ufw allow 1883/tcp
# 或
sudo iptables -A INPUT -p tcp --dport 1883 -j ACCEPT
```

### 2. Mosquitto 配置

编辑 `/etc/mosquitto/mosquitto.conf`，确保监听所有网络接口：

```conf
# 监听所有网络接口（0.0.0.0）
listener 1883 0.0.0.0

# 或者监听特定 IP
# listener 1883 192.168.254.129
```

重启 Mosquitto：
```bash
sudo systemctl restart mosquitto
```

### 3. 验证连接

**在服务器上测试：**
```bash
mosquitto_sub -h 192.168.254.129 -t test
```

**在客户端设备上测试：**
```bash
mosquitto_pub -h 192.168.254.129 -t test -m "hello"
```

### 4. 安全建议

**生产环境建议：**

1. **使用认证：**
```conf
# /etc/mosquitto/mosquitto.conf
allow_anonymous false
password_file /etc/mosquitto/passwd
```

2. **使用 TLS/SSL：**
```conf
listener 8883
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
```

3. **限制访问：**
```conf
acl_file /etc/mosquitto/acl
```

## 完整部署示例

### 服务器端（192.168.254.129）

```bash
# 1. 安装 Mosquitto
sudo apt-get install mosquitto mosquitto-clients

# 2. 配置监听所有接口
sudo nano /etc/mosquitto/mosquitto.conf
# 添加: listener 1883 0.0.0.0

# 3. 启动服务
sudo systemctl restart mosquitto

# 4. 启动桥接服务
cd ~/mqtt_openclaw_bridge
export MQTT_BROKER=192.168.254.129
python3 mqtt_openclaw_bridge.py
```

### 客户端设备

```bash
# 1. 安装依赖
pip3 install --user paho-mqtt

# 2. 发送消息
cd ~/mqtt_openclaw_bridge
export MQTT_BROKER=192.168.254.129
python3 test_sender.py "你的消息"
```

## 测试连接

```bash
# 测试 MQTT broker 是否可达
ping 192.168.254.129

# 测试端口是否开放
telnet 192.168.254.129 1883
# 或
nc -zv 192.168.254.129 1883
```

## 常见问题

### Q: 连接被拒绝 (Connection refused)
A: 检查：
- Mosquitto 是否运行: `sudo systemctl status mosquitto`
- 防火墙是否开放端口
- Mosquitto 是否监听 0.0.0.0 而不是 127.0.0.1

### Q: 超时 (Timeout)
A: 检查：
- IP 地址是否正确
- 网络是否连通: `ping <IP地址>`
- 端口是否被占用: `netstat -tlnp | grep 1883`

### Q: 不同网段无法连接
A: 确保：
- 路由器允许跨网段通信
- 防火墙规则正确
- 使用正确的网关 IP

