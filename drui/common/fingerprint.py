"""
Generate a deterministic or fallback machine fingerprint for identifying hosts.
"""

import secrets
import typing as t
from hashlib import sha256
from pathlib import Path


class Fingerprint:
    """
    Provide a machine fingerprint based on available system identifiers.

    The fingerprint is derived from the first available source in the following
    order of preference:
      1. /etc/machine-id (standard Linux / container ID)
      2. /proc/sys/kernel/random/boot_id (container fallback)
      3. MachineGuid from Windows registry
      4. Random token (non-deterministic)

    The result is always returned as a SHA-256 hex digest.

    Example:
        >>> fingerprint = Fingerprint()
        >>> fingerprint.hex
    """

    def __init__(self, hex_value: t.Optional[str] = None):
        """
        Initialize the Fingerprint instance.

        :param hex_value: an optional hex string to use as the fingerprint
        """
        self.hex_value = hex_value

    @staticmethod
    def hexdigest(value: str) -> str:
        """
        Hash a string using SHA-256.

        :param value: the string to hash
        :return: a hex string representing the SHA-256 hash of the input
        """
        return sha256(value.encode()).hexdigest()

    @property
    def hex(self) -> str:
        """
        Resolve the machine fingerprint by probing system sources.

        If a hex string was provided during initialization,
        it is returned immediately.

        :return:a hex string representing the machine fingerprint
        """
        # explicit hex string from initialization
        if self.hex_value:
            if len(self.hex_value) == 64 and all(
                c in '0123456789abcdef' for c in self.hex_value.lower()
            ):
                return self.hex_value
            return self.hexdigest(self.hex_value)

        # 1. /etc/machine-id (standard Linux / container ID)
        machine_id_path = Path('/etc/machine-id')
        if machine_id_path.is_file():
            try:
                machine_id = machine_id_path.read_text(encoding='utf-8').strip()
                if machine_id:
                    return self.hexdigest(machine_id)
            except OSError:
                pass

        # 2. /proc/sys/kernel/random/boot_id (container fallback)
        boot_id_path = Path('/proc/sys/kernel/random/boot_id')
        if boot_id_path.is_file():
            try:
                boot_id = boot_id_path.read_text(encoding='utf-8').strip()
                if boot_id:
                    return self.hexdigest(boot_id)
            except OSError:
                pass

        # 3. MachineGuid from Windows registry
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\Microsoft\Cryptography',
            )
            try:
                machine_guid, _ = winreg.QueryValueEx(key, 'MachineGuid')
                if machine_guid:
                    return self.hexdigest(machine_guid)
            finally:
                winreg.CloseKey(key)
        except (ImportError, OSError):
            pass

        # 4. Fallback — random key (non-deterministic)
        return self.hexdigest(secrets.token_hex(16))
