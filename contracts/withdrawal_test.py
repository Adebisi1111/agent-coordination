# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


class WithdrawalTest(gl.Contract):
    _withdrawable: TreeMap[str, u256]

    def __init__(self):
        pass

    @gl.public.write.payable
    def deposit(self) -> None:
        sender = gl.message.sender_address.as_hex
        current = self._withdrawable.get(sender, u256(0))
        self._withdrawable[sender] = current + gl.message.value

    @gl.public.write
    def withdraw(self) -> u256:
        sender = gl.message.sender_address.as_hex
        amount = self._withdrawable.get(sender, u256(0))
        if amount <= u256(0):
            return u256(0)
        self._withdrawable[sender] = u256(0)
        Address(sender).transfer(amount)
        return amount

    @gl.public.view
    def getWithdrawable(self, addr: str) -> str:
        return str(int(self._withdrawable.get(addr, u256(0))))
