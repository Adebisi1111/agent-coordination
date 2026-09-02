import { createClient, chains } from 'genlayer-js';

const CONTRACT = '0x7B04E8a1b7759166150bcC34b3095f17296bfC89';
const USER_ADDR = '0x61fd0047595A30A067f1F21F3b28C4AE8A8e3Dc3';

const client = createClient({ chain: chains.testnetBradbury });

async function main() {
  console.log('=== Verification Pass ===');

  // 1. Check TreeMap operations work (postTask already tested this)
  console.log('\n1. TreeMap read/write via getExpectedBalance...');
  const balance = await client.readContract({ address: CONTRACT, functionName: 'getExpectedBalance', args: [USER_ADDR] });
  console.log('   Expected balance:', balance, '(should be -1000000000000000000 from postTask)');

  // 2. Check TreeMap iteration works
  console.log('\n2. TreeMap iteration via getEmittedTransfers...');
  const transfers = await client.readContract({ address: CONTRACT, functionName: 'getEmittedTransfers', args: [] });
  console.log('   Transfers:', transfers, '(empty = no payouts yet)');

  // 3. Check task state after verify tx
  console.log('\n3. Task state after verify tx...');
  const task = await client.readContract({ address: CONTRACT, functionName: 'getTask', args: ['task-1'] });
  console.log('   Task:', task);
  console.log('   Status:', task.status, '| Verification:', task.verification);

  // 4. Check agent state
  console.log('\n4. Agent state...');
  const agent = await client.readContract({ address: CONTRACT, functionName: 'getAgent', args: [USER_ADDR] });
  console.log('   Agent:', agent);

  // 5. Check wallet balance (real value transfer test)
  console.log('\n5. Wallet balance...');
  const walletBalance = await client.getBalance({ address: USER_ADDR });
  console.log('   Balance:', walletBalance.toString(), '(', Number(walletBalance) / 1e18, 'GEN)');

  console.log('\n=== Verification Complete ===');
}

main().catch(console.error);
