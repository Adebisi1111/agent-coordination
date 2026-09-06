import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const CONTRACT = '0x50BD0a5C0AF880c5DC5DDbc899F8B6E2e7Af48a1';

// Use poster for everything
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.studionet, account: poster });

async function main() {
  console.log('=== CHECKING STUDIO NETWORK STATE ===');
  console.log('Contract:', CONTRACT);
  console.log('Account:', poster.address);

  // Check balance
  const bal = await posterClient.getBalance({ address: poster.address });
  console.log('Balance:', bal.toString(), 'wei');

  // Check emitted transfers
  const transfers = await posterClient.readContract({ address: CONTRACT, functionName: 'getEmittedTransfers', args: [] });
  console.log('\nEmitted Transfers:', transfers);

  const externalLog = await posterClient.readContract({ address: CONTRACT, functionName: 'getExternalTransferLog', args: [] });
  console.log('External Transfer Log:', externalLog);

  // Check task count
  const count = await posterClient.readContract({ address: CONTRACT, functionName: 'getClaimCount', args: [] });
  console.log('\nTask count:', count);
}

main().catch(console.error);
