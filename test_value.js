const { createClient, chains } = require('genlayer-js');
const { privateKeyToAccount } = require('viem/accounts');

// Test: Does payable function receive value?
const CONTRACT = '0xFFff7f3DC91401Efd5e1f869259d36DAEf67F519';

async function main() {
  const account = privateKeyToAccount('0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26');
  const client = createClient({ chain: chains.testnetBradbury, account });
  
  console.log('Address:', account.address);
  
  const contractBalanceBefore = await client.getBalance({ address: CONTRACT });
  console.log('Contract balance before:', contractBalanceBefore.toString(), 'wei');
  
  // Try deposit with value using genlayer-js
  console.log('\n--- Deposit with value (genlayer-js) ---');
  try {
    const tx = await client.writeContract({
      address: CONTRACT,
      functionName: 'deposit',
      args: [],
      value: 100000000000000000n,  // 0.1 GEN
    });
    console.log('Tx hash:', tx);
  } catch (err) {
    console.log('Error:', err.message);
  }
  
  // Wait
  console.log('\nWaiting 30 seconds...');
  await new Promise(r => setTimeout(r, 30000));
  
  const contractBalanceAfter = await client.getBalance({ address: CONTRACT });
  console.log('Contract balance after:', contractBalanceAfter.toString(), 'wei');
  console.log('Contract delta:', (contractBalanceAfter - contractBalanceBefore).toString(), 'wei');
  
  // Check stored balance
  const storedBalance = await client.readContract({
    address: CONTRACT,
    functionName: 'getBalance',
    args: [],
  });
  console.log('Stored balance:', storedBalance, 'wei');
  
  console.log('\n=== Test Complete ===');
}

main().catch(console.error);
