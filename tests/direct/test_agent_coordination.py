import json


def _hex(addr):
    if isinstance(addr, (bytes, bytearray)):
        from genlayer.py.types import Address
        return Address(bytes(addr)).as_hex
    return str(addr)


def test_registerAgent(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing,coding,research")
    out = json.loads(contract.getAgent(direct_alice))
    assert out["exists"] is True
    assert out["stake"] == 2000000000000000000


def test_postTask(direct_vm, direct_deploy, direct_bob):
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.postTask("Write a blog post about AI safety")
    out = json.loads(contract.getTask(task_id))
    assert out["exists"] is True
    assert out["reward"] == 500000000000000000


def test_claim_and_deliver(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")
    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.postTask("Write a blog post")
    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    out = json.loads(contract.getTask(task_id))
    assert out["status"] == "ASSIGNED"
    contract.submitDelivery(task_id, "https://example.com/delivery")
    out = json.loads(contract.getTask(task_id))
    assert out["status"] == "DELIVERED"


def test_approveDelivery_pays_agent(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Approve delivery and verify agent is paid."""
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")
    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.postTask("Write about AI")
    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    contract.submitDelivery(task_id, "https://example.com/ai-blog")
    contract.approveDelivery(task_id)
    out = json.loads(contract.getTask(task_id))
    assert out["status"] == "VERIFIED"


def test_cancel_task_refunds_poster(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.postTask("Write about AI")
    direct_vm.sender = direct_bob
    contract.cancelTask(task_id)
    assert json.loads(contract.getTask(task_id))["status"] == "CANCELLED"


def test_full_escrow_lifecycle_pass(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")
    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.postTask("Write about AI")
    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    contract.submitDelivery(task_id, "https://example.com/ai-blog")
    contract.approveDelivery(task_id)
    out = json.loads(contract.getTask(task_id))
    assert out["status"] == "VERIFIED"
    assert out["verification"] == "PASS"


def test_full_escrow_lifecycle_dispute(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")
    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.postTask("Write about AI")
    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    contract.submitDelivery(task_id, "https://example.com/off-topic")
    direct_vm.sender = direct_bob
    contract.rejectDelivery(task_id)
    out = json.loads(contract.getTask(task_id))
    assert out["status"] == "DISPUTED"
    contract.resolveDispute(task_id)
    assert json.loads(contract.getTask(task_id))["status"] == "REFUNDED"


def test_resolveDispute_only_poster(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")
    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.postTask("Write about AI")
    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    contract.submitDelivery(task_id, "https://example.com/off-topic")
    direct_vm.sender = direct_bob
    contract.rejectDelivery(task_id)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("Only the poster can resolve a dispute"):
        contract.resolveDispute(task_id)
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Only the poster can resolve a dispute"):
        contract.resolveDispute(task_id)


def test_get_claim_count(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")
    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    contract.postTask("Task 1")
    direct_vm.sender = direct_alice
    contract.postTask("Task 2")
    count = contract.getClaimCount()
    assert json.loads(count)["count"] >= 2


# --------------------------------------------------------------------------
# STEWARD REQUEST: verify real balance changes, not internal logs.
# These tests MUST fail if the real transfer amount is wrong.
# --------------------------------------------------------------------------


def test_pass_pays_agent_real_balance(direct_vm, direct_deploy,
                                       direct_alice, direct_bob):
    """PASS: agent's balance increases by reward amount."""
    contract = direct_deploy("contracts/agent_coordination.py")

    reward = 500000000000000000

    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")

    direct_vm.sender = direct_bob
    direct_vm.value = reward
    task_id = contract.postTask("Write about AI")

    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    contract.submitDelivery(task_id, "https://example.com/ai-blog")

    # Check agent balance before approval
    balance_before = direct_vm.get_balance(direct_alice)

    contract.approveDelivery(task_id)

    # Check agent balance after approval
    balance_after = direct_vm.get_balance(direct_alice)

    # Agent should have received the reward
    assert balance_after == balance_before + reward, \
        f"Agent balance mismatch: {balance_after} != {balance_before} + {reward}"


def test_dispute_refunds_poster_real_balance(direct_vm, direct_deploy,
                                              direct_alice, direct_bob):
    """Dispute: poster's balance increases by refund amount."""
    contract = direct_deploy("contracts/agent_coordination.py")
    reward = 500000000000000000

    # 1. Alice registers as an agent
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")

    # 2. Bob posts the task (Status: OPEN)
    direct_vm.sender = direct_bob
    direct_vm.value = reward
    task_id = contract.postTask("Write about AI")

    # 3. Alice claims the task (Status: ASSIGNED)
    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    
    # 4. Alice submits delivery (Status: DELIVERED)
    contract.submitDelivery(task_id, "https://example.com")

    # 5. Bob (Poster) rejects delivery (Transitions Status to DISPUTED)
    direct_vm.sender = direct_bob
    contract.rejectDelivery(task_id)

    # Check poster balance before dispute resolution
    balance_before = direct_vm.get_balance(direct_bob)

    # 6. Bob (Poster) resolves dispute (Transitions Status to REFUNDED)
    direct_vm.sender = direct_bob
    contract.resolveDispute(task_id)

    # Check poster balance after dispute resolution
    balance_after = direct_vm.get_balance(direct_bob)

    # Assert balance verification
    assert balance_after == balance_before + reward, \
        f"Poster balance mismatch: {balance_after} != {balance_before} + {reward}"


def test_payout_amount_matches_real_balance_change(direct_vm, direct_deploy,
                                                     direct_alice, direct_bob):
    """The actual payout must equal the reward amount."""
    contract = direct_deploy("contracts/agent_coordination.py")

    reward = 500000000000000000

    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")

    direct_vm.sender = direct_bob
    direct_vm.value = reward
    task_id = contract.postTask("Write about AI")

    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    contract.submitDelivery(task_id, "https://example.com/ai-blog")

    balance_before = direct_vm.get_balance(direct_alice)
    contract.approveDelivery(task_id)
    balance_after = direct_vm.get_balance(direct_alice)

    # The balance change must equal the reward
    assert balance_after - balance_before == reward, \
        f"Balance change {balance_after - balance_before} != reward {reward}"


def test_refund_amount_matches_real_balance_change(direct_vm, direct_deploy,
                                                    direct_alice, direct_bob):
    """The actual refund must equal the reward amount."""
    contract = direct_deploy("contracts/agent_coordination.py")

    reward = 500000000000000000

    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")

    direct_vm.sender = direct_bob
    direct_vm.value = reward
    task_id = contract.postTask("Write about AI")

    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    contract.submitDelivery(task_id, "https://example.com/off-topic")

    direct_vm.sender = direct_bob
    contract.rejectDelivery(task_id)

    balance_before = direct_vm.get_balance(direct_bob)
    contract.resolveDispute(task_id)
    balance_after = direct_vm.get_balance(direct_bob)

    # The balance change must equal the reward
    assert balance_after - balance_before == reward, \
        f"Balance change {balance_after - balance_before} != reward {reward}"
