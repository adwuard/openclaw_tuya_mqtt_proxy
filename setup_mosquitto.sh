#!/bin/bash
# Mosquitto 配置脚本 - 让 Mosquitto 监听所有网络接口

echo "=========================================="
echo "配置 Mosquitto 监听所有网络接口"
echo "=========================================="
echo

# 检查是否有 sudo 权限
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  此脚本需要 sudo 权限"
    echo "   请运行: sudo bash setup_mosquitto.sh"
    exit 1
fi

# 创建配置文件
CONF_FILE="/etc/mosquitto/conf.d/listen_all.conf"
echo "创建配置文件: $CONF_FILE"

cat > "$CONF_FILE" << 'EOF'
# 监听所有网络接口（0.0.0.0）的 1883 端口
listener 1883 0.0.0.0

# 允许匿名连接（生产环境建议关闭）
allow_anonymous true

# 注意：log_dest 和 log_type 已在主配置文件中定义，不要重复配置
EOF

echo "✅ 配置文件已创建"
echo

# 检查配置文件语法（注意：某些版本的 mosquitto 不支持 -t 选项）
echo "检查配置文件语法..."
if mosquitto -c /etc/mosquitto/mosquitto.conf -t 2>&1 | grep -q "Error"; then
    echo "⚠️  配置文件可能有语法错误，请检查日志"
else
    echo "✅ 配置文件语法检查完成"
fi

echo
echo "重启 Mosquitto 服务..."
systemctl restart mosquitto

sleep 2

# 检查服务状态
echo
echo "检查服务状态..."
systemctl status mosquitto --no-pager | head -15

echo
echo "检查监听端口..."
netstat -tlnp | grep 1883 || ss -tlnp | grep 1883

echo
echo "=========================================="
echo "配置完成！"
echo "=========================================="
echo "Mosquitto 现在应该监听所有网络接口"
echo "可以从 192.168.100.132:1883 连接"

