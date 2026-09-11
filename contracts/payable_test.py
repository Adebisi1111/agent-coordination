# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


class PayableTest(gl.Contract):
    _balance: u256

    def __init__(self):
        pass

    @gl.public.write.payable
    def deposit(self) -> None:
        self._balance += gl.message.value

    @gl.public.view
    def getBalance(self) -> str:
        return str(int(self._balance))
