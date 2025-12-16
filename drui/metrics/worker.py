from datetime import datetime
from os import getppid
from os import kill
from time import sleep

from drui.common.config import ConfigParser
from drui.metrics import Metrics
from drui.metrics import STATUSES


def run(conf: ConfigParser) -> None:
    """
    Collect registry metrics.

    :param conf: config instance
    """
    parent_pid = getppid()

    metrics = Metrics(conf)
    interval = 3600
    error_count = 0

    while True:
        try:
            kill(parent_pid, 0)
        except OSError:
            exit(0)

        stats = metrics.stats()
        if stats:
            timestamp = datetime.fromisoformat(stats.get('timestamp'))
            status = stats.get('status')
            seconds = (datetime.now() - timestamp).total_seconds()
            diff = interval - seconds

            if status == STATUSES.completed:
                sleep(diff if diff >= 0 else 0)
            elif STATUSES.error:
                error_count += 1
                if error_count >= 3:
                    exit(2)
                sleep(60)

        metrics.run()
