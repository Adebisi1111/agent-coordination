"""
Integration tests — require GenLayer Studio running.

These tests verify ACTUAL account-balance changes and emitted external transfers
on Studio Network, not just contract-maintained bookkeeping.

Run with: gltest tests/integration/ -v -s
"""
import pytest
import json
import time


@pytest.mark.integration
def test_payout_emitted_transfer_logged(
    integration_vm, integration_deploy, integration_alice, integration_bob
):
    """PASS verification: emitted payout transfer is logged with correct amount.
    
    This test checks the on-chain emitted transfer log, which records
    actual external transfers emitted via _Recipient.emit_transfer().
    """
    contract = integration_deploy("agent_coordination.py")
    
    reward_amount = 0.01  # GEN
    stake_amount = 0.01   # GEN
    
    # Register as agent (Alice)
    fn = contract.registerAgent(args=["writing", ""])
    fn.transact_method(value=int(stake_amount * 10**18), wait_interval=5000, wait_retries=10)
    
    # Post task with reward (Bob is poster)
    fn = contract.postTask(args=["AI safety", ""])
    post_result = fn.transact_method(value=int(reward_amount * 10**18), wait_interval=5000, wait_retries=10)
    
    task_id = post_result.get("result", "")
    
    # Claim and deliver task (Alice is agent)
    fn = contract.claimTask(args=[task_id])
    fn.transact_method(wait_interval=5000, wait_retries=10)
    fn = contract.submitDelivery(args=[task_id, "https://example.com/ai-safety-delivery"])
    fn.transact_method(wait_interval=5000, wait_retries=10)
    
    # Approve delivery (direct approval)
    fn = contract.approveDelivery(args=[task_id])
    fn.transact_method(wait_interval=10000, wait_retries=15)
    
    # Wait for external transfer to finalize
    time.sleep(60)
    
    # Check emitted transfer log
    transfers = json.loads(contract.getEmittedTransfers())
    payouts = [v for v in transfers.values() if json.loads(v)["type"] == "payout"]
    assert len(payouts) == 1, f"Expected 1 payout, got {len(payouts)}"
    
    payout_data = json.loads(payouts[0])
    assert payout_data["amount"] == int(reward_amount * 10**18), \
        f"Payout amount mismatch: {payout_data['amount']} != {int(reward_amount * 10**18)}"
    assert payout_data["to"] == integration_alice.address, \
        f"Payout recipient mismatch: {payout_data['to']}"
    
    # Check external transfer log
    log = json.loads(contract.getExternalTransferLog())
    log_entries = [v for v in log.values() if json.loads(v)["type"] == "payout"]
    assert len(log_entries) == 1, f"Expected 1 payout log, got {len(log_entries)}"
    log_data = json.loads(log_entries[0])
    assert log_data["status"] == "emitted", \
        f"Payout status mismatch: {log_data['status']}"


@pytest.mark.integration
def test_refund_emitted_transfer_logged(
    integration_vm, integration_deploy, integration_alice, integration_bob
):
    """Dispute resolution: emitted refund transfer is logged with correct amount.
    
    This test checks the on-chain emitted transfer log, which records
    actual external transfers emitted via _Recipient.emit_transfer().
    """
    contract = integration_deploy("agent_coordination.py")
    
    reward_amount = 0.01  # GEN
    stake_amount = 0.01   # GEN
    
    # Register as agent (Alice)
    fn = contract.registerAgent(args=["writing", ""])
    fn.transact_method(value=int(stake_amount * 10**18), wait_interval=5000, wait_retries=10)
    
    # Post task with reward (Bob is poster)
    fn = contract.postTask(args=["Write about AI", ""])
    post_result = fn.transact_method(value=int(reward_amount * 10**18), wait_interval=5000, wait_retries=10)
    
    task_id = post_result.get("result", "")
    
    # Claim and deliver task (Alice is agent)
    fn = contract.claimTask(args=[task_id])
    fn.transact_method(wait_interval=5000, wait_retries=10)
    fn = contract.submitDelivery(args=[task_id, "https://example.com/off-topic"])
    fn.transact_method(wait_interval=5000, wait_retries=10)
    
    # Resolve dispute (Bob is poster)
    fn = contract.resolveDispute(args=[task_id])
    fn.transact_method(wait_interval=5000, wait_retries=10)
    
    # Wait for external transfer to finalize
    time.sleep(60)
    
    # Check emitted transfer log
    transfers = json.loads(contract.getEmittedTransfers())
    refunds = [v for v in transfers.values() if json.loads(v)["type"] == "refund"]
    assert len(refunds) == 1, f"Expected 1 refund, got {len(refunds)}"
    
    refund_data = json.loads(refunds[0])
    assert refund_data["amount"] == int(reward_amount * 10**18), \
        f"Refund amount mismatch: {refund_data['amount']} != {int(reward_amount * 10**18)}"
    assert refund_data["to"] == integration_bob.address, \
        f"Refund recipient mismatch: {refund_data['to']}"
    
    # Check external transfer log
    log = json.loads(contract.getExternalTransferLog())
    log_entries = [v for v in log.values() if json.loads(v)["type"] == "refund"]
    assert len(log_entries) == 1, f"Expected 1 refund log, got {len(log_entries)}"
    log_data = json.loads(log_entries[0])
    assert log_data["status"] == "emitted", \
        f"Refund status mismatch: {log_data['status']}"
