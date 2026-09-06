"""
Integration tests — require GenLayer Studio running.

These tests verify ACTUAL account-balance changes and emitted external transfers
on Studio Network, not just contract-maintained bookkeeping.

Run with: gltest tests/integration/ -v -s
"""
import pytest
import json


@pytest.mark.integration
def test_payout_changes_agent_balance(
    integration_vm, integration_deploy, integration_alice, integration_bob
):
    """PASS verification: agent's ACTUAL balance increases by reward.
    
    This test checks REAL account balances, not contract-internal records.
    It will FAIL if the actual ETH transfer doesn't happen.
    """
    contract = integration_deploy("contracts/agent_coordination.py")
    
    reward_amount = 0.5  # GEN
    stake_amount = 2.0   # GEN
    
    # Get ACTUAL initial balances (not contract records)
    alice_balance_before = integration_vm.get_balance(integration_alice)
    bob_balance_before = integration_vm.get_balance(integration_bob)
    
    # Register as agent
    contract.registerAgent(
        args=["writing", ""],
        value=stake_amount,
        wait_interval=5000,
        wait_retries=10,
    )
    
    # Post task with reward
    post_result = contract.postTask(
        args=["AI safety", ""],
        value=reward_amount,
        wait_interval=5000,
        wait_retries=10,
    )
    
    # Get task ID from result
    task_id = post_result.get("result", "")
    
    # Claim and deliver task
    contract.claimTask(
        args=[task_id],
        wait_interval=5000,
        wait_retries=10,
    )
    contract.submitDelivery(
        args=[task_id, "https://en.wikipedia.org/wiki/AI_safety"],
        wait_interval=5000,
        wait_retries=10,
    )
    
    # Get ACTUAL balance before verification
    alice_balance_before_verify = integration_vm.get_balance(integration_alice)
    
    # Verify delivery (PASS)
    contract.verifyDelivery(
        args=[task_id],
        wait_interval=10000,
        wait_retries=15,
    )
    
    # Wait for external transfer to finalize
    import time
    time.sleep(60)
    
    # Get ACTUAL balance after verification
    alice_balance_after_verify = integration_vm.get_balance(integration_alice)
    
    # Verify ACTUAL balance increased by reward amount
    balance_delta = alice_balance_after_verify - alice_balance_before_verify
    assert balance_delta == reward_amount, \
        f"ACTUAL balance delta {balance_delta} != reward {reward_amount}"


@pytest.mark.integration
def test_refund_changes_poster_balance(
    integration_vm, integration_deploy, integration_alice, integration_bob
):
    """Dispute resolution: poster's ACTUAL balance increases by reward.
    
    This test checks REAL account balances, not contract-internal records.
    It will FAIL if the actual ETH refund doesn't happen.
    """
    contract = integration_deploy("contracts/agent_coordination.py")
    
    reward_amount = 0.5  # GEN
    stake_amount = 2.0   # GEN
    
    # Register as agent
    contract.registerAgent(
        args=["writing", ""],
        value=stake_amount,
        wait_interval=5000,
        wait_retries=10,
    )
    
    # Post task with reward
    post_result = contract.postTask(
        args=["Write about AI", ""],
        value=reward_amount,
        wait_interval=5000,
        wait_retries=10,
    )
    
    task_id = post_result.get("result", "")
    
    # Claim and deliver task
    contract.claimTask(
        args=[task_id],
        wait_interval=5000,
        wait_retries=10,
    )
    contract.submitDelivery(
        args=[task_id, "https://example.com/off-topic"],
        wait_interval=5000,
        wait_retries=10,
    )
    
    # Get ACTUAL balance before dispute resolution
    bob_balance_before = integration_vm.get_balance(integration_bob)
    
    # Verify delivery (FAIL → DISPUTED)
    contract.verifyDelivery(
        args=[task_id],
        wait_interval=10000,
        wait_retries=15,
    )
    
    # Resolve dispute
    contract.resolveDispute(
        args=[task_id],
        wait_interval=5000,
        wait_retries=10,
    )
    
    # Wait for external transfer to finalize
    import time
    time.sleep(60)
    
    # Get ACTUAL balance after dispute resolution
    bob_balance_after = integration_vm.get_balance(integration_bob)
    
    # Verify ACTUAL balance increased by reward
    balance_delta = bob_balance_after - bob_balance_before
    assert balance_delta == reward_amount, \
        f"ACTUAL refund balance delta {balance_delta} != reward {reward_amount}"
