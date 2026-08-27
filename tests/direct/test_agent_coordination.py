import json


def _hex(addr):
    if isinstance(addr, (bytes, bytearray)):
        from genlayer.py.types import Address
        return Address(bytes(addr)).as_hex
    return str(addr)


def test_registerAgent(direct_vm, direct_deploy, direct_alice):
    """Agent registers with stake."""
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing,coding,research")
    out = json.loads(contract.getAgent(direct_alice))
    assert out["exists"] is True
    assert out["stake"] == 2000000000000000000
    assert out["reputation"] == 0
    assert out["active"] is True


def test_postTask(direct_vm, direct_deploy, direct_bob):
    """Post a task with reward."""
    contract = direct_deploy("contracts/agent_coordination.py")
    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.postTask("Write a blog post about AI safety")
    out = json.loads(contract.getTask(task_id))
    assert out["exists"] is True
    assert out["reward"] == 500000000000000000
    assert out["status"] == "OPEN"


def test_claim_and_deliver(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Agent claims task and submits delivery."""
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
    assert out["assignee"].lower() == _hex(direct_alice).lower()
    contract.submitDelivery(task_id, "https://example.com/delivery")
    out = json.loads(contract.getTask(task_id))
    assert out["status"] == "DELIVERED"


def test_verifyDelivery_pass(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Delivery verified as PASS, agent reputation increases."""
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
    out = json.loads(contract.getAgent(direct_alice))
    assert out["reputation"] == 1


def test_verifyDelivery_fail(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Delivery verified as FAIL, status becomes DISPUTED."""
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
    """Poster can cancel an open task and get a full refund."""
    contract = direct_deploy("contracts/agent_coordination.py")

    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.postTask("Write about AI")

    # balance before cancel
    poster_before = int(contract.getExpectedBalance(_hex(direct_bob)))
    direct_vm.sender = direct_bob
    contract.cancelTask(task_id)
    poster_after = int(contract.getExpectedBalance(_hex(direct_bob)))

    assert json.loads(contract.getTask(task_id))["status"] == "CANCELLED"
    # cancel refunds the locked reward back to poster
    assert poster_after - poster_before == 500000000000000000


def test_cancelTask_only_poster(direct_vm, direct_deploy,
                                direct_alice, direct_bob, direct_charlie):
    """Only the poster can cancel; agent and strangers cannot."""
    contract = direct_deploy("contracts/agent_coordination.py")

    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")

    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.postTask("Write about AI")

    direct_vm.sender = direct_alice
    contract.claimTask(task_id)

    # agent cannot cancel
    with direct_vm.expect_revert("Only the poster can cancel"):
        contract.cancelTask(task_id)

    # stranger cannot cancel
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Only the poster can cancel"):
        contract.cancelTask(task_id)


def test_cancelTask_not_open_or_assigned(direct_vm, direct_deploy,
                                          direct_alice, direct_bob):
    """A delivered task cannot be cancelled."""
    contract = direct_deploy("contracts/agent_coordination.py")

    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")

    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.postTask("Write about AI")

    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    contract.submitDelivery(task_id, "https://example.com/delivery")

    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("Only open or assigned tasks can be cancelled"):
        contract.cancelTask(task_id)


def test_full_escrow_lifecycle_pass(direct_vm, direct_deploy,
                                    direct_alice, direct_bob):
    """Full lifecycle: post → claim → deliver → verify PASS → agent paid."""
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
    agent = json.loads(contract.getAgent(direct_alice))
    assert agent["reputation"] == 1


def test_full_escrow_lifecycle_dispute(direct_vm, direct_deploy,
                                       direct_alice, direct_bob):
    """Full lifecycle: post → claim → deliver → verify FAIL → dispute → refund."""
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


# --------------------------------------------------------------------------
# STEWARD REQUEST: focused tests for reward balances and both settlement
# outcomes. These tests MUST fail if payout/refund amounts are wrong, even
# when status and reputation are correct.
# --------------------------------------------------------------------------


def test_pass_pays_agent_and_deducts_poster(direct_vm, direct_deploy,
                                             direct_alice, direct_bob):
    """PASS / successful completion: agent receives the reward, poster pays it."""
    contract = direct_deploy("contracts/agent_coordination.py")

    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")

    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    # balances before posting
    poster_before = int(contract.getExpectedBalance(_hex(direct_bob)))
    agent_before = int(contract.getExpectedBalance(_hex(direct_alice)))
    task_id = contract.postTask("Write about AI")

    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    contract.submitDelivery(task_id, "https://example.com/ai-blog")

    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "AI is transformative..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "PASS", "reason": "fulfills task"}))
    contract.verifyDelivery(task_id)

    # balances after
    poster_after = int(contract.getExpectedBalance(_hex(direct_bob)))
    agent_after = int(contract.getExpectedBalance(_hex(direct_alice)))

    reward = 500000000000000000

    # agent was paid the reward
    assert agent_after - agent_before == reward, \
        f"agent should gain {reward}, gained {agent_after - agent_before}"
    # poster paid the reward
    assert poster_after - poster_before == -reward, \
        f"poster should lose {reward}, lost {poster_after - poster_before}"
    # task settled VERIFIED
    assert json.loads(contract.getTask(task_id))["status"] == "VERIFIED"
    # agent reputation increased
    assert int(json.loads(contract.getAgent(direct_alice))["reputation"]) == 1
    # emitted payout matches reward
    transfers = json.loads(contract.getEmittedTransfers())
    payouts = [v for v in transfers.values() if json.loads(v)["type"] == "payout"]
    assert len(payouts) == 1
    assert json.loads(payouts[0])["amount"] == reward
    assert json.loads(payouts[0])["to"] == _hex(direct_alice)


def test_dispute_refunds_poster_and_pays_nothing_to_agent(direct_vm, direct_deploy,
                                                          direct_alice, direct_bob):
    """Dispute / refund: poster reclaims the reward, agent receives nothing."""
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

    # balances before
    poster_before = int(contract.getExpectedBalance(_hex(direct_bob)))
    agent_before = int(contract.getExpectedBalance(_hex(direct_alice)))

    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "Cooking recipes..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "FAIL", "reason": "off topic"}))
    contract.verifyDelivery(task_id)

    direct_vm.sender = direct_bob
    contract.resolveDispute(task_id)

    # balances after
    poster_after = int(contract.getExpectedBalance(_hex(direct_bob)))
    agent_after = int(contract.getExpectedBalance(_hex(direct_alice)))

    reward = 500000000000000000

    # poster got the reward back
    assert poster_after - poster_before == reward, \
        f"poster should gain {reward}, gained {poster_after - poster_before}"
    # agent received nothing
    assert agent_after == agent_before, \
        f"agent should receive nothing, balance changed by {agent_after - agent_before}"
    # task settled REFUNDED
    assert json.loads(contract.getTask(task_id))["status"] == "REFUNDED"
    # agent reputation did NOT increase
    assert int(json.loads(contract.getAgent(direct_alice))["reputation"]) == 0
    # emitted refund matches reward
    transfers = json.loads(contract.getEmittedTransfers())
    refunds = [v for v in transfers.values() if json.loads(v)["type"] == "refund"]
    assert len(refunds) == 1
    assert json.loads(refunds[0])["amount"] == reward
    assert json.loads(refunds[0])["to"] == _hex(direct_bob)


def test_resolveDispute_only_poster(direct_vm, direct_deploy,
                                    direct_alice, direct_bob, direct_charlie):
    """Only the poster may resolve a dispute; the agent and strangers cannot."""
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

    # agent cannot resolve
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("Only the poster can resolve a dispute"):
        contract.resolveDispute(task_id)

    # stranger cannot resolve
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("Only the poster can resolve a dispute"):
        contract.resolveDispute(task_id)


def test_resolveDispute_not_disputed(direct_vm, direct_deploy,
                                     direct_alice, direct_bob):
    """A task that is not disputed cannot be resolved."""
    contract = direct_deploy("contracts/agent_coordination.py")

    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")

    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.postTask("Write about AI")

    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("Task is not disputed"):
        contract.resolveDispute(task_id)


def test_submitDelivery_then_verify_full_workflow(direct_vm, direct_deploy,
                                                  direct_alice, direct_bob):
    """The full repository workflow reaches verification through the
    submitDelivery client call — the path the steward flagged as missing."""
    contract = direct_deploy("contracts/agent_coordination.py")

    direct_vm.sender = direct_alice
    direct_vm.value = 2000000000000000000
    contract.registerAgent("writing")

    direct_vm.sender = direct_bob
    direct_vm.value = 500000000000000000
    task_id = contract.postTask("Write about AI")

    # claim → submit → verify: every step succeeds
    direct_vm.sender = direct_alice
    contract.claimTask(task_id)
    assert json.loads(contract.getTask(task_id))["status"] == "ASSIGNED"

    contract.submitDelivery(task_id, "https://example.com/ai-blog")
    assert json.loads(contract.getTask(task_id))["status"] == "DELIVERED"

    direct_vm.mock_web(r".*example.*", {"status": 200, "body": "AI is transformative..."})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "PASS", "reason": "fulfills task"}))
    contract.verifyDelivery(task_id)
    assert json.loads(contract.getTask(task_id))["status"] == "VERIFIED"


def test_empty_evidence_fails_verification(direct_vm, direct_deploy,
                                           direct_alice, direct_bob):
    """An unreadable source (e.g. a PDF renders as empty text) fails
    verification rather than passing."""
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

    direct_vm.mock_web(r".*example.*", {"status": 200, "body": ""})
    direct_vm.mock_llm(r".*", json.dumps({"verdict": "PASS", "reason": "fulfills"}))
    contract.verifyDelivery(task_id)

    assert json.loads(contract.getTask(task_id))["status"] == "DISPUTED"
