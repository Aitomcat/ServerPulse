import os
import yaml
from typing import List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class ServerConfig:
    host: str
    port: int = 22
    user: str = "root"
    password: str = None
    key_file: str = None
    tags: Dict[str, str] = field(default_factory=dict)  # 额外标签，如 env:prod

@dataclass
class MonitorConfig:
    servers: List[ServerConfig]
    thresholds: Dict[str, float] = field(default_factory=lambda: {"cpu": 90, "memory": 80, "disk": 85})
    alert_channels: List[str] = field(default_factory=lambda: ["dingtalk"])
    alert_config: Dict[str, Any] = field(default_factory=dict)  # 各通道的配置（webhook等）
    metrics_commands: Dict[str, str] = field(default_factory=lambda: {
        "cpu": "top -bn1 | grep 'Cpu(s)' | awk '{print $8}'",
        "memory": "free -m | awk '/^Mem:/{printf \"%.2f\", $3/$2*100}'",
        "disk": "df -h / | awk 'NR==2{print $5}' | tr -d '%'"
    })
    concurrency: int = 5   # 并发线程数
    log_file: str = "serverpulse.log"

def load_config(path: str) -> MonitorConfig:
    """从 YAML 文件加载配置并返回 MonitorConfig 对象"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    servers = [ServerConfig(**s) for s in data.get('servers', [])]
    thresholds = data.get('thresholds', {})
    alert_channels = data.get('alert_channels', ['dingtalk'])
    alert_config = data.get('alert_config', {})
    metrics_commands = data.get('metrics_commands', {
        "cpu": "top -bn1 | grep 'Cpu(s)' | awk '{print $8}'",
        "memory": "free -m | awk '/^Mem:/{printf \"%.2f\", $3/$2*100}'",
        "disk": "df -h / | awk 'NR==2{print $5}' | tr -d '%'"
    })
    concurrency = data.get('concurrency', 5)
    log_file = data.get('log_file', 'serverpulse.log')

    return MonitorConfig(
        servers=servers,
        thresholds=thresholds,
        alert_channels=alert_channels,
        alert_config=alert_config,
        metrics_commands=metrics_commands,
        concurrency=concurrency,
        log_file=log_file
    )