class DownburstError(Exception):
    """
    Unknown Downburst error
    """

    def __str__(self):
        doc = self.__doc__.strip()
        return ': '.join([doc] + [str(a) for a in self.args])


class LibvirtConnectionError(DownburstError):
    """
    Cannot connect to libvirt
    """


class VMExistsError(DownburstError):
    """
    Virtual machine with this name exists already
    """


class ImageHashMismatchError(DownburstError):
    """
    Image SHA-512 did not match
    """
