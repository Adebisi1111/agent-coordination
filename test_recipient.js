const { createClient, chains } = require('genlayer-js');
const { privateKeyToAccount } = require('viem/accounts');

const CONTRACT = '0x8E2F4557dA23B9306418f4A1C5F5A813Bee6d758';
const POSTER_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';

async function main() {
  const posterAccount = privateKeyToAccount(POSTER_KEY);
  const posterClient = createClient({ chain: chains.testnetBradbury, account: posterAccount });
  
  console.log('Poster address:', posterAccount.address);
  
  const balanceBefore = await posterClient.getBalance({ address: posterAccount.address });
  console.log('Balance before:', balanceBefore.toString(), 'wei =', Number(balanceBefore) / 1e18, 'GEN');
  
  // Post task with 0.2 GEN reward
  console.log('\n--- Post Task (0.2 GEN) ---');
  try {
    const tx = await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'postTask',
      args: ['Write about AI safety', ''],
      value: 200000000000000000n,
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
  console.log('Task count:', taskCount);
  
  const taskId = `task-${JSON.parse(taskCount).count}`;
  console.log('Task ID:', taskId);
  
  // Check task
  const task = await posterClient.readContract({
    address: CONTRACT,
    functionName: 'getTask',
    args: [taskId],
  });
  console.log('Task:', task);
  
  const balanceAfter = await posterClient.getBalance({ address: posterAccount.address });
  console.log('Balance after:', balanceAfter.toString(), 'wei =', Number(balanceAfter) / 1e18, 'GEN');
  console.log('Delta:', (balanceAfter - balanceBefore).toString(), 'wei');
  
  console.log('\n=== Test Complete ===');
}

main().catch(console.error);
