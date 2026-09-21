import { createClient, createAccount, chains } from 'genlayer-js';

const CONTRACT = '0x471CFDa12A5C1a75279FC65a506beD210c6415d2';

// Poster (main wallet)
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = createAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.testnetBradbury, account: poster });

// Agent (fixed private key)
const AGENT_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const agent = createAccount(AGENT_KEY);
const agentClient = createClient({ chain: chains.testnetBradbury, account: agent });

async function retry(fn, name, maxAttempts = 5) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      return await fn();
    } catch (e) {
      const msg = e.message || '';
      if (msg.includes('rate limit') || msg.includes('-32005')) {
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
  console.log('=== END-TO-END PAYOUT/REFUND TEST (BRADBURY) ===');
  console.log('Contract:', CONTRACT);
  console.log('Poster:', poster.address);
  console.log('Agent:', agent.address);

  // Balances BEFORE
  const posterBefore = await posterClient.getBalance({ address: poster.address });
  const agentBefore = await agentClient.getBalance({ address: agent.address });
  console.log('\n--- Balances BEFORE ---');
  console.log('Poster:', posterBefore.toString(), 'wei');
  console.log('Agent:', agentBefore.toString(), 'wei');

  // === TEST 1: Payout ===
  console.log('\n--- TEST 1: PAYOUT (Approve Delivery) ---');
  
  // Post task
  console.log('1. Posting task with 0.01 GEN reward...');
  const postHash = await retry(() => posterClient.writeContract({
    address: CONTRACT,
    functionName: 'postTask',
    args: ['Write a blog post about AI safety'],
    value: 10000000000000000n,  // 0.01 GEN
  }), 'postTask');
  console.log('   Post tx:', postHash);

  // Agent claims
  console.log('2. Agent claiming task...');
  const claimHash = await retry(() => agentClient.writeContract({
    address: CONTRACT,
    functionName: 'claimTask',
    args: ['task-1'],
    value: 0n,
  }), 'claimTask');
  console.log('   Claim tx:', claimHash);

  // Agent delivers
  console.log('3. Agent submitting delivery...');
  const submitHash = await retry(() => agentClient.writeContract({
    address: CONTRACT,
    functionName: 'submitDelivery',
    args: ['task-1', 'https://en.wikipedia.org/wiki/Artificial_intelligence'],
    value: 0n,
  }), 'submitDelivery');
  console.log('   Submit tx:', submitHash);

  // Agent balance BEFORE approval
  const agentBalanceBefore = await agentClient.getBalance({ address: agent.address });
  console.log('4. Agent balance BEFORE approval:', agentBalanceBefore.toString(), 'wei');

  // Approve delivery (triggers payout)
  console.log('5. Approving delivery (triggers payout)...');
  const approveHash = await retry(() => posterClient.writeContract({
    address: CONTRACT,
    functionName: 'approveDelivery',
    args: ['task-1'],
    value: 0n,
  }), 'approveDelivery');
  console.log('   Approve tx:', approveHash);

  // Wait for finalization
  console.log('6. Waiting for finalization...');
  await new Promise(r => setTimeout(r, 60000));

  // Agent balance AFTER approval
  const agentBalanceAfter = await agentClient.getBalance({ address: agent.address });
  console.log('7. Agent balance AFTER approval:', agentBalanceAfter.toString(), 'wei');

  const agentDelta = agentBalanceAfter - agentBalanceBefore;
  console.log('   Agent balance change:', agentDelta.toString(), 'wei');

  // Verify payout
  if (agentDelta >= 10000000000000000n) {
    console.log('   ✅ PAYOUT VERIFIED: Agent received at least 0.01 GEN');
  } else {
    console.log('   ❌ PAYOUT FAILED: Agent did not receive expected amount');
    process.exit(1);
  }

  // === TEST 2: Refund ===
  console.log('\n--- TEST 2: REFUND (Cancel Task) ---');
  
  // Post another task
  console.log('1. Posting second task with 0.01 GEN reward...');
  const postHash2 = await retry(() => posterClient.writeContract({
    address: CONTRACT,
    functionName: 'postTask',
    args: ['Write about blockchain'],
    value: 10000000000000000n,
  }), 'postTask2');
  console.log('   Post tx:', postHash2);

  // Poster balance BEFORE cancel
  const posterBalanceBefore = await posterClient.getBalance({ address: poster.address });
  console.log('2. Poster balance BEFORE cancel:', posterBalanceBefore.toString(), 'wei');

  // Cancel task
  console.log('3. Cancelling task (triggers refund)...');
  const cancelHash = await retry(() => posterClient.writeContract({
    address: CONTRACT,
    functionName: 'cancelTask',
    args: ['task-2'],
    value: 0n,
  }), 'cancelTask');
  console.log('   Cancel tx:', cancelHash);

  // Wait for finalization
  console.log('4. Waiting for finalization...');
  await new Promise(r => setTimeout(r, 60000));

  // Poster balance AFTER cancel
  const posterBalanceAfter = await posterClient.getBalance({ address: poster.address });
  console.log('5. Poster balance AFTER cancel:', posterBalanceAfter.toString(), 'wei');

  const posterDelta = posterBalanceAfter - posterBalanceBefore;
  console.log('   Poster balance change:', posterDelta.toString(), 'wei');

  // Verify refund
  if (posterDelta >= 10000000000000000n) {
    console.log('   ✅ REFUND VERIFIED: Poster received at least 0.01 GEN back');
  } else {
    console.log('   ❌ REFUND FAILED: Poster did not receive expected refund');
    process.exit(1);
  }

  // === FINAL RESULTS ===
  console.log('\n=== FINAL RESULTS ===');
  console.log('Agent balance change (payout):', agentDelta.toString(), 'wei');
  console.log('Poster balance change (refund):', posterDelta.toString(), 'wei');
  console.log('✅ BOTH PAYOUT AND REFUND VERIFIED');
}

main().catch(e => {
  console.error('ERROR:', e);
  process.exit(1);
});
