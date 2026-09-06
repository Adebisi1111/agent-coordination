import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const CONTRACT = '0x471CFDa12A5C1a75279FC65a506beD210c6415d2';

// Poster (main wallet)
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.testnetBradbury, account: poster });

async function main() {
  console.log('=== CHECKING TASK STATUS ===');
  
  // Check task status
  const task = await posterClient.readContract({ 
    address: CONTRACT, 
    functionName: 'getTask', 
    args: ['task-1'] 
  });
  console.log('Task:', task);
  
  // Check balances
  const poster = await posterClient.getBalance({ address: '0x61fd0047595A30A067f1F21F3b28C4AE8A8e3Dc3' });
  const agent = await posterClient.getBalance({ address: '0x782abaE1C6C4aec093C964785a4c10C0991Fa01A' });
  console.log('\nBalances:');
  console.log('Poster:', poster.toString(), 'wei');
  console.log('Agent:', agent.toString(), 'wei');
  
  // Check emitted transfers
  const transfers = await posterClient.readContract({ 
    address: CONTRACT, 
    functionName: 'getEmittedTransfers', 
    args: [] 
  });
  console.log('\nEmitted Transfers:', transfers);
}

main().catch(console.error);
