const { createClient, chains } = require('genlayer-js');
const { privateKeyToAccount } = require('viem/accounts');

const CONTRACT = '0x8E2F4557dA23B9306418f4A1C5F5A813Bee6d758';
const AGENT_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';

async function main() {
  const agentAccount = privateKeyToAccount(AGENT_KEY);
  const agentClient = createClient({ chain: chains.testnetBradbury, account: agentAccount });
  
  console.log('Agent address:', agentAccount.address);
  
  const balanceBefore = await agentClient.getBalance({ address: agentAccount.address });
  console.log('Balance before:', balanceBefore.toString(), 'wei =', Number(balanceBefore) / 1e18, 'GEN');
  
  // Try verifyDelivery with a simpler URL
  console.log('\n--- Verify Delivery (task-2) with httpbin.org ---');
  try {
    const tx = await agentClient.writeContract({
      address: CONTRACT,
      functionName: 'verifyDelivery',
      args: ['task-2'],
    });
    console.log('Tx hash:', tx);
  } catch (err) {
    console.log('Error:', err.message);
  }
  
  // Wait
  console.log('\nWaiting 60 seconds...');
  await new Promise(r => setTimeout(r, 60000));
  
  // Check task status
  const task = await agentClient.readContract({
    address: CONTRACT,
    functionName: 'getTask',
    args: ['task-2'],
  });
  console.log('Task status:', task);
  
  // Check emitted transfers
  const transfers = await agentClient.readContract({
    address: CONTRACT,
    functionName: 'getEmittedTransfers',
    args: [],
  });
  console.log('Emitted transfers:', transfers);
  
  const balanceAfter = await agentClient.getBalance({ address: agentAccount.address });
  console.log('\nBalance after:', balanceAfter.toString(), 'wei =', Number(balanceAfter) / 1e18, 'GEN');
  console.log('Delta:', (balanceAfter - balanceBefore).toString(), 'wei');
  
  console.log('\n=== Test Complete ===');
}

main().catch(console.error);
