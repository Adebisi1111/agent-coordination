import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

// Studio Network
const CONTRACT = '0x50BD0a5C0AF880c5DC5DDbc899F8B6E2e7Af48a1';

// Poster (main wallet)
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.studionet, account: poster });

async function wait(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log('=== STUDIO NETWORK - DISPUTE/REFUND TEST ===');
  console.log('Contract:', CONTRACT);
  console.log('Poster:', poster.address);

  const posterBefore = await posterClient.getBalance({ address: poster.address });
  console.log('Poster before:', posterBefore.toString(), 'wei');

  // Check current task status
  const task = await posterClient.readContract({ address: CONTRACT, functionName: 'getTask', args: ['task-1'] });
  console.log('\nCurrent task status:', task);

  // Resolve dispute (refund to poster)
  console.log('\nResolving dispute...');
  const hash = await posterClient.writeContract({
    address: CONTRACT,
    functionName: 'resolveDispute',
    args: ['task-1'],
    value: 0n,
  });
  console.log('Resolve tx:', hash);

  // Wait for finalization
  console.log('\nWaiting for finalization...');
  for (let i = 0; i < 30; i++) {
    await wait(10000);
    try {
      const t = await posterClient.readContract({ address: CONTRACT, functionName: 'getTask', args: ['task-1'] });
      const parsed = JSON.parse(t.data || t);
      if (parsed.status === 'REFUNDED') {
        console.log('   Refunded! Status:', parsed.status);
        break;
      }
      process.stdout.write('.');
    } catch (e) {
      process.stdout.write('x');
    }
  }

  // Final balances
  const posterAfter = await posterClient.getBalance({ address: poster.address });
  console.log('\nPoster delta:', (posterAfter - posterBefore).toString(), 'wei');

  // Check emitted transfers
  const transfers = await posterClient.readContract({ address: CONTRACT, functionName: 'getEmittedTransfers', args: [] });
  console.log('Emitted Transfers:', transfers);

  const externalLog = await posterClient.readContract({ address: CONTRACT, functionName: 'getExternalTransferLog', args: [] });
  console.log('External Transfer Log:', externalLog);

  console.log('\n=== RESULT ===');
  console.log('Poster balance change:', (posterAfter - posterBefore).toString(), 'wei');
  if (posterAfter > posterBefore) {
    console.log('✅ REFUND VERIFIED: Poster received refund');
  } else {
    console.log('❌ No refund detected');
  }
}

main().catch(console.error);
