import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';
import { readFileSync } from 'fs';

// Use Studio Network
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.studionet, account: poster });

async function main() {
  console.log('=== DEPLOYING TO STUDIO NETWORK ===');
  console.log('RPC: https://studio.genlayer.com/api');
  console.log('Deployer:', poster.address);

  // Check balance first
  const balance = await posterClient.getBalance({ address: poster.address });
  console.log('Balance:', balance.toString(), 'wei');
  
  if (balance === 0n) {
    console.log('\n!!! Poster wallet has no GEN on Studio Network !!!');
    console.log('Send GEN to:', poster.address);
    console.log('Then try again.');
    return;
  }

  // Read contract source
  const contractSource = readFileSync('./contracts/agent_coordination.py', 'utf8');
  console.log('Contract source loaded, length:', contractSource.length);

  // Deploy
  console.log('\nDeploying contract...');
  try {
    const result = await posterClient.deployContract({
      source: contractSource,
      args: [],
    });
    console.log('Deploy result:', result);
    console.log('Contract address:', result.contractAddress);
  } catch (e) {
    console.log('Deploy error:', e.message);
  }
}

main().catch(console.error);
