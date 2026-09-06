import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const CONTRACT = '0x471CFDa12A5C1a75279FC65a506beD210c6415d2';

// Poster (main wallet)
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.testnetBradbury, account: poster });

// Agent (fixed private key)
const AGENT_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const agent = privateKeyToAccount(AGENT_KEY);
const agentClient = createClient({ chain: chains.testnetBradbury, account: agent });

async function main() {
  console.log('=== FUNDING AGENT ===');
  console.log('Agent address:', agent.address);
  
  // Send 2 GEN to agent
  const hash = await posterClient.sendTransaction({
    to: agent.address,
    value: 2000000000000000000n,
  });
  console.log('Fund tx:', hash);
}

main().catch(console.error);
