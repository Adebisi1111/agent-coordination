import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const AGENT_ADDRESS = '0x5ff6f0F645646503830E7d4D24D19Cc2C56335F1';

const poster = privateKeyToAccount(POSTER_KEY);
const client = createClient({ chain: chains.testnetBradbury, account: poster });

async function main() {
  console.log('Poster address:', poster.address);
  console.log('Agent address:', AGENT_ADDRESS);
  
  const amount = 100000000000000000n; // 0.1 GEN
  console.log('Sending 0.1 GEN to agent wallet...');
  
  const txHash = await client.sendTransaction({
    to: AGENT_ADDRESS,
    value: amount,
  });
  console.log('Transaction hash:', txHash);
  
  // Check balance
  const balance = await client.getBalance({ address: AGENT_ADDRESS });
  console.log('Agent balance:', balance.toString(), 'wei');
}

main().catch(console.error);
