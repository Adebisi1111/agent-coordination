import { createClient, chains } from 'genlayer-js';

const CONTRACT = '0x7B04E8a1b7759166150bcC34b3095f17296bfC89';
const USER_ADDR = '0x61fd0047595A30A067f1F21F3b28C4AE8A8e3Dc3';

const client = createClient({ chain: chains.testnetBradbury });

async function main() {
  console.log('=== Deep Verification (Fixed) ===');

  // 1. TreeMap write/read verification
  console.log('\n1. TreeMap write/read...');
  const balanceRaw = await client.readContract({ address: CONTRACT, functionName: 'getExpectedBalance', args: [USER_ADDR] });
  console.log('   Raw:', balanceRaw);
  console.log('   Expected: -1000000000000000000');
  console.log('   Match:', balanceRaw === '-1000000000000000000' ? 'PASS' : 'FAIL');

  // 2. TreeMap iteration verification
  console.log('\n2. TreeMap iteration...');
  const transfersRaw = await client.readContract({ address: CONTRACT, functionName: 'getEmittedTransfers', args: [] });
  console.log('   Raw:', transfersRaw);
  console.log('   Type:', typeof transfersRaw);
  const transfers = JSON.parse(transfersRaw);
  console.log('   Parsed:', transfers);
  console.log('   Is empty:', Object.keys(transfers).length === 0);

  // 3. Task state after verify tx
  console.log('\n3. Task state after verify tx...');
  const taskRaw = await client.readContract({ address: CONTRACT, functionName: 'getTask', args: ['task-1'] });
  console.log('   Raw:', taskRaw);
  const task = JSON.parse(taskRaw);
  console.log('   Status:', task.status);
  console.log('   Verification:', task.verification);
  console.log('   Assignee:', task.assignee);

  // 4. Agent state
  console.log('\n4. Agent state...');
  const agentRaw = await client.readContract({ address: CONTRACT, functionName: 'getAgent', args: [USER_ADDR] });
  console.log('   Raw:', agentRaw);
  const agent = JSON.parse(agentRaw);
  console.log('   Exists:', agent.exists);
  console.log('   Stake:', agent.stake);
  console.log('   Reputation:', agent.reputation);
  console.log('   Active:', agent.active);

  // 5. Wallet balance
  console.log('\n5. Wallet balance...');
  const walletBalance = await client.getBalance({ address: USER_ADDR });
  console.log('   Balance:', Number(walletBalance) / 1e18, 'GEN');

  // 6. Replay test
  console.log('\n6. Replay test...');
  console.log('   Task status:', task.status);
  console.log('   Can verifyDelivery be called again?', task.status === 'DELIVERED' ? 'YES (BUG)' : 'NO (blocked)');

  console.log('\n=== Verification Complete ===');
}

main().catch(console.error);
