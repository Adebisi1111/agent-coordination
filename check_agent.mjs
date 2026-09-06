import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const CONTRACT = '0x50BD0a5C0AF880c5DC5DDbc899F8B6E2e7Af48a1';

// Agent account
const AGENT_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';
const agent = privateKeyToAccount(AGENT_KEY);
const agentClient = createClient({ chain: chains.studionet, account: agent });

async function main() {
  console.log('=== AGENT STATE ===');
  console.log('Agent:', agent.address);

  const bal = await agentClient.getBalance({ address: agent.address });
  console.log('Agent balance:', bal.toString(), 'wei');

  // Check agent info
  const agentInfo = await agentClient.readContract({ address: CONTRACT, functionName: 'getAgent', args: [agent.address] });
  console.log('Agent info:', agentInfo);
}

main().catch(console.error);
