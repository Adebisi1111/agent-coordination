# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
from dataclasses import dataclass
from genlayer import *


# Multi-Agent Coordination System
#
# Agents coordinate work through GenLayer consensus. Tasks are posted,
# agents claim them, consensus verifies delivery, payments are escrowed.
#
# Consensus angles:
#   - Task assignment: consensus picks best agent among claimants
#   - Delivery verification: validators independently check quality
#   - Dispute resolution: agents dispute verdicts, consensus rules


@allow_storage
@dataclass
class Agent:
    owner: str
    capabilities: str     # comma-separated
    stake: u256
    reputation: u256      # score from successful deliveries
    active: bool


@allow_storage
@dataclass
class Task:
    poster: str
    description: str
    reward: u256
    status: str           # "OPEN" | "ASSIGNED" | "DELIVERED" | "VERIFIED" | "DISPUTED"
    assignee: str
    delivery_url: str
    verification: str     # "PENDING" | "PASS" | "FAIL"


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

    def __init__(self):
        pass

    @gl.public.write.payable
    def registerAgent(self, capabilities: str) -> None:
        """Register as an agent with capabilities (comma-separated)."""
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
        """Post a task with reward (value sent)."""
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
        return task_id

    @gl.public.write
    def claimTask(self, task_id: str) -> None:
        """Claim a task. Only verified agents can claim."""
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
        """Submit or resubmit delivery for an assigned task."""
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
    def cancelTask(self, task_id: str) -> None:
        """Cancel an unclaimed task and refund the poster.

        Escape hatch so a reward is not permanently locked when no agent
        ever claims or the assigned agent abandons the task.
        """
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
        _Payee(Address(task.poster)).emit_transfer(
            value=u256(int(task.reward)), on="finalized"
        )

    @gl.public.write
    def verifyDelivery(self, task_id: str) -> None:
        """Verify a delivery via consensus and settle the escrow.

        PASS → agent is paid the reward and earns a reputation point.
        FAIL → task is DISPUTED; poster can reclaim the reward via resolveDispute().
        """
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
                # Transient fetch failure: treat as unverifiable, not a pass.
                raise gl.vm.UserError("EVIDENCE_UNREACHABLE")
            if not content:
                # An unreadable source proves nothing.
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
            # Error classification per Error Handling docs: agree only when
            # we reproduce the same deterministic outcome as the leader.
            if not isinstance(leaders_res, gl.vm.Return):
                leader_msg = getattr(leaders_res, "message", "")
                try:
                    work()
                    return False            # leader errored, we succeeded
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
            # Pay the agent the escrowed reward. Paying an EOA is an EXTERNAL
            # message, so it routes through the EVM interface contract.
            _Payee(Address(task.assignee)).emit_transfer(
                value=u256(int(task.reward)), on="finalized"
            )
        else:
            task.status = "DISPUTED"

        self.tasks[task_id] = task

    @gl.public.write
    def resolveDispute(self, task_id: str) -> None:
        """Refund the poster when a task is disputed.

        Defines the reward-resolution path so a disputed task does not leave
        the reward permanently locked in the contract. Only the original poster
        may reclaim, and only from the DISPUTED state.
        """
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
