import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const CONTRACT = '0x471CFDa12A5C1a75279FC65a506beD210c6415d2';

// Poster (main wallet)
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.testnetBradbury, account: poster });

async function main() {
  console.log('=== FUNDING AGENT ===');
  console.log('Sending 5 GEN to agent...');
  
  try {
    const hash = await posterClient.sendTransaction({
      to: '0x782abaE1C6C4aec093C964785a4c10C0991Fa01A',
      value: 5000000000000000000n,
    });
    console.log('Fund tx:', hash);
  } catch (e) {
    console.log('Error:', e.message);
  }
}

main().catch(console.error);
