const { createClient, chains } = require('genlayer-js');
const { privateKeyToAccount } = require('viem/accounts');

// Test the AgentPact v5 contract which uses create_agreement (non-payable) + fund_agreement (payable)
const CONTRACT = '0xf3bb0D88A3D07C7A349f30292c9ff470b2990652';
const AGENT_KEY = '0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26';

async function main() {
  const account = privateKeyToAccount(AGENT_KEY);
  const client = createClient({ chain: chains.testnetBradbury, account });
  
  console.log('Address:', account.address);
  
  const balanceBefore = await client.getBalance({ address: account.address });
  console.log('Balance before:', balanceBefore.toString(), 'wei =', Number(balanceBefore) / 1e18, 'GEN');
  
  // Create agreement (non-payable)
  console.log('\n--- Create Agreement ---');
  try {
    const tx = await client.writeContract({
      address: CONTRACT,
      functionName: 'create_agreement',
      args: [
        'test-js-001',
        '0x782abaE1C6C4aec093C964785a4c10C0991Fa01A',
        'Test service agreement',
        10000000000000000n,
        3600,
        10,
        95,
        5000,
        10
      ],
    });
    console.log('Tx hash:', tx);
  } catch (err) {
    console.log('Error:', err.message);
  }
  
  // Wait
  console.log('\nWaiting 30 seconds...');
  await new Promise(r => setTimeout(r, 30000));
  
  const balanceAfter = await client.getBalance({ address: account.address });
  console.log('Balance after:', balanceAfter.toString(), 'wei =', Number(balanceAfter) / 1e18, 'GEN');
  console.log('Delta:', (balanceAfter - balanceBefore).toString(), 'wei');
  
  // Read agreement
  const result = await client.readContract({
    address: CONTRACT,
    functionName: 'get_agreement',
    args: ['test-js-001'],
  });
  console.log('\nAgreement:', result);
  
  // Now fund agreement (payable) with genlayer-js
  console.log('\n--- Fund Agreement ---');
  try {
    const tx = await client.writeContract({
      address: CONTRACT,
      functionName: 'fund_agreement',
      args: ['test-js-001'],
      value: 100000000000000000n,  // 0.1 GEN
    });
    console.log('Tx hash:', tx);
  } catch (err) {
    console.log('Error:', err.message);
  }
  
  // Wait
  console.log('\nWaiting 30 seconds...');
  await new Promise(r => setTimeout(r, 30000));
  
  const balanceFinal = await client.getBalance({ address: account.address });
  console.log('Balance after fund:', balanceFinal.toString(), 'wei =', Number(balanceFinal) / 1e18, 'GEN');
  
  // Read agreement
  const result2 = await client.readContract({
    address: CONTRACT,
    functionName: 'get_agreement',
    args: ['test-js-001'],
  });
  console.log('\nAgreement after fund:', result2);
  
  console.log('\n=== Test Complete ===');
}

main().catch(console.error);
