import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

// Studio Network
const CONTRACT = '0x50BD0a5C0AF880c5DC5DDbc899F8B6E2e7Af48a1';

// Poster (main wallet)
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.studionet, account: poster });

// Agent (fixed private key)
const AGENT_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const agent = privateKeyToAccount(AGENT_KEY);
const agentClient = createClient({ chain: chains.studionet, account: agent });

async function wait(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log('=== STUDIO NETWORK - FULL PAYOUT TEST ===');
  console.log('Contract:', CONTRACT);
  console.log('Poster:', poster.address);
  console.log('Agent:', agent.address);

  const posterBefore = await posterClient.getBalance({ address: poster.address });
  const agentBefore = await posterClient.getBalance({ address: agent.address });
  console.log('\nPoster before:', posterBefore.toString(), 'wei');
  console.log('Agent before:', agentBefore.toString(), 'wei');

  // 1. Agent registers
  console.log('\n1. Registering agent...');
  await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'registerAgent',
    args: ['writing,coding,research', ''],
    value: 2000000000000000000n,
  });
  console.log('   Done');
  await wait(3000);

  // 2. Post task with 0.5 GEN reward
  console.log('\n2. Posting task...');
  await posterClient.writeContract({
    address: CONTRACT,
    functionName: 'postTask',
    args: ['Write a blog post about AI safety', ''],
    value: 500000000000000000n,
  });
  console.log('   Done');
  await wait(3000);

  // 3. Agent claims task
  console.log('\n3. Claiming task...');
  await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'claimTask',
    args: ['task-2'],
    value: 0n,
  });
  console.log('   Done');
  await wait(3000);

  // 4. Agent submits delivery (Wikipedia about AI safety - should PASS)
  console.log('\n4. Submitting delivery...');
  await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'submitDelivery',
    args: ['task-2', 'https://en.wikipedia.org/wiki/AI_safety'],
    value: 0n,
  });
  console.log('   Done');
  await wait(3000);

  // 5. Verify delivery (triggers AI consensus)
  console.log('\n5. Verifying delivery (AI consensus)...');
  await posterClient.writeContract({
    address: CONTRACT,
    functionName: 'verifyDelivery',
    args: ['task-2'],
    value: 0n,
  });
  console.log('   Done');

  // Wait for finalization
  console.log('\nWaiting for finalization...');
  let result = null;
  for (let i = 0; i < 30; i++) {
    await wait(10000);
    try {
      const task = await posterClient.readContract({ address: CONTRACT, functionName: 'getTask', args: ['task-2'] });
      const parsed = JSON.parse(task.data || task);
      if (parsed.status === 'VERIFIED' || parsed.status === 'REFUNDED') {
        result = parsed;
        console.log('   Finalized! Status:', parsed.status);
        break;
      }
      process.stdout.write('.');
    } catch (e) {
      process.stdout.write('x');
    }
  }

  // Wait additional time for external transfer to finalize
  console.log('\nWaiting for external transfer to finalize...');
  await wait(60000);

  // Final balances
  const posterAfter = await posterClient.getBalance({ address: poster.address });
  const agentAfter = await posterClient.getBalance({ address: agent.address });

  console.log('\n--- BALANCE CHANGES ---');
  console.log('Poster delta:', (posterAfter - posterBefore).toString(), 'wei');
  console.log('Agent delta:', (agentAfter - agentBefore).toString(), 'wei');

  // Check emitted transfers
  const transfers = await posterClient.readContract({ address: CONTRACT, functionName: 'getEmittedTransfers', args: [] });
  console.log('\nEmitted Transfers:', transfers);

  const externalLog = await posterClient.readContract({ address: CONTRACT, functionName: 'getExternalTransferLog', args: [] });
  console.log('External Transfer Log:', externalLog);

  const task = await posterClient.readContract({ address: CONTRACT, functionName: 'getTask', args: ['task-2'] });
  console.log('\nFinal task status:', task);

  console.log('\n=== RESULT ===');
  if (result) {
    console.log('Task status:', result.status);
    console.log('Agent balance change:', (agentAfter - agentBefore).toString(), 'wei');
    console.log('Poster balance change:', (posterAfter - posterBefore).toString(), 'wei');
    if (result.status === 'VERIFIED' && agentAfter > agentBefore) {
      console.log('✅ PAYOUT VERIFIED: Agent received reward');
    } else if (result.status === 'VERIFIED') {
      console.log('⏳ PAYOUT PENDING: External transfer not yet finalized');
    }
  }
}

main().catch(console.error);
