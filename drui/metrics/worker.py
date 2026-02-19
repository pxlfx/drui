from os import getppid
from os import kill
from time import sleep
from time import time

from drui.common.config import ConfigParser
from drui.common.process import pid_exists
from drui.metrics import Metrics
from drui.metrics import STATUSES


def run(conf: ConfigParser) -> None:
    """
    Collect registry metrics.

    :param conf: config instance
    """
    parent_pid = getppid()

    metrics = Metrics(conf, recreate_on_mismatch=True)
    interval = conf.getint('interval', section='metrics', default=60) * 60
    error_count = 0

    while True:
        if not pid_exists(parent_pid):
            exit(0)

        try:
            stats = metrics.stats()
            if stats:
                timestamp = float(stats.get('timestamp', 0))
                status = stats.get('status')
                seconds = time() - timestamp
                diff = interval - seconds

                if status == STATUSES.completed:
                    sleep(diff if diff >= 0 else 0)
                elif STATUSES.error:
                    error_count += 1
                    if error_count >= 3:
                        exit(2)
                sleep(60)
        except KeyboardInterrupt:
            exit(1)

        metrics.run()
