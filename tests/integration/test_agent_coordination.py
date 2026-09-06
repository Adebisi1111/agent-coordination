"""
Integration tests — require GenLayer Studio running.

These tests verify actual account-balance changes and emitted external transfers
on Studio, not just contract-maintained bookkeeping.

Run with: gltest tests/integration/ -v -s
"""
import pytest
import json
import time


@pytest.mark.integration
def test_payout_changes_agent_balance(
    integration_vm, integration_deploy, integration_alice, integration_bob
):
    """PASS verification: agent's actual balance increases by reward."""
    contract = integration_deploy("contracts/agent_coordination.py")
    
    reward_amount = 0.5  # GEN
    stake_amount = 2.0   # GEN
    
    # Get initial balances
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
        args=["Write about AI safety", ""],
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
        args=[task_id, "https://example.com/ai-blog"],
        wait_interval=5000,
        wait_retries=10,
    )
    
    # Get balance before verification
    alice_balance_before_verify = integration_vm.get_balance(integration_alice)
    
    # Verify delivery (PASS)
    contract.verifyDelivery(
        args=[task_id],
        wait_interval=10000,
        wait_retries=15,
    )
    
    # Get balance after verification
    alice_balance_after_verify = integration_vm.get_balance(integration_alice)
    
    # Verify actual balance increased
    balance_delta = alice_balance_after_verify - alice_balance_before_verify
    assert abs(balance_delta - reward_amount) < 0.001, \
        f"Balance delta {balance_delta} != reward {reward_amount}"


@pytest.mark.integration
def test_refund_changes_poster_balance(
    integration_vm, integration_deploy, integration_alice, integration_bob
):
    """Dispute resolution: poster's actual balance increases by reward."""
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
    
    # Get balance before dispute resolution
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
    
    # Get balance after dispute resolution
    bob_balance_after = integration_vm.get_balance(integration_bob)
    
    # Verify actual balance increased by reward
    balance_delta = bob_balance_after - bob_balance_before
    assert abs(balance_delta - reward_amount) < 0.001, \
        f"Refund balance delta {balance_delta} != reward {reward_amount}"
