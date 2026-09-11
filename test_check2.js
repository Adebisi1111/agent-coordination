const { createClient, chains } = require('genlayer-js');
const { privateKeyToAccount } = require('viem/accounts');

const CONTRACT = '0x8E2F4557dA23B9306418f4A1C5F5A813Bee6d758';
const AGENT_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';

async function main() {
  const agentAccount = privateKeyToAccount(AGENT_KEY);
  const agentClient = createClient({ chain: chains.testnetBradbury, account: agentAccount });
  
  console.log('Agent address:', agentAccount.address);
  
  // Check current state
  const task = await agentClient.readContract({
    address: CONTRACT,
    functionName: 'getTask',
    args: ['task-2'],
  });
  console.log('Task:', task);
  
  // Check emitted transfers
  const transfers = await agentClient.readContract({
    address: CONTRACT,
    functionName: 'getEmittedTransfers',
    args: [],
  });
  console.log('Emitted transfers:', transfers);
  
  // Check external transfer log
  const log = await agentClient.readContract({
    address: CONTRACT,
    functionName: 'getExternalTransferLog',
    args: [],
  });
  console.log('External transfer log:', log);
  
  console.log('\n=== Check Complete ===');
}

main().catch(console.error);
