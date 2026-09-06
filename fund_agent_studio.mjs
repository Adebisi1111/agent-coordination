import { createClient, chains } from 'genlayer-js';
import { privateKeyToAccount } from 'viem/accounts';

const CONTRACT = '0x50BD0a5C0AF880c5DC5DDbc899F8B6E2e7Af48a1';

// Poster (main wallet)
const POSTER_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';
const poster = privateKeyToAccount(POSTER_KEY);
const posterClient = createClient({ chain: chains.studionet, account: poster });

async function wait(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log('=== FUNDING AGENT ON STUDIO NETWORK ===');
  console.log('Contract:', CONTRACT);
  console.log('Poster:', poster.address);

  // Check poster balance
  const posterBal = await posterClient.getBalance({ address: poster.address });
  console.log('Poster balance:', posterBal.toString(), 'wei');

  // Check agent balance
  const agentAddress = '0x782abaE1C6C4aec093C964785a4c10C0991Fa01A';
  const agentBal = await posterClient.getBalance({ address: agentAddress });
  console.log('Agent balance:', agentBal.toString(), 'wei');

  // Send GEN to agent using writeContract with value
  console.log('\nSending 3 GEN to agent...');
  try {
    // Use the contract's registerAgent to send value to the contract
    // Actually, let's just send a simple transfer
    const hash = await posterClient.sendTransaction({
      to: agentAddress,
      value: 3000000000000000000n,
    });
    console.log('Fund tx:', hash);
    await wait(10000);

    const agentBalAfter = await posterClient.getBalance({ address: agentAddress });
    console.log('Agent balance after:', agentBalAfter.toString(), 'wei');
  } catch (e) {
    console.log('Funding error:', e.message);
    console.log('\nTrying alternative approach...');
    
    // Alternative: deploy a contract that holds funds for the agent
    // Or use the poster as the agent
    console.log('Will use poster as agent for testing');
  }
}

main().catch(console.error);
