import { createClient, chains } from 'genlayer-js';

const CONTRACT = '0x7B04E8a1b7759166150bcC34b3095f17296bfC89';

const client = createClient({ chain: chains.testnetBradbury });

async function main() {
  console.log('=== Verify Contract State on Bradbury ===');

  // Check task count
  console.log('\n1. Task count...');
  const count = await client.readContract({ address: CONTRACT, functionName: 'getClaimCount', args: [] });
  console.log('Task count:', count);

  // Check task 1
  console.log('\n2. Task 1...');
  const task = await client.readContract({ address: CONTRACT, functionName: 'getTask', args: ['task-1'] });
  console.log('Task 1:', task);

  // Check agent
  console.log('\n3. Agent...');
  const agent = await client.readContract({ address: CONTRACT, functionName: 'getAgent', args: ['0x61fd0047595A30A067f1F21F3b28C4AE8A8e3Dc3'] });
  console.log('Agent:', agent);

  // Check emitted transfers
  console.log('\n4. Emitted transfers...');
  const transfers = await client.readContract({ address: CONTRACT, functionName: 'getEmittedTransfers', args: [] });
  console.log('Transfers:', transfers);

  // Check expected balance
  console.log('\n5. Expected balance...');
  const balance = await client.readContract({ address: CONTRACT, functionName: 'getExpectedBalance', args: ['0x61fd0047595A30A067f1F21F3b28C4AE8A8e3Dc3'] });
  console.log('Expected balance:', balance);

  console.log('\n=== Done ===');
}

main().catch(console.error);
