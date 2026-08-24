import json


def _hex(addr):
    if isinstance(addr, bytes):
        return "0x" + addr.hex()
    return str(addr)


def test_register_agent(direct_vm, direct_deploy, direct_alice):
    """Agent registers with stake."""
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.register_agent("writing,coding,research")
    out = json.loads(contract.get_agent(direct_alice))
    assert out["exists"] is True
    assert out["stake"] == 2000000000000000000
    assert out["reputation"] == 0
    assert out["active"] is True


def test_post_task(direct_vm, direct_deploy, direct_bob):
    """Post a task with reward."""
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.post_task("Write a blog post about AI safety")
    out = json.loads(contract.get_task(task_id))
    assert out["exists"] is True
    assert out["reward"] == 500000000000000000
    assert out["status"] == "OPEN"


def test_claim_and_deliver(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Agent claims task and submits delivery."""
    contract = direct_deploy("contracts/agent_coordination.py")
    # Register agent
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.register_agent("writing")
    # Post task
    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.post_task("Write a blog post")
    # Claim
    direct_vm.sender = direct_alice
    contract.claim_task(task_id)
    out = json.loads(contract.get_task(task_id))
    assert out["status"] == "ASSIGNED"
    assert out["assignee"].lower() == _hex(direct_alice).lower()
    # Submit delivery
    contract.submit_delivery(task_id, "https://example.com/delivery")
    out = json.loads(contract.get_task(task_id))
    assert out["status"] == "DELIVERED"


def test_verify_delivery_pass(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Delivery verified as PASS, agent reputation increases."""
    contract = direct_deploy("contracts/agent_coordination.py")
    # Register
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.register_agent("writing")
    # Post + claim + deliver
    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.post_task("Write about AI")
    direct_vm.sender = direct_alice
    contract.claim_task(task_id)
    contract.submit_delivery(task_id, "https://example.com/ai-blog")
    # Mock consensus
    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "AI is transformative..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "PASS", "reason": "fulfills task"}))
    contract.verify_delivery(task_id)
    out = json.loads(contract.get_task(task_id))
    assert out["status"] == "VERIFIED"
    out = json.loads(contract.get_agent(direct_alice))
    assert out["reputation"] == 1


def test_verify_delivery_fail(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Delivery verified as FAIL, status becomes DISPUTED."""
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.register_agent("writing")
    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.post_task("Write about AI")
    direct_vm.sender = direct_alice
    contract.claim_task(task_id)
    contract.submit_delivery(task_id, "https://example.com/off-topic")
    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "Cooking recipes..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "FAIL", "reason": "off topic"}))
    contract.verify_delivery(task_id)
    out = json.loads(contract.get_task(task_id))
    assert out["status"] == "DISPUTED"


def test_unauthorized_claim_fails(direct_vm, direct_deploy, direct_alice, direct_charlie):
    """Unregistered agent cannot claim."""
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.register_agent("writing")
    direct_vm.sender = direct_alice
    direct_vm.value = 500000000000000000
    task_id = contract.post_task("Task")
    direct_vm.sender = direct_charlie
    try:
        contract.claim_task(task_id)
        raise AssertionError("expected revert")
    except Exception as e:
        assert "Not a registered agent" in str(e)
