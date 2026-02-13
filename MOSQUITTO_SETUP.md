# Mosquitto 配置指南 - 监听局域网IP

## 问题

Mosquitto 默认只监听 `127.0.0.1:1883`（localhost），无法从局域网内的其他设备连接。

## 解决方案

### 方法 1: 使用配置脚本（推荐）

```bash
cd ~/mqtt_openclaw_bridge
sudo bash setup_mosquitto.sh
```

### 方法 2: 手动配置

1. **创建配置文件：**

```bash
sudo nano /etc/mosquitto/conf.d/listen_all.conf
```

2. **添加以下内容：**

```conf
# 监听所有网络接口（0.0.0.0）的 1883 端口
listener 1883 0.0.0.0

# 允许匿名连接
allow_anonymous true
```

3. **重启 Mosquitto：**

```bash
sudo systemctl restart mosquitto
```

4. **验证配置：**

```bash
# 检查服务状态
sudo systemctl status mosquitto

# 检查监听端口（应该看到 0.0.0.0:1883）
netstat -tlnp | grep 1883
# 或
ss -tlnp | grep 1883
```

## 验证连接

### 从本机测试：

```bash
# 测试本地连接
mosquitto_pub -h localhost -t test -m "hello"
mosquitto_sub -h localhost -t test
```

### 从局域网测试：

```bash
# 在其他设备上测试
mosquitto_pub -h 192.168.254.129 -t test -m "hello"
mosquitto_sub -h 192.168.254.129 -t test
```

## 查看日志

```bash
# 查看系统日志
sudo journalctl -u mosquitto -f

# 查看 Mosquitto 日志文件
sudo tail -f /var/log/mosquitto/mosquitto.log
```

## 安全建议

**生产环境建议：**

1. **禁用匿名连接：**
```conf
allow_anonymous false
password_file /etc/mosquitto/passwd
```

2. **创建用户：**
```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd username
```

3. **使用 TLS/SSL：**
```conf
listener 8883
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
```

## 故障排查

### 问题 1: 连接被拒绝

**检查：**
- Mosquitto 是否运行：`sudo systemctl status mosquitto`
- 端口是否监听：`netstat -tlnp | grep 1883`
- 防火墙是否开放：`sudo ufw status`

**解决：**
```bash
# 开放防火墙端口
sudo ufw allow 1883/tcp
```

### 问题 2: 配置文件错误

**检查配置：**
```bash
sudo mosquitto -c /etc/mosquitto/mosquitto.conf -t
```

### 问题 3: 权限问题

**检查日志文件权限：**
```bash
sudo chown mosquitto:mosquitto /var/log/mosquitto/mosquitto.log
```

