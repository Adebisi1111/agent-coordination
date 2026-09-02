import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

// Studio test - dispute/refund balance verification
const CONTRACT = '0x62f15557819748FA5287EB1207026721f52aE4E3';

// Test wallets - use throwaway keys for testing
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const AGENT_KEY = '0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6';

const poster = privateKeyToAccount(POSTER_KEY);
const agent = privateKeyToAccount(AGENT_KEY);

const posterClient = createClient({ chain: chains.studionet, account: poster });
const agentClient = createClient({ chain: chains.studionet, account: agent });

async function main() {
  console.log('=== Agent Coordination System - Refund Verification ===');
  console.log('Poster:', poster.address);
  console.log('Agent:', agent.address);
  console.log('Contract:', CONTRACT);

  // Get initial balances
  const posterInitial = await posterClient.getBalance({ address: poster.address });
  const agentInitial = await agentClient.getBalance({ address: agent.address });
  console.log('\nInitial balances:');
  console.log('  Poster:', posterInitial.toString(), 'wei');
  console.log('  Agent:', agentInitial.toString(), 'wei');

  // Step 1: Post a task
  console.log('\n1. Posting task with 0.5 GEN reward...');
  const postHash = await posterClient.writeContract({
    address: CONTRACT,
    functionName: 'postTask',
    args: ['Write a blog post about AI safety'],
    value: 500000000000000000n,
  });
  console.log('   Post tx:', postHash);

  // Step 2: Agent claims task
  console.log('\n2. Agent claiming task...');
  const claimHash = await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'claimTask',
    args: ['task-1'],
    value: 0n,
  });
  console.log('   Claim tx:', claimHash);

  // Step 3: Agent submits BAD delivery (will fail verification)
  console.log('\n3. Agent submitting BAD delivery...');
  const submitHash = await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'submitDelivery',
    args: ['task-1', 'https://en.wikipedia.org/wiki/Cooking'],
    value: 0n,
  });
  console.log('   Submit tx:', submitHash);

  // Step 4: Verify delivery (should FAIL → DISPUTED)
  console.log('\n4. Verifying delivery (should FAIL)...');
  const verifyHash = await posterClient.writeContract({
    address: CONTRACT,
    functionName: 'verifyDelivery',
    args: ['task-1'],
    value: 0n,
  });
  console.log('   Verify tx:', verifyHash);

  // Wait for consensus
  console.log('\n   Waiting 30s for AI consensus...');
  await new Promise(r => setTimeout(r, 30000));

  // Check status after failed verification
  const taskAfterVerify = await posterClient.readContract({
    address: CONTRACT,
    functionName: 'getTask',
    args: ['task-1'],
  });
  console.log('\nTask status after verify:', taskAfterVerify);

  // Step 5: Resolve dispute (refund poster)
  console.log('\n5. Resolving dispute (refunding poster)...');
  const resolveHash = await posterClient.writeContract({
    address: CONTRACT,
    functionName: 'resolveDispute',
    args: ['task-1'],
    value: 0n,
  });
  console.log('   Resolve tx:', resolveHash);

  // Wait for finalization
  console.log('\n   Waiting 10s...');
  await new Promise(r => setTimeout(r, 10000));

  // Check final balances
  const posterFinal = await posterClient.getBalance({ address: poster.address });
  const agentFinal = await agentClient.getBalance({ address: agent.address });

  console.log('\n=== Final Results ===');
  console.log('Poster final balance:', posterFinal.toString(), 'wei');
  console.log('Agent final balance:', agentFinal.toString(), 'wei');

  const posterDelta = posterFinal - posterInitial;
  const agentDelta = agentFinal - agentInitial;

  console.log('\nBalance changes:');
  console.log('  Poster delta:', posterDelta.toString(), 'wei');
  console.log('  Agent delta:', agentDelta.toString(), 'wei');

  // Verify task status
  const task = await posterClient.readContract({
    address: CONTRACT,
    functionName: 'getTask',
    args: ['task-1'],
  });
  console.log('\nTask status:', task);

  // Check emitted transfers
  const transfers = await posterClient.readContract({
    address: CONTRACT,
    functionName: 'getEmittedTransfers',
    args: [],
  });
  console.log('Emitted transfers:', transfers);

  // Assertions
  console.log('\n=== Assertions ===');
  const reward = 500000000000000000n;

  // Agent should have received nothing
  if (agentDelta === 0n) {
    console.log('✅ PASS: Agent received nothing (disputed delivery)');
  } else {
    console.log('❌ FAIL: Agent delta', agentDelta.toString(), '!= 0');
  }

  // Poster should have gotten full refund
  if (posterDelta === 0n) {
    console.log('✅ PASS: Poster got full refund (net zero after post + refund)');
  } else {
    console.log('❌ FAIL: Poster delta', posterDelta.toString(), '!= 0');
  }

  console.log('\n=== Complete ===');
}

main().catch(console.error);
