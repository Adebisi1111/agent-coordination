import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount, generatePrivateKey } from 'viem/accounts';

const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const client = createClient({ chain: chains.testnetBradbury, account: poster });

async function main() {
  // Generate agent wallet
  const agentKey = generatePrivateKey();
  const agent = privateKeyToAccount(agentKey);
  console.log('Agent address:', agent.address);
  console.log('Agent PRIVATE KEY:', agentKey);
  
  // Send 0.1 GEN to agent
  const amount = 100000000000000000n;
  console.log('Sending 0.1 GEN to agent wallet...');
  const txHash = await client.sendTransaction({
    to: agent.address,
    value: amount,
  });
  console.log('Transaction hash:', txHash);
  
  // Check balance
  const balance = await client.getBalance({ address: agent.address });
  console.log('Agent balance:', balance.toString(), 'wei');
}

main().catch(console.error);
