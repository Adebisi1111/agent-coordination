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
# Emitted transfer verification (direct-mode safe).
# These tests verify the contract correctly RECORDS external transfers.
# For live balance verification, see tests/integration/test_agent_coordination.py.
# --------------------------------------------------------------------------


def test_payout_emits_external_transfer(direct_vm, direct_deploy, direct_alice, direct_bob):
    """PASS path: approveDelivery emits external transfer to agent."""
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
    contract.approveDelivery(task_id)

    # Verify emitted transfer via contract view
    transfers_raw = contract.getEmittedTransfers()
    transfers = json.loads(transfers_raw) if isinstance(transfers_raw, str) else transfers_raw

    # Should have at least one payout transfer
    payout_found = False
    for key, val in transfers.items():
        t = json.loads(val) if isinstance(val, str) else val
        if t.get("type") == "payout" and int(t.get("amount", 0)) == reward:
            payout_found = True
            break

    assert payout_found, f"No payout transfer found with amount {reward}. Transfers: {transfers}"


def test_refund_emits_external_transfer(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Dispute path: resolveDispute emits external transfer to poster."""
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
    contract.resolveDispute(task_id)

    # Verify emitted transfer via contract view
    transfers_raw = contract.getEmittedTransfers()
    transfers = json.loads(transfers_raw) if isinstance(transfers_raw, str) else transfers_raw

    # Should have at least one refund transfer
    refund_found = False
    for key, val in transfers.items():
        t = json.loads(val) if isinstance(val, str) else val
        if t.get("type") == "refund" and int(t.get("amount", 0)) == reward:
            refund_found = True
            break

    assert refund_found, f"No refund transfer found with amount {reward}. Transfers: {transfers}"


def test_cancel_emits_external_transfer(direct_vm, direct_deploy, direct_bob):
    """Cancel path: cancelTask emits external transfer to poster."""
    contract = direct_deploy("contracts/agent_coordination.py")
    reward = 500000000000000000

    direct_vm.sender = direct_bob
    direct_vm.value = reward
    task_id = contract.postTask("Write about AI")
    contract.cancelTask(task_id)

    # Verify emitted transfer via contract view
    transfers_raw = contract.getEmittedTransfers()
    transfers = json.loads(transfers_raw) if isinstance(transfers_raw, str) else transfers_raw

    # Should have at least one refund transfer (cancel = refund)
    refund_found = False
    for key, val in transfers.items():
        t = json.loads(val) if isinstance(val, str) else val
        if t.get("type") == "refund" and int(t.get("amount", 0)) == reward:
            refund_found = True
            break

    assert refund_found, f"No refund transfer found after cancel. Transfers: {transfers}"
