import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const CONTRACT = '0x50BD0a5C0AF880c5DC5DDbc899F8B6E2e7Af48a1';

// Use poster for everything
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.studionet, account: poster });

async function wait(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log('=== PAYOUT VERIFICATION TEST ===');
  console.log('Contract:', CONTRACT);
  console.log('Account:', poster.address);

  // Check initial balance
  const initialBal = await posterClient.getBalance({ address: poster.address });
  console.log('Initial balance:', initialBal.toString(), 'wei');

  // Register as agent
  console.log('\n1. Registering as agent with 2 GEN stake...');
  await posterClient.writeContract({
    address: CONTRACT,
    functionName: 'registerAgent',
    args: ['writing,coding,research', ''],
    value: 2000000000000000000n,
  });
  await wait(5000);

  const afterRegister = await posterClient.getBalance({ address: poster.address });
  console.log('Balance after register:', afterRegister.toString(), 'wei');

  // Post task
  console.log('\n2. Posting task with 0.5 GEN reward...');
  await posterClient.writeContract({
    address: CONTRACT,
    functionName: 'postTask',
    args: ['AI safety', ''],
    value: 500000000000000000n,
  });
  await wait(5000);

  const afterPost = await posterClient.getBalance({ address: poster.address });
  console.log('Balance after post:', afterPost.toString(), 'wei');

  // Claim task
  console.log('\n3. Claiming task...');
  await posterClient.writeContract({
    address: CONTRACT,
    functionName: 'claimTask',
    args: ['task-600'],
    value: 0n,
  });
  await wait(5000);

  // Submit delivery
  console.log('\n4. Submitting delivery...');
  await posterClient.writeContract({
    address: CONTRACT,
    functionName: 'submitDelivery',
    args: ['task-600', 'https://en.wikipedia.org/wiki/AI_safety'],
    value: 0n,
  });
  await wait(5000);

  // Verify delivery
  console.log('\n5. Verifying delivery (AI consensus)...');
  await posterClient.writeContract({
    address: CONTRACT,
    functionName: 'verifyDelivery',
    args: ['task-600'],
    value: 0n,
  });

  // Wait for finalization
  console.log('\n6. Waiting for finalization...');
  for (let i = 0; i < 30; i++) {
    await wait(10000);
    const task = await posterClient.readContract({ address: CONTRACT, functionName: 'getTask', args: ['task-600'] });
    const parsed = JSON.parse(task.data || task);
    if (parsed.status === 'VERIFIED' || parsed.status === 'REFUNDED') {
      console.log('Finalized! Status:', parsed.status);
      break;
    }
    process.stdout.write('.');
  }

  // Wait for external transfer to finalize
  console.log('\n7. Waiting for external transfer to finalize...');
  await wait(120000); // 2 minutes

  // Check final balance
  const finalBal = await posterClient.getBalance({ address: poster.address });
  console.log('\nFinal balance:', finalBal.toString(), 'wei');

  const totalDelta = finalBal - initialBal;
  console.log('Total balance delta:', totalDelta.toString(), 'wei');

  // Expected: -2 GEN (stake) - 0.5 GEN (reward) + 0.5 GEN (payout) = -2 GEN
  // The stake is still in the contract, so net change is -2 GEN
  // But if stake is returned, net change should be 0
  if (totalDelta >= -2000000000000000000n && totalDelta <= 0n) {
    console.log('\n✅ TEST PASSED: Balance change is within expected range');
  } else {
    console.log('\n❌ TEST FAILED: Unexpected balance change');
  }

  // Check emitted transfers
  const transfers = await posterClient.readContract({ address: CONTRACT, functionName: 'getEmittedTransfers', args: [] });
  console.log('\nEmitted Transfers:', transfers);

  const externalLog = await posterClient.readContract({ address: CONTRACT, functionName: 'getExternalTransferLog', args: [] });
  console.log('External Transfer Log:', externalLog);
}

main().catch(console.error);
