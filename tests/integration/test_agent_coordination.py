import pytest
import json
import time


@pytest.mark.integration
def test_payout_real_balance_change(
    integration_vm, integration_deploy, integration_alice, integration_bob
):
    """PASS verification: agent's balance increases by reward amount."""
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
    
    # Check agent balance before approval
    balance_before = integration_vm.get_balance(integration_alice)
    
    # Approve delivery (direct approval)
    fn = contract.approveDelivery(args=[task_id])
    fn.transact_method(wait_interval=10000, wait_retries=15)
    
    # Wait for external transfer to finalize
    time.sleep(60)
    
    # Check agent balance after approval
    balance_after = integration_vm.get_balance(integration_alice)
    
    # Agent should have received the reward
    assert balance_after == balance_before + int(reward_amount * 10**18), \
        f"Agent balance mismatch: {balance_after} != {balance_before} + {int(reward_amount * 10**18)}"


@pytest.mark.integration
def test_refund_real_balance_change(
    integration_vm, integration_deploy, integration_alice, integration_bob
):
    """Dispute resolution: poster's balance increases by refund amount."""
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
    
    # Reject delivery (Bob is poster)
    fn = contract.rejectDelivery(args=[task_id])
    fn.transact_method(wait_interval=5000, wait_retries=10)
    
    # Check poster balance before dispute resolution
    balance_before = integration_vm.get_balance(integration_bob)
    
    # Resolve dispute (Bob is poster)
    fn = contract.resolveDispute(args=[task_id])
    fn.transact_method(wait_interval=5000, wait_retries=10)
    
    # Wait for external transfer to finalize
    time.sleep(60)
    
    # Check poster balance after dispute resolution
    balance_after = integration_vm.get_balance(integration_bob)
    
    # Poster should have received the refund
    assert balance_after == balance_before + int(reward_amount * 10**18), \
        f"Poster balance mismatch: {balance_after} != {balance_before} + {int(reward_amount * 10**18)}"
