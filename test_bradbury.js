const { createClient, chains } = require('genlayer-js');
const { privateKeyToAccount } = require('viem/accounts');
const fs = require('fs');

const MAIN_KEY = '0x023d076ab40ea46c59ac7ca7cecfaa2db5fa10b7a481aef27cf68e9cc5a8c0af';

async function main() {
  const account = privateKeyToAccount(MAIN_KEY);
  const client = createClient({ chain: chains.testnetBradbury, account });
  
  console.log('Address:', account.address);
  
  // Read contract code
  const contractCode = fs.readFileSync('contracts/agent_coordination.py', 'utf8');
  
  // Deploy contract
  console.log('\n--- Deploying Contract ---');
  const txHash = await client.deployContract({
    code: contractCode,
    args: [],
  });
  console.log('Deploy tx hash:', txHash);
  
  // Wait for transaction to finalize
  console.log('Waiting for deployment to finalize...');
  const receipt = await client.waitForTransactionReceipt({ hash: txHash });
  const contractAddress = receipt.txDataDecoded?.contractAddress || receipt.contractAddress;
  console.log('Contract address:', contractAddress);
  
  if (!contractAddress) {
    console.log('Could not find contract address.');
    return;
  }
  
  // Get initial balance
  const balanceBefore = await client.getBalance({ address: account.address });
  console.log('Balance before:', balanceBefore.toString(), 'wei =', Number(balanceBefore) / 1e18, 'GEN');
  
  // Register agent with value (min stake = 0.001 GEN = 1000000000000000 wei)
  console.log('\n--- Register Agent ---');
  const tx1 = await client.writeContract({
    address: contractAddress,
    functionName: 'registerAgent',
    args: ['writing,coding,research'],
    value: BigInt(2000000000000000000), // 2 GEN
  });
  console.log('Register tx:', tx1);
  
  // Wait
  await new Promise(r => setTimeout(r, 30000));
  
  // Post task with reward
  console.log('\n--- Post Task ---');
  const tx2 = await client.writeContract({
    address: contractAddress,
    functionName: 'postTask',
    args: ['Write about AI safety'],
    value: BigInt(500000000000000000), // 0.5 GEN
  });
  console.log('Post task tx:', tx2);
  
  // Wait
  await new Promise(r => setTimeout(r, 30000));
  
  // Get task ID
  const taskCount = await client.readContract({
    address: contractAddress,
    functionName: 'getClaimCount',
    args: [],
  });
  console.log('Task count:', taskCount);
  
  const taskId = 'task-1';
  
  // Claim task
  console.log('\n--- Claim Task ---');
  const tx3 = await client.writeContract({
    address: contractAddress,
    functionName: 'claimTask',
    args: [taskId],
  });
  console.log('Claim tx:', tx3);
  
  // Wait
  await new Promise(r => setTimeout(r, 30000));
  
  // Submit delivery
  console.log('\n--- Submit Delivery ---');
  const tx4 = await client.writeContract({
    address: contractAddress,
    functionName: 'submitDelivery',
    args: [taskId, 'https://example.com/ai-blog'],
  });
  console.log('Submit tx:', tx4);
  
  // Wait
  await new Promise(r => setTimeout(r, 30000));
  
  // Check balance before approval
  const balanceBeforeApprove = await client.getBalance({ address: account.address });
  console.log('\nBalance before approve:', balanceBeforeApprove.toString(), 'wei =', Number(balanceBeforeApprove) / 1e18, 'GEN');
  
  // Approve delivery
  console.log('\n--- Approve Delivery ---');
  const tx5 = await client.writeContract({
    address: contractAddress,
    functionName: 'approveDelivery',
    args: [taskId],
  });
  console.log('Approve tx:', tx5);
  
  // Wait
  await new Promise(r => setTimeout(r, 30000));
  
  // Check balance after approval
  const balanceAfterApprove = await client.getBalance({ address: account.address });
  console.log('\nBalance after approve:', balanceAfterApprove.toString(), 'wei =', Number(balanceAfterApprove) / 1e18, 'GEN');
  console.log('Delta:', (balanceAfterApprove - balanceBeforeApprove).toString(), 'wei');
  
  // Get task
  const task = await client.readContract({
    address: contractAddress,
    functionName: 'getTask',
    args: [taskId],
  });
  console.log('\nTask:', task);
  
  console.log('\n=== Test Complete ===');
}

main().catch(console.error);
