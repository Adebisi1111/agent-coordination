import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const CONTRACT = '0x471CFDa12A5C1a75279FC65a506beD210c6415d2';

// Poster (main wallet)
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.testnetBradbury, account: poster });

// Agent (fixed private key)
const AGENT_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const agent = privateKeyToAccount(AGENT_KEY);
const agentClient = createClient({ chain: chains.testnetBradbury, account: agent });

async function retry(fn, name, maxAttempts = 5) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      return await fn();
    } catch (e) {
      const msg = e.message || '';
      if (msg.includes('rate limit') || msg.includes('-32005') || msg.includes('at capacity')) {
        const wait = (i + 1) * 3000;
        console.log(`   ⚠️ ${name}: rate limited, waiting ${wait}ms...`);
        await new Promise(r => setTimeout(r, wait));
        continue;
      }
      throw e;
    }
  }
  throw new Error(`${name}: too many retries`);
}

async function main() {
  console.log('=== FULL PAYOUT TEST ===');
  
  // Check task count
  const count = await posterClient.readContract({ address: CONTRACT, functionName: 'getClaimCount', args: [] });
  console.log('Task count:', count);
  
  const posterBefore = await posterClient.getBalance({ address: poster.address });
  const agentBefore = await agentClient.getBalance({ address: agent.address });
  console.log('Poster before:', posterBefore.toString(), 'wei');
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

  // 2. Post task
  console.log('\n2. Posting task...');
  const postResult = await retry(() => posterClient.writeContract({
    address: CONTRACT,
    functionName: 'postTask',
    args: ['Write a blog post about AI safety', ''],
    value: 500000000000000000n,
  }), 'postTask');
  console.log('   Post tx:', postResult);

  // Get task ID from result
  const taskId = postResult || 'task-1';
  console.log('   Task ID:', taskId);

  // 3. Claim task
  console.log('\n3. Claiming task...');
  await retry(() => agentClient.writeContract({
    address: CONTRACT,
    functionName: 'claimTask',
    args: [taskId],
    value: 0n,
  }), 'claimTask');
  console.log('   Done');

  // 4. Submit delivery
  console.log('\n4. Submitting delivery...');
  await retry(() => agentClient.writeContract({
    address: CONTRACT,
    functionName: 'submitDelivery',
    args: [taskId, 'https://en.wikipedia.org/wiki/Artificial_intelligence'],
    value: 0n,
  }), 'submitDelivery');
  console.log('   Done');

  // 5. Verify delivery
  console.log('\n5. Verifying delivery...');
  await retry(() => posterClient.writeContract({
    address: CONTRACT,
    functionName: 'verifyDelivery',
    args: [taskId],
    value: 0n,
  }), 'verifyDelivery');
  console.log('   Done');

  // Wait for finalization
  console.log('\nWaiting...');
  for (let i = 0; i < 30; i++) {
    await new Promise(r => setTimeout(r, 10000));
    const task = await posterClient.readContract({ address: CONTRACT, functionName: 'getTask', args: [taskId] });
    const parsed = JSON.parse(task.data || task);
    if (parsed.status === 'VERIFIED' || parsed.status === 'REFUNDED') {
      console.log('   Finalized! Status:', parsed.status);
      break;
    }
    process.stdout.write('.');
  }

  // Final balances
  const posterAfter = await posterClient.getBalance({ address: poster.address });
  const agentAfter = await agentClient.getBalance({ address: agent.address });
  console.log('\n--- RESULT ---');
  console.log('Poster delta:', (posterAfter - posterBefore).toString(), 'wei');
  console.log('Agent delta:', (agentAfter - agentBefore).toString(), 'wei');
  
  const transfers = await posterClient.readContract({ address: CONTRACT, functionName: 'getEmittedTransfers', args: [] });
  console.log('Transfers:', transfers);
}

main().catch(console.error);
