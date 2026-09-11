# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from genlayer import *


# Multi-Agent Coordination System v6
#
# Withdrawal pattern: contract holds funds in escrow, users withdraw.
# This ensures REAL balance changes on Bradbury testnet.


@allow_storage
@dataclass
class Agent:
    owner: str
    capabilities: str
    stake: u256
    reputation: u256
    active: bool
    did_hash: str


@allow_storage
@dataclass
class Task:
    poster: str
    description: str
    reward: u256
    status: str
    assignee: str
    delivery_url: str
    verification: str
    technocore_room: str


class AgentCoordination(gl.Contract):
    agents: TreeMap[str, Agent]
    tasks: TreeMap[str, Task]
    task_count: u256
    min_stake: u256 = u256(1000000000000000000)  # 1 GEN
    
    # Withdrawal pattern: track withdrawable balances
    _withdrawable: TreeMap[str, u256]
    
    # Track emitted transfers for verification
    _emitted_transfers: TreeMap[str, str]
    _external_transfer_log: TreeMap[str, str]

    def __init__(self):
        pass

    def _withdraw(self, addr: str) -> u256:
        """Withdraw all available funds for an address."""
        amount = self._withdrawable.get(addr, u256(0))
        if amount > u256(0):
            self._withdrawable[addr] = u256(0)
        return amount

    @gl.public.write.payable
    def registerAgent(self, capabilities: str, did_hash: str = "") -> None:
        sender = gl.message.sender_address.as_hex
        if gl.message.value < self.min_stake:
            raise gl.vm.UserError("Stake below minimum (1 GEN)")
        existing = self.agents.get(sender, None)
        if existing is None:
            self.agents[sender] = Agent(
                owner=sender,
                capabilities=capabilities,
                stake=gl.message.value,
                reputation=u256(0),
                active=True,
                did_hash=did_hash,
            )
        else:
            existing.stake += gl.message.value
            existing.capabilities = capabilities
            existing.active = True
            if did_hash:
                existing.did_hash = did_hash
            self.agents[sender] = existing

    @gl.public.write.payable
    def postTask(self, description: str, technocore_room: str = "") -> str:
        if gl.message.value <= u256(0):
            raise gl.vm.UserError("Reward must be > 0")
        task_id = f"task-{self.task_count + u256(1)}"
        self.tasks[task_id] = Task(
            poster=gl.message.sender_address.as_hex,
            description=description,
            reward=gl.message.value,
            status="OPEN",
            assignee="",
            delivery_url="",
            verification="PENDING",
            technocore_room=technocore_room,
        )
        self.task_count += u256(1)
        return task_id

    @gl.public.write
    def claimTask(self, task_id: str) -> None:
        sender = gl.message.sender_address.as_hex
        agent = self.agents.get(sender, None)
        if agent is None or not agent.active:
            raise gl.vm.UserError("Not a registered agent")
        task = self.tasks.get(task_id, None)
        if task is None:
            raise gl.vm.UserError("Task not found")
        if task.status != "OPEN":
            raise gl.vm.UserError("Task not open")
        task.status = "ASSIGNED"
        task.assignee = sender
        self.tasks[task_id] = task

    @gl.public.write
    def submitDelivery(self, task_id: str, delivery_url: str) -> None:
        sender = gl.message.sender_address.as_hex
        task = self.tasks.get(task_id, None)
        if task is None:
            raise gl.vm.UserError("Task not found")
        if task.assignee != sender:
            raise gl.vm.UserError("Not assigned to this task")
        if task.status not in ("ASSIGNED", "DELIVERED"):
            raise gl.vm.UserError("Task not assigned")
        task.delivery_url = delivery_url
        task.status = "DELIVERED"
        task.verification = "PENDING"
        self.tasks[task_id] = task

    @gl.public.write
    def verifyDelivery(self, task_id: str) -> None:
        task = self.tasks.get(task_id, None)
        if task is None:
            raise gl.vm.UserError("Task not found")
        if task.status != "DELIVERED":
            raise gl.vm.UserError("No delivery to verify")
        if task.verification == "IN_PROGRESS":
            raise gl.vm.UserError("Verification already in progress")

        task.verification = "IN_PROGRESS"
        self.tasks[task_id] = task

        ALLOWED = ("PASS", "FAIL")

        def work() -> dict:
            try:
                content = gl.nondet.web.render(task.delivery_url, mode="text")
            except Exception:
                raise gl.vm.UserError("EVIDENCE_UNREACHABLE")
            if not content:
                return {"verdict": "FAIL"}
            prompt = (
                f"Task: {task.description}\n"
                f"Delivery content from {task.delivery_url}:\n\n{content[:6000]}\n\n"
                f"Does this delivery fulfill the task? Respond as JSON: "
                f'{{"verdict": "PASS"|"FAIL", "reason": "..."}}'
            )
            res = gl.nondet.exec_prompt(prompt, response_format="json")
            verdict = (res.get("verdict") or "").strip().upper()
            if verdict not in ALLOWED:
                raise gl.vm.UserError("MALFORMED_DECISION")
            return {"verdict": verdict}

        def validator(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                leader_msg = getattr(leaders_res, "message", "")
                try:
                    work()
                    return False
                except gl.vm.UserError as e:
                    return str(e.message) == str(leader_msg)
                except Exception:
                    return False
            try:
                mine = work()
            except Exception:
                return False
            return mine["verdict"] == leaders_res.calldata["verdict"]

        try:
            result = gl.vm.run_nondet_unsafe(work, validator)
        except gl.vm.UserError as e:
            raise gl.vm.UserError(f"Verification failed: {e.message}")

        task.verdict = result["verdict"]

        if result["verdict"] == "PASS":
            task.status = "VERIFIED"
            agent = self.agents.get(task.assignee, None)
            if agent is not None:
                agent.reputation += u256(1)
                self.agents[task.assignee] = agent
            # Credit agent's withdrawable balance
            current = self._withdrawable.get(task.assignee, u256(0))
            self._withdrawable[task.assignee] = current + task.reward
            # Log the transfer
            transfer_id = f"payout-{task_id}"
            self._emitted_transfers[transfer_id] = json.dumps({
                "to": task.assignee, "amount": int(task.reward), "type": "payout"
            })
            self._external_transfer_log[transfer_id] = json.dumps({
                "to": task.assignee, "amount": int(task.reward), "type": "payout",
                "status": "credited"
            })
        else:
            task.status = "DISPUTED"

        self.tasks[task_id] = task

    @gl.public.write
    def resolveDispute(self, task_id: str) -> None:
        task = self.tasks.get(task_id, None)
        if task is None:
            raise gl.vm.UserError("Task not found")
        if task.status != "DISPUTED":
            raise gl.vm.UserError("Task is not disputed")
        sender = gl.message.sender_address.as_hex
        if sender != task.poster:
            raise gl.vm.UserError("Only the poster can resolve a dispute")

        task.status = "REFUNDED"
        self.tasks[task_id] = task
        # Credit poster's withdrawable balance
        current = self._withdrawable.get(task.poster, u256(0))
        self._withdrawable[task.poster] = current + task.reward
        # Log the transfer
        transfer_id = f"refund-{task_id}"
        self._emitted_transfers[transfer_id] = json.dumps({
            "to": task.poster, "amount": int(task.reward), "type": "refund"
        })
        self._external_transfer_log[transfer_id] = json.dumps({
            "to": task.poster, "amount": int(task.reward), "type": "refund",
            "status": "credited"
        })

    @gl.public.write
    def cancelTask(self, task_id: str) -> None:
        task = self.tasks.get(task_id, None)
        if task is None:
            raise gl.vm.UserError("Task not found")
        if task.status not in ("OPEN", "ASSIGNED"):
            raise gl.vm.UserError("Only open or assigned tasks can be cancelled")
        sender = gl.message.sender_address.as_hex
        if sender != task.poster:
            raise gl.vm.UserError("Only the poster can cancel")
        task.status = "CANCELLED"
        self.tasks[task_id] = task
        # Credit poster's withdrawable balance
        current = self._withdrawable.get(task.poster, u256(0))
        self._withdrawable[task.poster] = current + task.reward
        # Log the transfer
        transfer_id = f"cancel-{task_id}"
        self._emitted_transfers[transfer_id] = json.dumps({
            "to": task.poster, "amount": int(task.reward), "type": "cancel_refund"
        })
        self._external_transfer_log[transfer_id] = json.dumps({
            "to": task.poster, "amount": int(task.reward), "type": "cancel_refund",
            "status": "credited"
        })

    @gl.public.write
    def withdraw(self) -> u256:
        """Withdraw all available funds."""
        sender = gl.message.sender_address.as_hex
        amount = self._withdrawable.get(sender, u256(0))
        if amount <= u256(0):
            return u256(0)
        self._withdrawable[sender] = u256(0)
        # Transfer the funds
        payable_addr = Address(sender)
        payable_addr.transfer(amount)
        return amount

    @gl.public.view
    def getWithdrawable(self, addr: str) -> str:
        """Get withdrawable balance for an address."""
        return str(int(self._withdrawable.get(addr, u256(0))))

    @gl.public.view
    def getClaimCount(self) -> str:
        return json.dumps({"count": int(self.task_count)})

    @gl.public.view
    def getTask(self, task_id: str) -> str:
        t = self.tasks.get(task_id, None)
        if t is None:
            return json.dumps({"exists": False})
        return json.dumps({
            "exists": True,
            "description": t.description,
            "reward": int(t.reward),
            "status": t.status,
            "assignee": t.assignee,
            "verification": t.verification,
            "poster": t.poster,
            "technocore_room": t.technocore_room,
        })

    @gl.public.view
    def getAgent(self, addr: Address) -> str:
        agent_hex = Address(addr).as_hex
        a = self.agents.get(agent_hex, None)
        if a is None:
            return json.dumps({"exists": False})
        return json.dumps({
            "exists": True,
            "capabilities": a.capabilities,
            "stake": int(a.stake),
            "reputation": int(a.reputation),
            "active": a.active,
            "did_hash": a.did_hash,
        })

    @gl.public.view
    def getEmittedTransfers(self) -> str:
        result = {}
        for k in self._emitted_transfers.keys():
            result[k] = self._emitted_transfers[k]
        return json.dumps(result)

    @gl.public.view
    def getExternalTransferLog(self) -> str:
        result = {}
        for k in self._external_transfer_log.keys():
            result[k] = self._external_transfer_log[k]
        return json.dumps(result)
