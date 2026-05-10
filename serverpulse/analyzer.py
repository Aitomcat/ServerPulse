import pandas as pd
import logging
from typing import List, Dict, Any
from .config import MonitorConfig

logger = logging.getLogger(__name__)

def analyze_data(data: List[Dict], config: MonitorConfig) -> (pd.DataFrame, List[Dict]):
    """
    分析采集数据，返回 DataFrame 和异常列表
    """
    if not data:
        return pd.DataFrame(), []

    df = pd.DataFrame(data)
    # 计算仅数值列的平均值
    metric_cols = [m for m in config.metrics_commands.keys() if m in df.columns]
    if metric_cols:
        means = df[metric_cols].mean()
        logger.info("全平台均值:")
        for m, v in means.items():
            logger.info(f"  {m}: {v:.2f}%")

    anomalies = []
    for _, row in df.iterrows():
        host = row["host"]
        for metric in metric_cols:
            threshold = config.thresholds.get(metric)
            if threshold is not None and row[metric] > threshold:
                anomaly = {
                    "host": host,
                    "metric": metric,
                    "value": row[metric],
                    "threshold": threshold,
                    "tags": {k: row[k] for k in row.index if k not in ("host", "cpu", "memory", "disk")}
                }
                anomalies.append(anomaly)
                logger.warning(f"异常: {host} {metric} {row[metric]:.2f}% > {threshold}%")
    return df, anomalies