import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from .ssh_client import SSHClient
from .config import MonitorConfig, ServerConfig

logger = logging.getLogger(__name__)

def collect_single_server(server: ServerConfig, commands: Dict[str, str]) -> Optional[Dict]:
    """采集单台服务器的所有指标"""
    metrics = {"host": server.host, **server.tags}
    try:
        with SSHClient(server.host, server.port, server.user, server.password, server.key_file) as client:
            for metric_name, cmd in commands.items():
                result = client.exec_command(cmd)
                if result is None:
                    logger.warning(f"{server.host} 指标 {metric_name} 采集失败")
                    return None
                # 特殊处理 CPU idle 反算
                if metric_name == "cpu":
                    try:
                        cpu_idle = float(result)
                        metrics["cpu"] = round(100 - cpu_idle, 2)
                    except:
                        logger.error(f"{server.host} CPU 解析失败")
                        return None
                else:
                    metrics[metric_name] = float(result)
        logger.info(f"{server.host} 采集成功: { {k:v for k,v in metrics.items() if k!='host'} }")
        return metrics
    except Exception as e:
        logger.error(f"{server.host} 采集异常: {e}")
        return None

def collect_all_metrics(config: MonitorConfig) -> List[Dict]:
    """多线程批量采集，返回所有成功的数据字典列表"""
    results = []
    with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        future_to_server = {
            executor.submit(collect_single_server, server, config.metrics_commands): server
            for server in config.servers
        }
        for future in as_completed(future_to_server):
            server = future_to_server[future]
            try:
                data = future.result()
                if data:
                    results.append(data)
            except Exception as e:
                logger.error(f"{server.host} 线程异常: {e}")
    return results