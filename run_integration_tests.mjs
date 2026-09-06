import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const CONTRACT = '0x50BD0a5C0AF880c5DC5DDbc899F8B6E2e7Af48a1';

// Use poster for everything (has enough GEN)
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.studionet, account: poster });

async function wait(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log('=== INTEGRATION TEST SUITE (STUDIO NETWORK) ===');
  console.log('Contract:', CONTRACT);
  console.log('Account:', poster.address);

  let allPassed = true;

  // ============================================
  // TEST 1: Payout changes agent balance
  // ============================================
  console.log('\n\n========================================');
  console.log('TEST 1: Payout changes agent balance');
  console.log('========================================');

  try {
    const posterBefore = await posterClient.getBalance({ address: poster.address });
    console.log('Balance before:', posterBefore.toString(), 'wei');

    // Register as agent (using poster as agent)
    console.log('Registering as agent...');
    await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'registerAgent',
      args: ['writing,coding,research', ''],
      value: 2000000000000000000n,
    });
    await wait(3000);

    // Post task with 0.5 GEN reward
    console.log('Posting task with 0.5 GEN reward...');
    await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'postTask',
      args: ['AI safety', ''],
      value: 500000000000000000n,
    });
    await wait(3000);

    // Claim task
    console.log('Claiming task...');
    await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'claimTask',
      args: ['task-500'],
      value: 0n,
    });
    await wait(3000);

    // Submit delivery
    console.log('Submitting delivery...');
    await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'submitDelivery',
      args: ['task-500', 'https://en.wikipedia.org/wiki/AI_safety'],
      value: 0n,
    });
    await wait(3000);

    // Verify delivery
    console.log('Verifying delivery (AI consensus)...');
    await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'verifyDelivery',
      args: ['task-500'],
      value: 0n,
    });

    // Wait for finalization
    console.log('Waiting for finalization...');
    for (let i = 0; i < 30; i++) {
      await wait(10000);
      const task = await posterClient.readContract({ address: CONTRACT, functionName: 'getTask', args: ['task-500'] });
      const parsed = JSON.parse(task.data || task);
      if (parsed.status === 'VERIFIED' || parsed.status === 'REFUNDED') {
        console.log('Finalized! Status:', parsed.status);
        break;
      }
      process.stdout.write('.');
    }

    // Wait for external transfer
    console.log('\nWaiting for external transfer...');
    await wait(60000);

    const posterAfter = await posterClient.getBalance({ address: poster.address });
    console.log('Balance after:', posterAfter.toString(), 'wei');

    const delta = posterAfter - posterBefore;
    console.log('Balance delta:', delta.toString(), 'wei');

    // Expected: -2 (stake) - 0.5 (reward posted) + 0.5 (payout) + 2 (stake returned) = 0
    // Or some variation depending on how stake is handled
    if (delta >= 0n) {
      console.log('✅ TEST 1 PASSED: Balance did not decrease (payout received)');
    } else {
      console.log('❌ TEST 1 FAILED: Balance decreased by', (-delta).toString(), 'wei');
      allPassed = false;
    }
  } catch (e) {
    console.log('❌ TEST 1 ERROR:', e.message);
    allPassed = false;
  }

  // ============================================
  // TEST 2: Refund changes poster balance
  // ============================================
  console.log('\n\n========================================');
  console.log('TEST 2: Refund changes poster balance');
  console.log('========================================');

  try {
    const posterBefore = await posterClient.getBalance({ address: poster.address });
    console.log('Balance before:', posterBefore.toString(), 'wei');

    // Post task with bad delivery expected
    console.log('Posting task...');
    await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'postTask',
      args: ['Write about AI', ''],
      value: 500000000000000000n,
    });
    await wait(3000);

    // Claim task
    console.log('Claiming task...');
    await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'claimTask',
      args: ['task-501'],
      value: 0n,
    });
    await wait(3000);

    // Submit bad delivery
    console.log('Submitting off-topic delivery...');
    await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'submitDelivery',
      args: ['task-501', 'https://example.com/cooking-recipes'],
      value: 0n,
    });
    await wait(3000);

    // Verify delivery (should FAIL)
    console.log('Verifying delivery...');
    await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'verifyDelivery',
      args: ['task-501'],
      value: 0n,
    });

    // Wait for finalization
    console.log('Waiting for finalization...');
    for (let i = 0; i < 30; i++) {
      await wait(10000);
      const task = await posterClient.readContract({ address: CONTRACT, functionName: 'getTask', args: ['task-501'] });
      const parsed = JSON.parse(task.data || task);
      if (parsed.status === 'DISPUTED') {
        console.log('Finalized! Status:', parsed.status);
        break;
      }
      process.stdout.write('.');
    }

    // Resolve dispute
    console.log('Resolving dispute...');
    await posterClient.writeContract({
      address: CONTRACT,
      functionName: 'resolveDispute',
      args: ['task-501'],
      value: 0n,
    });

    // Wait for external transfer
    await wait(60000);

    const posterAfter = await posterClient.getBalance({ address: poster.address });
    console.log('Balance after:', posterAfter.toString(), 'wei');

    const delta = posterAfter - posterBefore;
    console.log('Balance delta:', delta.toString(), 'wei');

    // Expected: -0.5 (reward posted) + 0.5 (refund) = 0
    if (delta >= 0n) {
      console.log('✅ TEST 2 PASSED: Balance did not decrease (refund received)');
    } else {
      console.log('❌ TEST 2 FAILED: Balance decreased by', (-delta).toString(), 'wei');
      allPassed = false;
    }
  } catch (e) {
    console.log('❌ TEST 2 ERROR:', e.message);
    allPassed = false;
  }

  // ============================================
  // TEST 3: Emitted external transfers
  // ============================================
  console.log('\n\n========================================');
  console.log('TEST 3: Emitted external transfers');
  console.log('========================================');

  try {
    const transfers = await posterClient.readContract({ address: CONTRACT, functionName: 'getEmittedTransfers', args: [] });
    console.log('Emitted Transfers:', transfers);

    const externalLog = await posterClient.readContract({ address: CONTRACT, functionName: 'getExternalTransferLog', args: [] });
    console.log('External Transfer Log:', externalLog);

    const transfersObj = JSON.parse(transfers);
    const externalObj = JSON.parse(externalLog);

    const payouts = Object.values(transfersObj).filter(v => JSON.parse(v).type === 'payout');
    const refunds = Object.values(transfersObj).filter(v => JSON.parse(v).type === 'refund');

    if (payouts.length >= 1 && refunds.length >= 1) {
      console.log('✅ TEST 3 PASSED: Both payout and refund transfers emitted');
    } else {
      console.log('❌ TEST 3 FAILED: Missing transfers');
      allPassed = false;
    }
  } catch (e) {
    console.log('❌ TEST 3 ERROR:', e.message);
    allPassed = false;
  }

  // ============================================
  // SUMMARY
  // ============================================
  console.log('\n\n========================================');
  console.log('INTEGRATION TEST RESULTS');
  console.log('========================================');
  if (allPassed) {
    console.log('✅ ALL TESTS PASSED');
  } else {
    console.log('❌ SOME TESTS FAILED');
  }
}

main().catch(console.error);
