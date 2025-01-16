# Couple of custom exceptions


class UploadFailed(Exception):
    pass

class CommandRequiresAdmin(Exception):
    pass


class CommandRequiresOwner(Exception):
    pass


