#!/usr/bin/env python3
"""
MQTT-OpenClaw bridge service.

Flow:
1. Subscribe to `openclaw/device/user_speech_text`
2. Call `openclaw agent --agent main --message ...`
3. Publish results to `openclaw/server/response`
"""

import paho.mqtt.client as mqtt
import subprocess
import json
import logging
import sys
import os
from datetime import datetime

# Logging
class ColorFormatter(logging.Formatter):
    """ANSI color formatter for stdout logs."""

    RESET = "\033[0m"
    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }

    def format(self, record):
        base = super().format(record)
        use_color = sys.stdout.isatty() and os.getenv("NO_COLOR") is None
        if not use_color:
            return base
        color = self.COLORS.get(record.levelno, "")
        return f"{color}{base}{self.RESET}"


stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(
    ColorFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

logging.basicConfig(level=logging.INFO, handlers=[stream_handler])
logger = logging.getLogger(__name__)

# Recommended: run MQTT bridge and OpenClaw on the same host.
# `configs/mosquitto_listen_all.conf` can expose broker on 0.0.0.0:1883.

def _env_first(*keys, default):
    """Return first non-empty environment value by key order."""
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return default


MQTT_BROKER_HOST = _env_first("MQTT_BROKER_HOST", "MQTT_BROKER", default="localhost")
MQTT_BROKER_PORT = int(_env_first("MQTT_BROKER_PORT", "MQTT_PORT", default="1883"))
MQTT_TOPIC_IN_COMMAND = _env_first(
    "MQTT_TOPIC_IN_COMMAND",
    "MQTT_TOPIC_CMD",
    default="openclaw/device/user_speech_text",
)
MQTT_TOPIC_OUT_RESULT = _env_first(
    "MQTT_TOPIC_OUT_RESULT",
    "MQTT_TOPIC_RET",
    default="openclaw/server/response",
)
MQTT_BRIDGE_CLIENT_ID = _env_first(
    "MQTT_BRIDGE_CLIENT_ID",
    "MQTT_CLIENT_ID",
    default=f"openclaw_bridge_srv_{os.getpid()}",
)


# OpenClaw configuration
OPENCLAW_AGENT = "main"
OPENCLAW_CMD = "openclaw"


class OpenClawBridge:
    """MQTT-OpenClaw bridge."""
    
    def __init__(self):
        # Prefer modern callback API when available.
        try:
            self.client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=MQTT_BRIDGE_CLIENT_ID
            )
        except (AttributeError, ValueError):
            # Fallback for older paho-mqtt versions.
            try:
                self.client = mqtt.Client(
                    mqtt.CallbackAPIVersion.VERSION1,
                    client_id=MQTT_BRIDGE_CLIENT_ID
                )
            except AttributeError:
                self.client = mqtt.Client(client_id=MQTT_BRIDGE_CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
    def on_connect(self, client, userdata, flags, rc, properties=None):
        """MQTT connect callback (VERSION1/VERSION2 compatible)."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
            client.subscribe(MQTT_TOPIC_IN_COMMAND, qos=1)
            logger.info(f"Subscribed to topic: {MQTT_TOPIC_IN_COMMAND}")
        else:
            logger.error(f"MQTT connection failed (rc={rc})")
            
    def on_disconnect(self, client, userdata, rc, properties=None):
        """MQTT disconnect callback (VERSION1/VERSION2 compatible)."""
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnect (rc={rc})")
        else:
            logger.info("MQTT disconnected")
            
    def on_message(self, client, userdata, msg):
        """Handle inbound MQTT command message."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            logger.info(f"Message received on topic: {topic}")
            
            try:
                cmd_data = json.loads(payload)
                message = cmd_data.get('message', payload)
                request_id = cmd_data.get('request_id', None)
            except json.JSONDecodeError:
                message = payload
                request_id = None
                logger.debug("Payload is plain text (not JSON)")
            
            logger.info("Calling OpenClaw...")
            result = self.call_openclaw(message)
            
            response = {
                'timestamp': datetime.now().isoformat(),
                'request_id': request_id,
                'message': message,
                'response': result,
                'status': 'success' if result else 'error'
            }
            
            response_json = json.dumps(response, ensure_ascii=False)
            client.publish(MQTT_TOPIC_OUT_RESULT, response_json, qos=1)
            logger.info(f"Published response to topic: {MQTT_TOPIC_OUT_RESULT}")
            
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}", exc_info=True)
            error_response = {
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
            client.publish(MQTT_TOPIC_OUT_RESULT, json.dumps(error_response, ensure_ascii=False), qos=1)
    
    def call_openclaw(self, message):
        """
        Call OpenClaw agent and return response text.
        """
        try:
            cmd = [
                OPENCLAW_CMD,
                'agent',
                '--agent', OPENCLAW_AGENT,
                '--message', message
            ]
            
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=False
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                lines = output.split('\n')
                content_start = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith('🦞') and 'OpenClaw' not in line:
                        content_start = i
                        break
                
                response = '\n'.join(lines[content_start:]).strip()
                return response if response else "Completed with no response content."
            else:
                error_msg = f"OpenClaw command failed: {result.stderr}"
                logger.error(error_msg)
                return f"Error: {error_msg}"
                
        except subprocess.TimeoutExpired:
            error_msg = "OpenClaw command timed out (over 5 minutes)."
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"OpenClaw invocation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"Error: {error_msg}"
    
    def start(self):
        """Start MQTT bridge service."""
        try:
            logger.info("Starting MQTT-OpenClaw bridge service...")
            logger.info(f"Broker: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
            logger.info(f"Inbound topic: {MQTT_TOPIC_IN_COMMAND}")
            logger.info(f"Outbound topic: {MQTT_TOPIC_OUT_RESULT}")
            
            try:
                self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
            except Exception as e:
                logger.error(f"Broker connection failed: {str(e)}")
                logger.error("Check broker status: sudo systemctl status mosquitto")
                logger.error("Check listening port: ss -tlnp | rg 1883")
                logger.error("Check broker host/IP value")
                sys.exit(1)
            
            logger.info("Waiting for messages...")
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            logger.info("Shutdown signal received. Stopping...")
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Service stopped")
        except Exception as e:
            logger.error(f"Service start failed: {str(e)}", exc_info=True)
            sys.exit(1)


def main():
    """Main entrypoint."""
    bridge = OpenClawBridge()
    bridge.start()


if __name__ == "__main__":
    main()

