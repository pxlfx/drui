import typing as t


class STATUSES:
    """
    Helper class for metrics worker.
    Holds metrics worker statuses.
    """
    in_progress = 'in progress'
    completed = 'completed'
    error = 'error'


class Tag:
    """
    Helper class for metrics worker.
    Holds metadata for a tag.
    """

    def __init__(self):
        self.digest: str = ''
        self.image: str = ''
        self.tag: str = ''
        self.os: str = ''
        self.arch: str = ''
        self.created: str = ''
        self.layers: t.Dict = {}
