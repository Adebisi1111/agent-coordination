"""
Integration tests — require GenLayer Studio running.

These tests verify ACTUAL account-balance changes on Studio Network,
not just contract-maintained bookkeeping.

Run with: gltest tests/integration/ -v -s
"""
import pytest
import json
import time


@pytest.mark.integration
def test_payout_real_balance_change(
    integration_vm, deployed_contract, integration_alice, integration_bob
):
    """PASS verification: agent's balance increases by reward amount."""
    contract = deployed_contract
    
    # Use larger reward to offset gas costs
    reward_amount_wei = 500000000000000000  # 0.5 GEN
    stake_amount_wei = 1000000000000000000  # 1 GEN
    
    # Fund the contract for payouts
    integration_bob.transfer(contract.address, 2000000000000000000)  # 2 GEN
    
    # Register as agent (Alice)
    fn = contract.registerAgent(args=["writing", ""])
    fn.transact_method(value=stake_amount_wei, wait_interval=5000, wait_retries=10)
    
    # Post task with reward (Bob is poster)
    fn = contract.postTask(args=["AI safety research paper"])
    post_result = fn.transact_method(value=reward_amount_wei, wait_interval=5000, wait_retries=10)
    
    task_id = post_result.get("result", "")
    assert task_id, f"Failed to get task_id from postTask result: {post_result}"
    
    # Claim and deliver task (Alice is agent)
    fn = contract.claimTask(args=[task_id])
    fn.transact_method(wait_interval=5000, wait_retries=10)
    fn = contract.submitDelivery(args=[task_id, "https://example.com/ai-safety-delivery"])
    fn.transact_method(wait_interval=5000, wait_retries=10)
    
    # Check agent balance before approval
    balance_before = integration_vm.get_balance(integration_alice)
    
    # Approve delivery (direct approval) — triggers payout
    fn = contract.approveDelivery(args=[task_id])
    fn.transact_method(wait_interval=10000, wait_retries=15)
    
    # Wait for external transfer to finalize
    time.sleep(60)
    
    # Check agent balance after approval
    balance_after = integration_vm.get_balance(integration_alice)
    
    # Agent should have received the reward (minus gas costs, so check >=)
    balance_increase = balance_after - balance_before
    assert balance_increase >= reward_amount_wei // 2, \
        f"Agent balance increase too small: {balance_increase} < {reward_amount_wei // 2}. Before: {balance_before}, After: {balance_after}"


@pytest.mark.integration
def test_refund_real_balance_change(
    integration_vm, deployed_contract, integration_alice, integration_bob
):
    """Dispute resolution: poster's balance increases by refund amount."""
    contract = deployed_contract
    
    # Use larger reward to offset gas costs
    reward_amount_wei = 500000000000000000  # 0.5 GEN
    stake_amount_wei = 1000000000000000000  # 1 GEN
    
    # Register as agent (Alice)
    fn = contract.registerAgent(args=["writing", ""])
    fn.transact_method(value=stake_amount_wei, wait_interval=5000, wait_retries=10)
    
    # Post task with reward (Bob is poster)
    fn = contract.postTask(args=["Write about AI", ""])
    post_result = fn.transact_method(value=reward_amount_wei, wait_interval=5000, wait_retries=10)
    
    task_id = post_result.get("result", "")
    assert task_id, f"Failed to get task_id from postTask result: {post_result}"
    
    # Claim and deliver task (Alice is agent)
    fn = contract.claimTask(args=[task_id])
    fn.transact_method(wait_interval=5000, wait_retries=10)
    fn = contract.submitDelivery(args=[task_id, "https://example.com/off-topic"])
    fn.transact_method(wait_interval=5000, wait_retries=10)
    
    # Reject delivery (Bob is poster)
    fn = contract.rejectDelivery(args=[task_id])
    fn.transact_method(wait_interval=5000, wait_retries=10)
    
    # Check poster balance before dispute resolution
    balance_before = integration_vm.get_balance(integration_bob)
    
    # Resolve dispute (Bob is poster) — triggers refund
    fn = contract.resolveDispute(args=[task_id])
    fn.transact_method(wait_interval=5000, wait_retries=10)
    
    # Wait for external transfer to finalize
    time.sleep(60)
    
    # Check poster balance after dispute resolution
    balance_after = integration_vm.get_balance(integration_bob)
    
    # Poster should have received the refund
    balance_increase = balance_after - balance_before
    assert balance_increase >= reward_amount_wei // 2, \
        f"Poster balance increase too small: {balance_increase} < {reward_amount_wei // 2}. Before: {balance_before}, After: {balance_after}"
