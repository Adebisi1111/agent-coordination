const { createClient, chains } = require('genlayer-js');
const { privateKeyToAccount } = require('viem/accounts');

const CONTRACT = '0xFFff7f3DC91401Efd5e1f869259d36DAEf67F519';

async function main() {
  const account = privateKeyToAccount('0xf6e536098748e4d4884c30b588136835ff7b6d6ed0e71dc1dc92753d27b94b26');
  const client = createClient({ chain: chains.testnetBradbury, account });
  
  console.log('Address:', account.address);
  
  const balanceBefore = await client.getBalance({ address: account.address });
  console.log('Balance before:', balanceBefore.toString(), 'wei =', Number(balanceBefore) / 1e18, 'GEN');
  
  const contractBalanceBefore = await client.getBalance({ address: CONTRACT });
  console.log('Contract balance before:', contractBalanceBefore.toString(), 'wei =', Number(contractBalanceBefore) / 1e18, 'GEN');
  
  // Withdraw
  console.log('\n--- Withdraw ---');
  try {
    const tx = await client.writeContract({
      address: CONTRACT,
      functionName: 'withdraw',
      args: [],
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
  console.log('Balance delta:', (balanceAfter - balanceBefore).toString(), 'wei =', Number(balanceAfter - balanceBefore) / 1e18, 'GEN');
  
  const contractBalanceAfter = await client.getBalance({ address: CONTRACT });
  console.log('Contract balance after:', contractBalanceAfter.toString(), 'wei =', Number(contractBalanceAfter) / 1e18, 'GEN');
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
