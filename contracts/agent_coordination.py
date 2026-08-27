# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from genlayer import *


# Multi-Agent Coordination System
#
# Agents coordinate work through GenLayer consensus. Tasks are posted,
# agents claim them, consensus verifies delivery, payments are escrowed.


@allow_storage
@dataclass
class Agent:
    owner: str
    capabilities: str
    stake: u256
    reputation: u256
    active: bool


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


@gl.evm.contract_interface
class _Payee:
    class View:
        pass

    class Write:
        pass


class AgentCoordination(gl.Contract):
    agents: TreeMap[str, Agent]
    tasks: TreeMap[str, Task]
    task_count: u256
    min_stake: u256 = u256(1000000000000000000)  # 1 GEN
    # Track emitted external transfers for verification.
    _emitted_transfers: TreeMap[str, str]
    # Track expected balance changes since direct mode doesn't move real funds.
    _expected_balances: TreeMap[str, i256]

    def __init__(self):
        pass

    def _adjust_balance(self, addr: str, delta: int) -> None:
        """Record an expected balance change for verification."""
        current = int(self._expected_balances.get(addr, i256(0)))
        self._expected_balances[addr] = i256(current + delta)

    @gl.public.view
    def getExpectedBalance(self, addr: str) -> str:
        """Read the expected balance change for an address."""
        return str(int(self._expected_balances.get(addr, i256(0))))

    @gl.public.write.payable
    def registerAgent(self, capabilities: str) -> None:
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
            )
        else:
            existing.stake += gl.message.value
            existing.capabilities = capabilities
            existing.active = True
            self.agents[sender] = existing

    @gl.public.write.payable
    def postTask(self, description: str) -> str:
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
        )
        self.task_count += u256(1)
        # The poster locks the reward into escrow
        self._adjust_balance(gl.message.sender_address.as_hex, -int(gl.message.value))
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

        task.verification = result["verdict"]

        if result["verdict"] == "PASS":
            task.status = "VERIFIED"
            agent = self.agents.get(task.assignee, None)
            if agent is not None:
                agent.reputation += u256(1)
                self.agents[task.assignee] = agent
            # Pay the agent the escrowed reward via external message
            self._adjust_balance(task.assignee, int(task.reward))
            transfer_id = f"payout-{task_id}"
            self._emitted_transfers[transfer_id] = json.dumps({
                "to": task.assignee, "amount": int(task.reward), "type": "payout"
            })
            _Payee(Address(task.assignee)).emit_transfer(
                value=u256(int(task.reward)), on="finalized"
            )
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
        self._adjust_balance(task.poster, int(task.reward))
        transfer_id = f"refund-{task_id}"
        self._emitted_transfers[transfer_id] = json.dumps({
            "to": task.poster, "amount": int(task.reward), "type": "refund"
        })
        _Payee(Address(task.poster)).emit_transfer(
            value=u256(int(task.reward)), on="finalized"
        )

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
        self._adjust_balance(task.poster, int(task.reward))
        transfer_id = f"cancel-{task_id}"
        self._emitted_transfers[transfer_id] = json.dumps({
            "to": task.poster, "amount": int(task.reward), "type": "cancel_refund"
        })
        _Payee(Address(task.poster)).emit_transfer(
            value=u256(int(task.reward)), on="finalized"
        )

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
        })

    @gl.public.view
    def getEmittedTransfers(self) -> str:
        """Return all emitted external transfers for verification."""
        result = {}
        for k in self._emitted_transfers.keys():
            result[k] = self._emitted_transfers[k]
        return json.dumps(result)
