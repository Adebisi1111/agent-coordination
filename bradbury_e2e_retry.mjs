import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';
import { setTimeout } from 'timers/promises';

const CONTRACT = '0x471CFDa12A5C1a75279FC65a506beD210c6415d2';

// Poster (main wallet)
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.testnetBradbury, account: poster });

// Agent (fixed private key)
const AGENT_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const agent = privateKeyToAccount(AGENT_KEY);
const agentClient = createClient({ chain: chains.testnetBradbury, account: agent });

// Mochi's retry helper: exponential backoff with jitter
async function retry(fn, name = 'rpc', maxAttempts = 8, baseDelayMs = 500) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err) {
      const code = err?.code || err?.cause?.code;
      const msg = err?.message || '';
      const isRateLimit = code === -32005 || msg.includes('rate limit') || msg.includes('node is capacity');
      
      if (!isRateLimit || attempt === maxAttempts) {
        throw err;
      }
      
      const jitter = Math.random() * 200;
      const delay = baseDelayMs * Math.pow(2, attempt - 1) + jitter;
      console.warn(`   ⚠️ ${name}: rate limited, retry ${attempt}/${maxAttempts} in ${Math.round(delay)}ms`);
      await setTimeout(delay);
    }
  }
  throw new Error(`${name}: retry loop exhausted`);
}

async function main() {
  console.log('=== END-TO-END PAYOUT TEST (BRADBURY) ===');
  console.log('Contract:', CONTRACT);
  console.log('Poster:', poster.address);
  console.log('Agent:', agent.address);

  // Balances BEFORE
  const posterBefore = await posterClient.getBalance({ address: poster.address });
  const agentBefore = await agentClient.getBalance({ address: agent.address });
  console.log('\n--- Balances BEFORE ---');
  console.log('Poster:', posterBefore.toString(), 'wei');
  console.log('Agent:', agentBefore.toString(), 'wei');

  // 1. Post task
  console.log('\n1. Posting task with 0.5 GEN reward...');
  const postHash = await retry(() => posterClient.writeContract({
    address: CONTRACT,
    functionName: 'postTask',
    args: ['Write a blog post about AI safety'],
    value: 500000000000000000n,
  }), 'postTask');
  console.log('   Post tx:', postHash);

  // 2. Agent claims
  console.log('2. Agent claiming task...');
  const claimHash = await retry(() => agentClient.writeContract({
    address: CONTRACT,
    functionName: 'claimTask',
    args: ['task-1'],
    value: 0n,
  }), 'claimTask');
  console.log('   Claim tx:', claimHash);

  // 3. Agent submits delivery
  console.log('3. Agent submitting delivery...');
  const submitHash = await retry(() => agentClient.writeContract({
    address: CONTRACT,
    functionName: 'submitDelivery',
    args: ['task-1', 'https://en.wikipedia.org/wiki/Artificial_intelligence'],
    value: 0n,
  }), 'submitDelivery');
  console.log('   Submit tx:', submitHash);

  // 4. Verify delivery (triggers AI consensus + payout)
  console.log('4. Verifying delivery (AI consensus)...');
  const verifyHash = await retry(() => posterClient.writeContract({
    address: CONTRACT,
    functionName: 'verifyDelivery',
    args: ['task-1'],
    value: 0n,
  }), 'verifyDelivery');
  console.log('   Verify tx:', verifyHash);

  // Wait for finalization
  console.log('\nWaiting for finalization...');
  let result = null;
  for (let i = 0; i < 60; i++) {
    await setTimeout(10000);
    const task = await posterClient.readContract({ address: CONTRACT, functionName: 'getTask', args: ['task-1'] });
    const parsed = JSON.parse(task.data || task);
    if (parsed.status === 'VERIFIED' || parsed.status === 'REFUNDED') {
      result = parsed;
      console.log('   Finalized! Status:', parsed.status);
      break;
    }
    process.stdout.write('.');
  }

  // Balances AFTER
  const posterAfter = await posterClient.getBalance({ address: poster.address });
  const agentAfter = await agentClient.getBalance({ address: agent.address });
  console.log('\n--- Balances AFTER ---');
  console.log('Poster:', posterAfter.toString(), 'wei');
  console.log('Agent:', agentAfter.toString(), 'wei');

  const posterDelta = posterAfter - posterBefore;
  const agentDelta = agentAfter - agentBefore;

  console.log('\n--- Balance Changes ---');
  console.log('Poster delta:', posterDelta.toString(), 'wei');
  console.log('Agent delta:', agentDelta.toString(), 'wei');

  // Transfers
  const transfers = await posterClient.readContract({ address: CONTRACT, functionName: 'getEmittedTransfers', args: [] });
  console.log('\nEmitted Transfers:', transfers);

  console.log('\n=== RESULT ===');
  if (result) {
    console.log('Task status:', result.status);
    console.log('Agent balance change:', agentDelta.toString(), 'wei');
    console.log('Poster balance change:', posterDelta.toString(), 'wei');
  } else {
    console.log('Consensus not yet finalized');
  }
}

main().catch(console.error);
