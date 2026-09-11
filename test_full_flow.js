const { createClient, chains } = require('genlayer-js');
const { privateKeyToAccount } = require('viem/accounts');

const CONTRACT = '0xF17D5c8A7F379E611b9F51189F68434a8517BD08';
const POSTER_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';

async function main() {
  const posterAccount = privateKeyToAccount(POSTER_KEY);
  const posterClient = createClient({ chain: chains.testnetBradbury, account: posterAccount });
  
  console.log('Poster address:', posterAccount.address);
  
  const balanceBefore = await posterClient.getBalance({ address: posterAccount.address });
  console.log('Balance before:', balanceBefore.toString(), 'wei =', Number(balanceBefore) / 1e18, 'GEN');
  
  // Register agent with 0.01 GEN (above 0.001 min stake)
  console.log('\n--- Register Agent (0.01 GEN) ---');
  try {
    const tx = await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'registerAgent',
      args: ['writing', ''],
      value: 10000000000000000n,
    });
    console.log('Tx hash:', tx);
  } catch (err) {
    console.log('Error:', err.message);
  }
  
  // Wait
  console.log('\nWaiting 30 seconds...');
  await new Promise(r => setTimeout(r, 30000));
  
  // Post task with 0.01 GEN reward
  console.log('\n--- Post Task (0.01 GEN) ---');
  try {
    const tx = await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'postTask',
      args: ['Write about AI safety', ''],
      value: 10000000000000000n,
    });
    console.log('Tx hash:', tx);
  } catch (err) {
    console.log('Error:', err.message);
  }
  
  // Wait
  console.log('\nWaiting 30 seconds...');
  await new Promise(r => setTimeout(r, 30000));
  
  // Get task ID
  const taskCount = await posterClient.readContract({
    address: CONTRACT,
    functionName: 'getClaimCount',
    args: [],
  });
  const taskId = `task-${JSON.parse(taskCount).count}`;
  console.log('Task ID:', taskId);
  
  // Claim task
  console.log('\n--- Claim Task ---');
  try {
    const tx = await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'claimTask',
      args: [taskId],
    });
    console.log('Tx hash:', tx);
  } catch (err) {
    console.log('Error:', err.message);
  }
  
  // Wait
  console.log('\nWaiting 30 seconds...');
  await new Promise(r => setTimeout(r, 30000));
  
  // Submit delivery
  console.log('\n--- Submit Delivery ---');
  try {
    const tx = await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'submitDelivery',
      args: [taskId, 'https://example.com/ai-safety'],
    });
    console.log('Tx hash:', tx);
  } catch (err) {
    console.log('Error:', err.message);
  }
  
  // Wait
  console.log('\nWaiting 30 seconds...');
  await new Promise(r => setTimeout(r, 30000));
  
  // Approve delivery (direct approval, no AI)
  console.log('\n--- Approve Delivery ---');
  try {
    const tx = await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'approveDelivery',
      args: [taskId],
    });
    console.log('Tx hash:', tx);
  } catch (err) {
    console.log('Error:', err.message);
  }
  
  // Wait
  console.log('\nWaiting 30 seconds...');
  await new Promise(r => setTimeout(r, 30000));
  
  // Check emitted transfers
  const transfers = await posterClient.readContract({
    address: CONTRACT,
    functionName: 'getEmittedTransfers',
    args: [],
  });
  console.log('\nEmitted transfers:', transfers);
  
  // Check balance delta
  const balanceAfter = await posterClient.getBalance({ address: posterAccount.address });
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
    console.log('Expected reward:', '10000000000000000', 'wei = 0.01 GEN');
    console.log('Amount match:', payout.amount.toString() === '10000000000000000');
    console.log('Recipient:', payout.to);
    console.log('Expected recipient:', posterAccount.address);
    console.log('Recipient match:', payout.to.toLowerCase() === posterAccount.address.toLowerCase());
    console.log('Balance increased:', delta > 0 ? 'YES' : 'NO');
    console.log('=== PAYOUT VERIFICATION COMPLETE ===');
  } else {
    console.log('\n❌ Expected 1 payout, got:', payouts.length);
  }
  
  console.log('\n=== Test Complete ===');
}

main().catch(console.error);
