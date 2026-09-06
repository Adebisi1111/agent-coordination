import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

// Use Studio Network
const CONTRACT = '0x471CFDa12A5C1a75279FC65a506beD210c6415d2';

// Poster (main wallet)
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.studionet, account: poster });

// Agent (fixed private key)
const AGENT_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const agent = privateKeyToAccount(AGENT_KEY);
const agentClient = createClient({ chain: chains.studionet, account: agent });

async function main() {
  console.log('=== STUDIO NETWORK TEST ===');
  console.log('RPC: https://studio.genlayer.com/api');
  console.log('Contract:', CONTRACT);
  console.log('Poster:', poster.address);
  console.log('Agent:', agent.address);

  // Check task count
  try {
    const count = await posterClient.readContract({ address: CONTRACT, functionName: 'getClaimCount', args: [] });
    console.log('Task count:', JSON.stringify(count));
  } catch (e) {
    console.log('Task count error:', e.message);
  }

  // Check balances
  try {
    const posterBal = await posterClient.getBalance({ address: poster.address });
    const agentBal = await agentClient.getBalance({ address: agent.address });
    console.log('Poster balance:', posterBal.toString(), 'wei');
    console.log('Agent balance:', agentBal.toString(), 'wei');
  } catch (e) {
    console.log('Balance error:', e.message);
  }

  // Check emitted transfers
  try {
    const transfers = await posterClient.readContract({ address: CONTRACT, functionName: 'getEmittedTransfers', args: [] });
    console.log('Emitted transfers:', transfers);
  } catch (e) {
    console.log('Transfers error:', e.message);
  }
}

main().catch(console.error);
