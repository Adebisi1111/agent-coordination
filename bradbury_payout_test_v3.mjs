import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount, generatePrivateKey } from 'viem/accounts';

const CONTRACT = '0x471CFDa12A5C1a75279FC65a506beD210c6415d2';

// Poster (main wallet)
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.testnetBradbury, account: poster });

// Agent (throwaway - fixed key for this test)
const AGENT_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const agent = privateKeyToAccount(AGENT_KEY);
const agentClient = createClient({ chain: chains.testnetBradbury, account: agent });

async function main() {
  console.log('=== Agent Coordination System - PAYOUT Verification (Bradbury) ===');
  console.log('Poster:', poster.address);
  console.log('Agent:', agent.address, '(throwaway)');
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

  // Check poster balance after posting
  const posterAfterPost = await posterClient.getBalance({ address: poster.address });
  console.log('   Poster balance after post:', posterAfterPost.toString(), 'wei');

  // Step 2: Agent claims task
  console.log('\n2. Agent claiming task...');
  const claimHash = await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'claimTask',
    args: ['task-1'],
    value: 0n,
  });
  console.log('   Claim tx:', claimHash);

  // Step 3: Agent submits delivery
  console.log('\n3. Agent submitting delivery...');
  const submitHash = await agentClient.writeContract({
    address: CONTRACT,
    functionName: 'submitDelivery',
    args: ['task-1', 'https://en.wikipedia.org/wiki/Artificial_intelligence'],
    value: 0n,
  });
  console.log('   Submit tx:', submitHash);

  // Step 4: Verify delivery (triggers AI consensus + payout)
  console.log('\n4. Verifying delivery (AI consensus)...');
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

  // Agent should have gained the reward
  if (agentDelta === reward) {
    console.log('✅ PASS: Agent received exactly the reward');
  } else {
    console.log('❌ FAIL: Agent delta', agentDelta.toString(), '!= reward', reward.toString());
  }

  // Poster should have lost the reward (plus gas)
  if (posterDelta === -reward) {
    console.log('✅ PASS: Poster paid exactly the reward');
  } else {
    console.log('❌ FAIL: Poster delta', posterDelta.toString(), '!= -reward', (-reward).toString());
  }

  console.log('\n=== Complete ===');
}

main().catch(console.error);
