import { createClient, chains } from 'genlayer-js';

const CONTRACT = '0x7B04E8a1b7759166150bcC34b3095f17296bfC89';

const client = createClient({ chain: chains.testnetBradbury });

async function main() {
  const task = await client.readContract({
    address: CONTRACT,
    functionName: 'getTask',
    args: ['task-1'],
  });
  console.log('Task 1:', task);
}

main().catch(console.error);
