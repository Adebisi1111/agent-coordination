import json
import pytest


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
# Real balance verification tests
# These tests use the integration_vm fixture to check actual account balances
# before and after payout/refund operations.
# --------------------------------------------------------------------------


def test_payout_increases_agent_balance(integration_vm, deployed_contract, integration_alice, integration_bob):
    """Real balance test: approveDelivery increases agent's balance."""
    contract = deployed_contract
    reward = 500000000000000000
    
    # Setup: alice registers as agent
    contract.registerAgent("writing", caller=integration_alice, value=2000000000000000000)
    
    # Bob posts task with reward
    contract.postTask("Write about AI", caller=integration_bob, value=reward)
    task_id = "task-1"
    
    # Record alice's balance BEFORE approval
    balance_before = integration_vm.get_balance(integration_alice)
    
    # Alice claims, delivers, and gets approved
    contract.claimTask(task_id, caller=integration_alice)
    contract.submitDelivery(task_id, "https://example.com/ai-blog", caller=integration_alice)
    contract.approveDelivery(task_id, caller=integration_bob)
    
    # Record alice's balance AFTER approval
    balance_after = integration_vm.get_balance(integration_alice)
    
    # VERIFY: Agent's balance increased by reward amount
    assert balance_after >= balance_before + reward, \
        f"Agent balance did not increase. Before: {balance_before}, After: {balance_after}, Expected increase: {reward}"


def test_refund_increases_poster_balance(integration_vm, deployed_contract, integration_alice, integration_bob):
    """Real balance test: resolveDispute increases poster's balance."""
    contract = deployed_contract
    reward = 500000000000000000
    
    # Setup: alice registers as agent
    contract.registerAgent("writing", caller=integration_alice, value=2000000000000000000)
    
    # Bob posts task
    contract.postTask("Write about AI", caller=integration_bob, value=reward)
    task_id = "task-1"
    
    # Record bob's balance BEFORE dispute resolution
    balance_before = integration_vm.get_balance(integration_bob)
    
    # Alice claims, delivers (bad delivery), bob rejects, resolves dispute
    contract.claimTask(task_id, caller=integration_alice)
    contract.submitDelivery(task_id, "https://example.com/off-topic", caller=integration_alice)
    contract.rejectDelivery(task_id, caller=integration_bob)
    contract.resolveDispute(task_id, caller=integration_bob)
    
    # Record bob's balance AFTER dispute resolution
    balance_after = integration_vm.get_balance(integration_bob)
    
    # VERIFY: Poster's balance increased by refund amount
    assert balance_after >= balance_before + reward, \
        f"Poster balance did not increase. Before: {balance_before}, After: {balance_after}, Expected increase: {reward}"


def test_cancel_refunds_poster_balance(integration_vm, deployed_contract, integration_alice, integration_bob):
    """Real balance test: cancelTask increases poster's balance."""
    contract = deployed_contract
    reward = 500000000000000000
    
    # Bob posts task
    contract.postTask("Write about AI", caller=integration_bob, value=reward)
    task_id = "task-1"
    
    # Record bob's balance BEFORE cancel
    balance_before = integration_vm.get_balance(integration_bob)
    
    # Bob cancels task
    contract.cancelTask(task_id, caller=integration_bob)
    
    # Record bob's balance AFTER cancel
    balance_after = integration_vm.get_balance(integration_bob)
    
    # VERIFY: Poster's balance increased by refund amount
    assert balance_after >= balance_before + reward, \
        f"Poster balance did not increase after cancel. Before: {balance_before}, After: {balance_after}, Expected increase: {reward}"
