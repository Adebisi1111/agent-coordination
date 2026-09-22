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
    """PASS verification: agent's balance increases and contract balance decreases."""
    contract = deployed_contract
    
    reward_amount_wei = 500000000000000000  # 0.5 GEN
    stake_amount_wei = 1000000000000000000  # 1 GEN
    
    # Register as agent (Alice) - send stake
    tx = contract.registerAgent(args=["writing", ""], value=stake_amount_wei).transact()
    
    # Post task with reward (Bob is poster)
    tx = contract.postTask(args=["AI safety research paper", ""], value=reward_amount_wei, sender=integration_bob).transact()
    
    task_id = "task-1"
    
    # Claim and deliver task (Alice is agent)
    tx = contract.claimTask(args=[task_id], sender=integration_alice).transact()
    tx = contract.submitDelivery(args=[task_id, "https://example.com/ai-safety-delivery"], sender=integration_alice).transact()
    
    # Record balances BEFORE payout
    contract_balance_before = integration_vm.get_balance(contract.address)
    agent_balance_before = integration_vm.get_balance(integration_alice)
    
    # Approve delivery — triggers payout (Bob is poster)
    tx = contract.approveDelivery(args=[task_id], sender=integration_bob).transact()
    
    # Wait for external transfer to finalize
    time.sleep(90)
    
    # Record balances AFTER payout
    contract_balance_after = integration_vm.get_balance(contract.address)
    agent_balance_after = integration_vm.get_balance(integration_alice)
    
    # Calculate changes
    contract_decrease = contract_balance_before - contract_balance_after
    agent_increase = agent_balance_after - agent_balance_before
    
    # VERIFY: Contract balance decreased by reward amount
    assert contract_decrease >= reward_amount_wei, \
        f"Contract balance did not decrease. Before: {contract_balance_before}, After: {contract_balance_after}, Decrease: {contract_decrease}"
    
    # VERIFY: Agent received the funds (may have gas costs deducted)
    assert agent_increase > 0, \
        f"Agent balance did not increase. Before: {agent_balance_before}, After: {agent_balance_after}"


@pytest.mark.integration
def test_refund_real_balance_change(
    integration_vm, deployed_contract, integration_alice, integration_bob
):
    """Dispute resolution: poster's balance increases and contract balance decreases."""
    contract = deployed_contract
    
    reward_amount_wei = 500000000000000000  # 0.5 GEN
    stake_amount_wei = 1000000000000000000  # 1 GEN
    
    # Register as agent (Alice)
    tx = contract.registerAgent(args=["writing", ""], value=stake_amount_wei).transact()
    
    # Post task with reward (Bob is poster)
    tx = contract.postTask(args=["Write about AI", ""], value=reward_amount_wei, sender=integration_bob).transact()
    
    task_id = "task-1"
    
    # Claim and deliver task (Alice is agent)
    tx = contract.claimTask(args=[task_id], sender=integration_alice).transact()
    tx = contract.submitDelivery(args=[task_id, "https://example.com/off-topic"], sender=integration_alice).transact()
    
    # Reject delivery (Bob is poster)
    tx = contract.rejectDelivery(args=[task_id], sender=integration_bob).transact()
    
    # Record balances BEFORE refund
    contract_balance_before = integration_vm.get_balance(contract.address)
    poster_balance_before = integration_vm.get_balance(integration_bob)
    
    # Resolve dispute — triggers refund (Bob is poster)
    tx = contract.resolveDispute(args=[task_id], sender=integration_bob).transact()
    
    # Wait for external transfer to finalize
    time.sleep(90)
    
    # Record balances AFTER refund
    contract_balance_after = integration_vm.get_balance(contract.address)
    poster_balance_after = integration_vm.get_balance(integration_bob)
    
    # Calculate changes
    contract_decrease = contract_balance_before - contract_balance_after
    poster_increase = poster_balance_after - poster_balance_before
    
    # VERIFY: Contract balance decreased by refund amount
    assert contract_decrease >= reward_amount_wei, \
        f"Contract balance did not decrease. Before: {contract_balance_before}, After: {contract_balance_after}, Decrease: {contract_decrease}"
    
    # VERIFY: Poster received the funds
    assert poster_increase > 0, \
        f"Poster balance did not increase. Before: {poster_balance_before}, After: {poster_balance_after}"
