const { createClient, chains } = require('genlayer-js');
const { privateKeyToAccount } = require('viem/accounts');

const CONTRACT = '0x12828cEB0072d167d8a8835711eB44DaEcAe029d';
const AGENT_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';

async function main() {
  const agentAccount = privateKeyToAccount(AGENT_KEY);
  const agentClient = createClient({ chain: chains.testnetBradbury, account: agentAccount });
  
  console.log('Agent address:', agentAccount.address);
  
  const balanceBefore = await agentClient.getBalance({ address: agentAccount.address });
  console.log('Balance before:', balanceBefore.toString(), 'wei =', Number(balanceBefore) / 1e18, 'GEN');
  
  // Register agent
  console.log('\n--- Register Agent ---');
  await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'registerAgent',
    args: ['writing', ''],
    value: 1000000000000000000n,  // 1 GEN (min stake)
  });
  console.log('Agent registered');
  
  // Post task
  console.log('\n--- Post Task ---');
  const reward = 500000000000000000n;  // 0.5 GEN
  await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'postTask',
    args: ['Write about AI safety', ''],
    value: reward,
  });
  console.log('Task posted');
  
  // Get task ID
  const taskCount = await agentClient.readContract({
    address: CONTRACT,
    functionName: 'getClaimCount',
    args: [],
  });
  const taskId = `task-${JSON.parse(taskCount).count}`;
  console.log('Task ID:', taskId);
  
  // Claim task
  console.log('\n--- Claim Task ---');
  await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'claimTask',
    args: [taskId],
  });
  console.log('Task claimed');
  
  // Submit delivery
  console.log('\n--- Submit Delivery ---');
  await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'submitDelivery',
    args: [taskId, 'https://example.com/ai-safety'],
  });
  console.log('Delivery submitted');
  
  // Verify delivery (PASS)
  console.log('\n--- Verify Delivery (PASS) ---');
  await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'verifyDelivery',
    args: [taskId],
  });
  console.log('Delivery verified');
  
  // Wait
  console.log('\nWaiting 30 seconds...');
  await new Promise(r => setTimeout(r, 30000));
  
  // Check emitted transfers
  const transfers = await agentClient.readContract({
    address: CONTRACT,
    functionName: 'getEmittedTransfers',
    args: [],
  });
  console.log('\nEmitted transfers:', transfers);
  
  // Check balance delta
  const balanceAfter = await agentClient.getBalance({ address: agentAccount.address });
  const delta = balanceAfter - balanceBefore;
  console.log('\nBalance after:', balanceAfter.toString(), 'wei =', Number(balanceAfter) / 1e18, 'GEN');
  console.log('Balance delta:', delta.toString(), 'wei =', Number(delta) / 1e18, 'GEN');
  
  // Verify payout
  const transfersObj = JSON.parse(transfers);
  const payouts = Object.values(transfersObj).filter(v => JSON.parse(v).type === 'payout');
  
  if (payouts.length === 1) {
    const payout = JSON.parse(payouts[0]);
    console.log('\n=== PAYOUT VERIFICATION ===');
    console.log('Payout amount:', payout.amount.toString(), 'wei =', Number(payout.amount) / 1e18, 'GEN');
    console.log('Expected reward:', reward.toString(), 'wei =', Number(reward) / 1e18, 'GEN');
    console.log('Amount match:', payout.amount.toString() === reward.toString());
    console.log('Recipient:', payout.to);
    console.log('Expected recipient:', agentAccount.address);
    console.log('Recipient match:', payout.to.toLowerCase() === agentAccount.address.toLowerCase());
    console.log('Balance increased:', delta > 0 ? 'YES' : 'NO');
    console.log('=== PAYOUT VERIFICATION COMPLETE ===');
  } else {
    console.log('\n❌ Expected 1 payout, got:', payouts.length);
  }
  
  console.log('\n=== Test Complete ===');
}

main().catch(console.error);
