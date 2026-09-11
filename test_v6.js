const { createClient, chains } = require('genlayer-js');
const { privateKeyToAccount } = require('viem/accounts');

// Test if Address.transfer() works on Bradbury
const CONTRACT = '0x655803fD80ee5D8Eed06Fe620A2F69b85318bA22';

async function main() {
  const account = privateKeyToAccount('0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26');
  const client = createClient({ chain: chains.testnetBradbury, account });
  
  console.log('Address:', account.address);
  
  const balanceBefore = await client.getBalance({ address: account.address });
  console.log('Balance before:', balanceBefore.toString(), 'wei =', Number(balanceBefore) / 1e18, 'GEN');
  
  // Try to register agent with 0.5 GEN
  console.log('\n--- Register Agent ---');
  try {
    const tx = await client.writeContract({
      address: CONTRACT,
      functionName: 'registerAgent',
      args: ['writing', ''],
      value: 500000000000000000n,
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
  
  console.log('\n=== Test Complete ===');
}

main().catch(console.error);
