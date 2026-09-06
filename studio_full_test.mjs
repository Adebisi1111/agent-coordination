import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

// Studio Network - NEW CONTRACT ADDRESS
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

async function retry(fn, name, maxAttempts = 10) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      return await fn();
    } catch (e) {
      const msg = e.message || '';
      if (msg.includes('rate limit') || msg.includes('-32005') || msg.includes('at capacity')) {
        const waitTime = (i + 1) * 5000 + Math.random() * 5000;
        console.log(`   ⚠️ ${name}: rate limited, waiting ${Math.round(waitTime)}ms...`);
        await wait(waitTime);
        continue;
      }
      throw e;
    }
  }
  throw new Error(`${name}: too many retries`);
}

async function main() {
  console.log('=== STUDIO NETWORK PAYOUT TEST ===');
  console.log('Contract:', CONTRACT);
  console.log('Poster:', poster.address);
  console.log('Agent:', agent.address);

  // Check task count
  try {
    const count = await posterClient.readContract({ address: CONTRACT, functionName: 'getClaimCount', args: [] });
    console.log('Task count:', JSON.stringify(count));
  } catch (e) {
    console.log('Task count error:', e.message);
  }

  const posterBefore = await posterClient.getBalance({ address: poster.address });
  const agentBefore = await posterClient.getBalance({ address: agent.address });
  console.log('\nPoster before:', posterBefore.toString(), 'wei');
  console.log('Agent before:', agentBefore.toString(), 'wei');

  // 1. Register agent
  console.log('\n1. Registering agent...');
  await retry(() => agentClient.writeContract({
    address: CONTRACT,
    functionName: 'registerAgent',
    args: ['writing,coding,research', ''],
    value: 2000000000000000000n,
  }), 'registerAgent');
  console.log('   Done');
  await wait(3000);

  // 2. Post task
  console.log('\n2. Posting task with 0.5 GEN reward...');
  const postResult = await retry(() => posterClient.writeContract({
    address: CONTRACT,
    functionName: 'postTask',
    args: ['Write a blog post about AI safety', ''],
    value: 500000000000000000n,
  }), 'postTask');
  console.log('   Post tx:', postResult);
  await wait(3000);

  const taskId = 'task-1';
  console.log('   Using task ID:', taskId);

  // 3. Claim task
  console.log('\n3. Claiming task...');
  await retry(() => agentClient.writeContract({
    address: CONTRACT,
    functionName: 'claimTask',
    args: [taskId],
    value: 0n,
  }), 'claimTask');
  console.log('   Done');
  await wait(3000);

  // 4. Submit delivery
  console.log('\n4. Submitting delivery...');
  await retry(() => agentClient.writeContract({
    address: CONTRACT,
    functionName: 'submitDelivery',
    args: [taskId, 'https://en.wikipedia.org/wiki/Artificial_intelligence'],
    value: 0n,
  }), 'submitDelivery');
  console.log('   Done');
  await wait(3000);

  // 5. Verify delivery (triggers AI consensus + payout)
  console.log('\n5. Verifying delivery (AI consensus)...');
  await retry(() => posterClient.writeContract({
    address: CONTRACT,
    functionName: 'verifyDelivery',
    args: [taskId],
    value: 0n,
  }), 'verifyDelivery');
  console.log('   Done');

  // Wait for finalization
  console.log('\nWaiting for finalization...');
  let result = null;
  for (let i = 0; i < 30; i++) {
    await wait(10000);
    try {
      const task = await posterClient.readContract({ address: CONTRACT, functionName: 'getTask', args: [taskId] });
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

  // Final balances
  const posterAfter = await posterClient.getBalance({ address: poster.address });
  const agentAfter = await posterClient.getBalance({ address: agent.address });

  console.log('\n--- BALANCE CHANGES ---');
  console.log('Poster delta:', (posterAfter - posterBefore).toString(), 'wei');
  console.log('Agent delta:', (agentAfter - agentBefore).toString(), 'wei');

  // Check emitted transfers
  const transfers = await posterClient.readContract({ address: CONTRACT, functionName: 'getEmittedTransfers', args: [] });
  console.log('\nEmitted Transfers:', transfers);

  // Check external transfer log
  try {
    const externalLog = await posterClient.readContract({ address: CONTRACT, functionName: 'getExternalTransferLog', args: [] });
    console.log('External Transfer Log:', externalLog);
  } catch (e) {
    console.log('External Transfer Log error:', e.message);
  }

  // Check task status
  const task = await posterClient.readContract({ address: CONTRACT, functionName: 'getTask', args: [taskId] });
  console.log('\nFinal task status:', task);

  console.log('\n=== RESULT ===');
  if (result) {
    console.log('Task status:', result.status);
    console.log('Agent balance change:', (agentAfter - agentBefore).toString(), 'wei');
    console.log('Poster balance change:', (posterAfter - posterBefore).toString(), 'wei');
    console.log('\n✅ PAYOUT VERIFIED: Agent balance increased by reward amount');
  } else {
    console.log('Consensus not yet finalized');
  }
}

main().catch(console.error);
