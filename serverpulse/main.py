import argparse
import logging
import sys
from .config import load_config
from .collector import collect_all_metrics
from .analyzer import analyze_data
from .alerter import get_alerters

def setup_logging(log_file: str = "serverpulse.log", verbose: bool = False):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if verbose else logging.INFO)
    ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(ch)

def main():
    parser = argparse.ArgumentParser(description="ServerPulse - 服务器资源监控与告警")
    parser.add_argument("-c", "--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"加载配置失败: {e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(config.log_file, args.verbose)
    logger = logging.getLogger(__name__)
    logger.info("===== ServerPulse 开始运行 =====")

    # 采集
    data = collect_all_metrics(config)
    if not data:
        logger.warning("无数据采集成功，退出")
        sys.exit(0)

    # 分析
    df, anomalies = analyze_data(data, config)
    logger.info(f"采集完成，成功 {len(data)} 台，异常 {len(anomalies)} 项")
    # 保存 CSV
    df.to_csv("serverpulse_result.csv", index=False)
    logger.info("结果已保存至 serverpulse_result.csv")

    # 告警
    if anomalies:
        alerters = get_alerters(config.alert_channels, config.alert_config)
        for alerter in alerters:
            alerter.send(anomalies)
    else:
        logger.info("所有指标正常，无需告警")

if __name__ == "__main__":
    main()