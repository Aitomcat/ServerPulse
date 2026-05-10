import requests
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class Alerter:
    """告警基类"""
    def send(self, anomalies: List[Dict], extra_info: str = "") -> bool:
        raise NotImplementedError

class DingTalkAlerter(Alerter):
    """钉钉群机器人告警"""
    def __init__(self, webhook: str):
        self.webhook = webhook

    def send(self, anomalies: List[Dict], extra_info: str = "") -> bool:
        title = "## 🚨 服务器资源告警\n"
        lines = []
        for a in anomalies:
            tags = " ".join([f"{k}={v}" for k,v in a.get("tags", {}).items()])
            line = f"- **{a['host']}** ({tags}) {a['metric'].upper()} **{a['value']}%** > 阈值 {a['threshold']}%"
            lines.append(line)
        text = title + "\n".join(lines) + f"\n> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if extra_info:
            text += f"\n{extra_info}"

        payload = {"msgtype": "markdown", "markdown": {"title": "ServerPulse Alert", "text": text}}
        try:
            resp = requests.post(self.webhook, data=json.dumps(payload),
                                 headers={"Content-Type": "application/json"}, timeout=5)
            if resp.status_code == 200 and resp.json().get("errcode") == 0:
                logger.info("钉钉告警发送成功")
                return True
            else:
                logger.error(f"钉钉告警失败: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"钉钉告警异常: {e}")
            return False

class WeChatWorkAlerter(Alerter):
    """企业微信机器人告警"""
    def __init__(self, webhook: str):
        self.webhook = webhook

    def send(self, anomalies: List[Dict], extra_info: str = "") -> bool:
        content = "**服务器资源告警**\n"
        for a in anomalies:
            content += f"> {a['host']} {a['metric']}: {a['value']}% > {a['threshold']}%\n"
        if extra_info:
            content += extra_info
        payload = {
            "msgtype": "markdown",
            "markdown": {"content": content}
        }
        try:
            resp = requests.post(self.webhook, json=payload, timeout=5)
            return resp.status_code == 200 and resp.json().get("errcode") == 0
        except Exception as e:
            logger.error(f"企业微信告警失败: {e}")
            return False

def get_alerters(channels: List[str], alert_config: Dict[str, Any]) -> List[Alerter]:
    """根据配置的通道名称列表，返回对应的 Alerter 实例列表"""
    alerters = []
    for ch in channels:
        if ch == "dingtalk" and "dingtalk" in alert_config:
            alerters.append(DingTalkAlerter(alert_config["dingtalk"]["webhook"]))
        elif ch == "wechat_work" and "wechat_work" in alert_config:
            alerters.append(WeChatWorkAlerter(alert_config["wechat_work"]["webhook"]))
        else:
            logger.warning(f"未配置或未知的告警通道: {ch}")
    return alerters