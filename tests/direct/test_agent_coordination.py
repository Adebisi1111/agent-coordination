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


def test_verifyDelivery_pass(direct_vm, direct_deploy, direct_alice, direct_bob):
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
    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "AI is transformative..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "PASS", "reason": "fulfills task"}))
    contract.verifyDelivery(task_id)
    out = json.loads(contract.getTask(task_id))
    assert out["status"] == "VERIFIED"


def test_verifyDelivery_fail(direct_vm, direct_deploy, direct_alice, direct_bob):
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
    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "Cooking recipes..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "FAIL", "reason": "off topic"}))
    contract.verifyDelivery(task_id)
    out = json.loads(contract.getTask(task_id))
    assert out["status"] == "DISPUTED"


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
    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "AI is transformative..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "PASS", "reason": "fulfills task"}))
    contract.verifyDelivery(task_id)
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
    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "Cooking recipes..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "FAIL", "reason": "off topic"}))
    contract.verifyDelivery(task_id)
    assert json.loads(contract.getTask(task_id))["status"] == "DISPUTED"
    direct_vm.sender = direct_bob
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
    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "Cooking recipes..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "FAIL", "reason": "off topic"}))
    contract.verifyDelivery(task_id)
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
# STEWARD REQUEST: verify emitted transfers match expected balance deltas.
# These tests MUST fail if the real transfer amount is wrong.
# --------------------------------------------------------------------------


def test_pass_pays_agent_emitted_transfer_matches_reward(direct_vm, direct_deploy,
                                                          direct_alice, direct_bob):
    """PASS: emitted payout transfer matches the reward amount exactly."""
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

    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "AI is transformative..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "PASS", "reason": "fulfills task"}))
    contract.verifyDelivery(task_id)

    # Verify emitted external transfer matches reward
    transfers = json.loads(contract.getEmittedTransfers())
    payouts = [v for v in transfers.values() if json.loads(v)["type"] == "payout"]
    assert len(payouts) == 1, f"Expected 1 payout, got {len(payouts)}"

    payout_data = json.loads(payouts[0])
    assert payout_data["amount"] == reward, \
        f"Payout amount mismatch: {payout_data['amount']} != {reward}"
    assert payout_data["to"] == _hex(direct_alice), \
        f"Payout recipient mismatch: {payout_data['to']}"

    # Verify expected balance delta matches emitted transfer
    agent_delta = int(contract.getExpectedBalance(_hex(direct_alice)))
    assert agent_delta == reward, \
        f"Agent balance delta {agent_delta} != reward {reward}"

    # Verify external transfer log matches emitted transfer
    external_log = json.loads(contract.getExternalTransferLog())
    log_entries = [v for v in external_log.values() if json.loads(v)["type"] == "payout"]
    assert len(log_entries) == 1, f"Expected 1 payout log, got {len(log_entries)}"
    log_data = json.loads(log_entries[0])
    assert log_data["amount"] == reward, \
        f"External log payout amount mismatch: {log_data['amount']} != {reward}"
    assert log_data["to"] == _hex(direct_alice), \
        f"External log payout recipient mismatch: {log_data['to']}"
    assert log_data["status"] == "emitted", \
        f"External log payout status mismatch: {log_data['status']} != emitted"


def test_dispute_refunds_poster_emitted_transfer_matches_reward(direct_vm, direct_deploy,
                                                                 direct_alice, direct_bob):
    """Dispute: emitted refund transfer matches the reward amount exactly."""
    contract = direct_deploy("contracts/agent_coordination.py")

    reward = 500000000000000000

    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")

    direct_vm.sender = direct_bob
    direct_vm.value = reward
    task_id = contract.postTask("Write about AI")

    # After posting, poster's expected balance is -reward (locked in escrow)
    poster_after_post = int(contract.getExpectedBalance(_hex(direct_bob)))
    assert poster_after_post == -reward

    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    contract.submitDelivery(task_id, "https://example.com/off-topic")

    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "Cooking recipes..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "FAIL", "reason": "off topic"}))
    contract.verifyDelivery(task_id)

    direct_vm.sender = direct_bob
    contract.resolveDispute(task_id)

    # After refund, poster's expected balance should be back to 0
    poster_after_refund = int(contract.getExpectedBalance(_hex(direct_bob)))
    assert poster_after_refund == 0, \
        f"Poster balance after refund should be 0, got {poster_after_refund}"

    # The refund delta is: 0 - (-reward) = reward
    refund_delta = poster_after_refund - poster_after_post
    assert refund_delta == reward, \
        f"Refund delta mismatch: {refund_delta} != {reward}"

    # Verify emitted external transfer matches reward
    transfers = json.loads(contract.getEmittedTransfers())
    refunds = [v for v in transfers.values() if json.loads(v)["type"] == "refund"]
    assert len(refunds) == 1, f"Expected 1 refund, got {len(refunds)}"

    refund_data = json.loads(refunds[0])
    assert refund_data["amount"] == reward, \
        f"Refund amount mismatch: {refund_data['amount']} != {reward}"
    assert refund_data["to"] == _hex(direct_bob), \
        f"Refund recipient mismatch: {refund_data['to']}"


def test_payout_amount_matches_emitted_transfer_exactly(direct_vm, direct_deploy,
                                                         direct_alice, direct_bob):
    """The actual payout amount must equal the emitted transfer amount."""
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

    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "AI is transformative..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "PASS", "reason": "fulfills task"}))
    contract.verifyDelivery(task_id)

    # Verify emitted transfer exists and matches reward
    transfers = json.loads(contract.getEmittedTransfers())
    payouts = [v for v in transfers.values() if json.loads(v)["type"] == "payout"]
    assert len(payouts) == 1
    emitted_amount = json.loads(payouts[0])["amount"]

    # The emitted amount must equal the reward
    assert emitted_amount == reward, \
        f"Emitted payout {emitted_amount} != reward {reward}"

    # The expected balance delta must equal the emitted amount
    balance_delta = int(contract.getExpectedBalance(_hex(direct_alice)))
    assert balance_delta == emitted_amount, \
        f"Balance delta {balance_delta} != emitted payout {emitted_amount}"


def test_refund_amount_matches_emitted_transfer_exactly(direct_vm, direct_deploy,
                                                        direct_alice, direct_bob):
    """The actual refund amount must equal the emitted transfer amount."""
    contract = direct_deploy("contracts/agent_coordination.py")

    reward = 500000000000000000

    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")

    direct_vm.sender = direct_bob
    direct_vm.value = reward
    task_id = contract.postTask("Write about AI")

    # Record poster's expected balance after posting (locked in escrow)
    poster_after_post = int(contract.getExpectedBalance(_hex(direct_bob)))
    assert poster_after_post == -reward

    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    contract.submitDelivery(task_id, "https://example.com/off-topic")

    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "Cooking recipes..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "FAIL", "reason": "off topic"}))
    contract.verifyDelivery(task_id)

    direct_vm.sender = direct_bob
    contract.resolveDispute(task_id)

    # After refund, poster's balance should return to 0
    poster_after_refund = int(contract.getExpectedBalance(_hex(direct_bob)))
    assert poster_after_refund == 0

    # The refund delta is: 0 - (-reward) = reward
    refund_delta = poster_after_refund - poster_after_post
    assert refund_delta == reward, \
        f"Refund delta mismatch: {refund_delta} != {reward}"

    # Verify emitted transfer exists and matches reward
    transfers = json.loads(contract.getEmittedTransfers())
    refunds = [v for v in transfers.values() if json.loads(v)["type"] == "refund"]
    assert len(refunds) == 1
    emitted_amount = json.loads(refunds[0])["amount"]

    # The emitted amount must equal the reward
    assert emitted_amount == reward, \
        f"Emitted refund {emitted_amount} != reward {reward}"

    # The refund delta must equal the emitted amount
    assert refund_delta == emitted_amount, \
        f"Refund delta {refund_delta} != emitted refund {emitted_amount}"
