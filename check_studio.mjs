import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

// Use Studio Network
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.studionet, account: poster });

async function main() {
  console.log('=== CHECKING STUDIO NETWORK ===');
  
  // Check balance
  const balance = await posterClient.getBalance({ address: poster.address });
  console.log('Poster balance:', balance.toString(), 'wei');
  
  // Get chain info
  const chain = await posterClient.getChain();
  console.log('Chain:', chain);
}

main().catch(console.error);
