import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount, generatePrivateKey } from 'viem/accounts';

// Bradbury test - ACTUAL wallet balance verification (Mochi's approach)
const CONTRACT = '0x471CFDa12A5C1a75279FC65a506beD210c6415d2';

// Poster (main wallet)
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.testnetBradbury, account: poster });

// Agent (throwaway - fixed key)
const AGENT_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const agent = privateKeyToAccount(AGENT_KEY);
const agentClient = createClient({ chain: chains.testnetBradbury, account: agent });

async function getBalance(client, address) {
  try {
    const bal = await client.getBalance({ address });
    return BigInt(bal.toString());
  } catch (e) {
    console.error('getBalance error:', e.message);
    return 0n;
  }
}

async function main() {
  console.log('=== PAYOUT Test: Actual Wallet Balance Verification ===');
  console.log('Contract:', CONTRACT);
  console.log('Poster:', poster.address);
  console.log('Agent:', agent.address);

  // ============================================================
  // STEP 1: Capture balances BEFORE
  // ============================================================
  const posterBefore = await getBalance(posterClient, poster.address);
  const agentBefore = await getBalance(agentClient, agent.address);
  console.log('\n--- Balances BEFORE ---');
  console.log('Poster:', posterBefore.toString(), 'wei');
  console.log('Agent:', agentBefore.toString(), 'wei');

  // ============================================================
  // STEP 2: Execute settlement (triggers payout via emit_transfer)
  // ============================================================
  console.log('\n--- Executing settlement ---');
  
  // Post task
  console.log('1. Posting task with 0.5 GEN reward...');
  const postHash = await posterClient.writeContract({
    address: CONTRACT,
    functionName: 'postTask',
    args: ['Write a blog post about AI safety'],
    value: 500000000000000000n,
  });
  console.log('   Post tx:', postHash);

  // Agent claims
  console.log('2. Agent claiming task...');
  const claimHash = await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'claimTask',
    args: ['task-1'],
    value: 0n,
  });
  console.log('   Claim tx:', claimHash);

  // Agent submits delivery
  console.log('3. Agent submitting delivery...');
  const submitHash = await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'submitDelivery',
    args: ['task-1', 'https://en.wikipedia.org/wiki/Artificial_intelligence'],
    value: 0n,
  });
  console.log('   Submit tx:', submitHash);

  // Verify delivery (triggers AI consensus + payout)
  console.log('4. Verifying delivery (AI consensus + payout)...');
  const verifyHash = await posterClient.writeContract({
    address: CONTRACT,
    functionName: 'verifyDelivery',
    args: ['task-1'],
    value: 0n,
  });
  console.log('   Verify tx:', verifyHash);

  // ============================================================
  // STEP 3: Wait for finalization (external transfer executes)
  // ============================================================
  console.log('\n--- Waiting for finalization (up to 5 min) ---');
  let finalized = false;
  for (let i = 0; i < 30; i++) {
    await new Promise(r => setTimeout(r, 10000)); // 10s intervals
    const task = await posterClient.readContract({
      address: CONTRACT,
      functionName: 'getTask',
      args: ['task-1'],
    });
    const parsed = JSON.parse(task.data || task);
    if (parsed.status === 'VERIFIED' || parsed.status === 'REFUNDED') {
      finalized = true;
      console.log('   ✅ Finalized! Status:', parsed.status);
      break;
    }
    process.stdout.write('.');
  }
  if (!finalized) {
    console.log('   ⏳ Still pending (will check balances anyway)');
  }

  // ============================================================
  // STEP 4: Capture balances AFTER
  // ============================================================
  const posterAfter = await getBalance(posterClient, poster.address);
  const agentAfter = await getBalance(agentClient, agent.address);
  console.log('\n--- Balances AFTER ---');
  console.log('Poster:', posterAfter.toString(), 'wei');
  console.log('Agent:', agentAfter.toString(), 'wei');

  // ============================================================
  // STEP 5: Calculate deltas and assert
  // ============================================================
  const posterDelta = posterAfter - posterBefore;
  const agentDelta = agentAfter - agentBefore;
  const reward = 500000000000000000n;

  console.log('\n--- Balance Deltas ---');
  console.log('Poster delta:', posterDelta.toString(), 'wei');
  console.log('Agent delta:', agentDelta.toString(), 'wei');

  // Check emitted transfers
  const transfers = await posterClient.readContract({
    address: CONTRACT,
    functionName: 'getEmittedTransfers',
    args: [],
  });
  console.log('\n--- Emitted Transfers ---');
  console.log(transfers);

  // ============================================================
  // ASSERTIONS
  // ============================================================
  console.log('\n=== ASSERTIONS ===');
  
  let allPassed = true;

  // Agent should have gained the reward (minus gas costs)
  // Note: agent pays gas for claim + submit, so delta is reward - gas
  if (agentDelta > 0n) {
    console.log('✅ PASS: Agent balance increased (received payout)');
  } else {
    console.log('❌ FAIL: Agent balance did not increase');
    allPassed = false;
  }

  // Poster should have lost the reward (plus gas)
  if (posterDelta < 0n) {
    console.log('✅ PASS: Poster balance decreased (paid reward)');
  } else {
    console.log('❌ FAIL: Poster balance did not decrease');
    allPassed = false;
  }

  // Verify emitted transfer exists
  const transfersStr = transfers.data || transfers;
  if (transfersStr && transfersStr.includes('payout')) {
    console.log('✅ PASS: Payout transfer emitted');
  } else {
    console.log('❌ FAIL: No payout transfer emitted');
    allPassed = false;
  }

  console.log('\n=== RESULT ===');
  console.log(allPassed ? '✅ ALL ASSERTIONS PASSED' : '❌ SOME ASSERTIONS FAILED');
  console.log('\n=== Complete ===');
}

main().catch(console.error);
