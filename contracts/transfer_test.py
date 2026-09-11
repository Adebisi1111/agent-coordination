# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


class TransferTest(gl.Contract):
    _balance: u256

    def __init__(self):
        pass

    @gl.public.write.payable
    def deposit(self) -> u256:
        self._balance += gl.message.value
        return self._balance

    @gl.public.write
    def withdraw(self) -> u256:
        sender = gl.message.sender_address.as_hex
        amount = self._balance
        if amount <= u256(0):
            return u256(0)
        self._balance = u256(0)
        Address(sender).transfer(amount)
        return amount

    @gl.public.view
    def getBalance(self) -> str:
        return str(int(self._balance))
