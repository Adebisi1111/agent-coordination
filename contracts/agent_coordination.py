# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from genlayer import *


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


@gl.evm.contract_interface
class _Recipient:
    class View:
        pass

    class Write:
        pass


class AgentCoordination(gl.Contract):
    agents: TreeMap[str, Agent]
    tasks: TreeMap[str, Task]
    task_count: u256
    min_stake: u256 = u256(1000000000000000)  # 0.001 GEN for testing

    def __init__(self):
        pass

    @gl.public.write.payable
    def registerAgent(self, capabilities: str, did_hash: str = "") -> None:
        sender = gl.message.sender_address.as_hex
        if gl.message.value < self.min_stake:
            raise gl.vm.UserError("Stake below minimum")
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
    def approveDelivery(self, task_id: str) -> None:
        """Approve delivery and pay agent."""
        task = self.tasks.get(task_id, None)
        if task is None:
            raise gl.vm.UserError("Task not found")
        if task.status != "DELIVERED":
            raise gl.vm.UserError("No delivery to approve")
        
        task.status = "VERIFIED"
        task.verification = "PASS"
        agent = self.agents.get(task.assignee, None)
        if agent is not None:
            agent.reputation += u256(1)
            self.agents[task.assignee] = agent
        # Use _Recipient.emit_transfer() for contract-to-EOA transfer
        _Recipient(Address(task.assignee)).emit_transfer(value=u256(int(task.reward)))
        self.tasks[task_id] = task

    @gl.public.write
    def rejectDelivery(self, task_id: str) -> None:
        """Reject delivery and mark as disputed."""
        task = self.tasks.get(task_id, None)
        if task is None:
            raise gl.vm.UserError("Task not found")
        if task.status != "DELIVERED":
            raise gl.vm.UserError("No delivery to reject")
        task.status = "DISPUTED"
        task.verification = "FAIL"
        self.tasks[task_id] = task

    @gl.public.write
    def resolveDispute(self, task_id: str) -> None:
        """Resolve dispute and refund poster."""
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
        # Use _Recipient.emit_transfer() for contract-to-EOA transfer
        _Recipient(Address(task.poster)).emit_transfer(value=u256(int(task.reward)))

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
        # Use _Recipient.emit_transfer() for contract-to-EOA transfer
        _Recipient(Address(task.poster)).emit_transfer(value=u256(int(task.reward)))

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
