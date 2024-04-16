
class InvalidInputException(Exception):

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(f'Invalid {self.message}')


class InvalidKeyboardException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(f'Invalid keyboard used: {self.message}')

