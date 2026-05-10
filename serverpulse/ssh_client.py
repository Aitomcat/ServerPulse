import paramiko
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SSHClient:
    """封装 paramiko SSH 连接，支持密钥和密码"""
    def __init__(self, host: str, port: int, user: str, password: str = None, key_file: str = None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.key_file = key_file
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self, timeout=10):
        try:
            if self.key_file:
                self._client.connect(hostname=self.host, port=self.port, username=self.user,
                                     key_filename=self.key_file, timeout=timeout)
            else:
                self._client.connect(hostname=self.host, port=self.port, username=self.user,
                                     password=self.password, timeout=timeout)
            logger.debug(f"SSH connected to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"SSH connection failed to {self.host}: {e}")
            raise

    def exec_command(self, command: str, timeout=10) -> Optional[str]:
        """执行命令并返回标准输出字符串，失败返回 None"""
        try:
            _, stdout, stderr = self._client.exec_command(command, timeout=timeout)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                logger.error(f"Command failed on {self.host}: {stderr.read().decode()}")
                return None
            return stdout.read().decode().strip()
        except Exception as e:
            logger.error(f"Command execution error on {self.host}: {e}")
            return None

    def close(self):
        self._client.close()
        logger.debug(f"SSH connection to {self.host} closed")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()