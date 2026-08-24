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


class AgentCoordination(gl.Contract):
    agents: TreeMap[str, Agent]
    tasks: TreeMap[str, Task]
    task_count: u256
    min_stake: u256 = u256(1000000000000000000)  # 1 GEN

    def __init__(self):
        pass

    @gl.public.write.payable
    def register_agent(self, capabilities: str) -> None:
        """Register as an agent with capabilities (comma-separated)."""
        sender = gl.message.sender_address.as_hex
        if gl.message.value < self.min_stake:
            raise Exception("Stake below minimum (1 GEN)")
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
    def post_task(self, description: str) -> str:
        """Post a task with reward (value sent)."""
        if gl.message.value <= u256(0):
            raise Exception("Reward must be > 0")
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
    def claim_task(self, task_id: str) -> None:
        """Claim a task. Only verified agents can claim."""
        sender = gl.message.sender_address.as_hex
        agent = self.agents.get(sender, None)
        if agent is None or not agent.active:
            raise Exception("Not a registered agent")
        task = self.tasks.get(task_id, None)
        if task is None:
            raise Exception("Task not found")
        if task.status != "OPEN":
            raise Exception("Task not open")
        task.status = "ASSIGNED"
        task.assignee = sender
        self.tasks[task_id] = task

    @gl.public.write
    def submit_delivery(self, task_id: str, delivery_url: str) -> None:
        """Submit delivery for an assigned task."""
        sender = gl.message.sender_address.as_hex
        task = self.tasks.get(task_id, None)
        if task is None:
            raise Exception("Task not found")
        if task.assignee != sender:
            raise Exception("Not assigned to this task")
        if task.status != "ASSIGNED":
            raise Exception("Task not assigned")
        task.delivery_url = delivery_url
        task.status = "DELIVERED"
        self.tasks[task_id] = task

    @gl.public.write
    def verify_delivery(self, task_id: str) -> None:
        """Verify a delivery via consensus. Checks if deliverable exists and matches task."""
        task = self.tasks.get(task_id, None)
        if task is None:
            raise Exception("Task not found")
        if task.status != "DELIVERED":
            raise Exception("No delivery to verify")

        ALLOWED = ("PASS", "FAIL")

        def leader() -> dict:
            try:
                content = gl.nondet.web.render(task.delivery_url, mode="text")
            except Exception:
                content = "(could not fetch)"
            prompt = (
                f"Task: {task.description}\n"
                f"Delivery content from {task.delivery_url}:\n\n{content[:2000]}\n\n"
                f"Does this delivery fulfill the task? Respond as JSON: "
                f'{{"verdict": "PASS"|"FAIL", "reason": "..."}}'
            )
            res = gl.nondet.exec_prompt(prompt, response_format="json")
            verdict = (res.get("verdict") or "").strip().upper()
            return {"verdict": verdict if verdict in ALLOWED else "FAIL"}

        def validator(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            return leader()["verdict"] == leader_result.calldata["verdict"]

        result = gl.vm.run_nondet_unsafe(leader, validator)
        task.verification = result["verdict"]

        if result["verdict"] == "PASS":
            task.status = "VERIFIED"
            # Pay agent
            agent = self.agents.get(task.assignee, None)
            if agent is not None:
                agent.reputation += u256(1)
                self.agents[task.assignee] = agent
        else:
            task.status = "DISPUTED"

        self.tasks[task_id] = task

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
        })

    @gl.public.view
    def get_agent(self, addr: Address) -> str:
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
