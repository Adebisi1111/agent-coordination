import { createClient, chains } from 'genlayer-js';

const CONTRACT = '0x7B04E8a1b7759166150bcC34b3095f17296bfC89';

const client = createClient({ chain: chains.testnetBradbury });

async function main() {
  console.log('=== Full State Verification ===');

  // Check all tasks
  const countRaw = await client.readContract({ address: CONTRACT, functionName: 'getClaimCount', args: [] });
  const count = JSON.parse(countRaw);
  console.log('Task count:', count.count);

  for (let i = 1; i <= count.count; i++) {
    const task = await client.readContract({ address: CONTRACT, functionName: 'getTask', args: [`task-${i}`] });
    console.log(`Task ${i}:`, task);
  }

  // Check agent
  const agent = await client.readContract({
    address: CONTRACT,
    functionName: 'getAgent',
    args: ['0x61fd0047595A30A067f1F21F3b28C4AE8A8e3Dc3']
  });
  console.log('Agent:', agent);

  // Check emitted transfers
  const transfers = await client.readContract({ address: CONTRACT, functionName: 'getEmittedTransfers', args: [] });
  console.log('Emitted transfers:', transfers);

  // Check expected balance
  const balance = await client.readContract({
    address: CONTRACT,
    functionName: 'getExpectedBalance',
    args: ['0x61fd0047595A30A067f1F21F3b28C4AE8A8e3Dc3']
  });
  console.log('Expected balance:', balance);

  console.log('\n=== Done ===');
}

main().catch(console.error);
