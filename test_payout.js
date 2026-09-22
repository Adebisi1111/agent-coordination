const { createClient, createAccount, chains, abi } = require('genlayer-js');

const RPC = 'http://127.0.0.1:4000/api';
const CONTRACT = '0xd632d82130E7A68f0c979EfD21dC2b385afd89d9';

async function main() {
  console.log('=== Real Balance Test ===');
  
  // Create clients
  const client = createClient({ chain: chains.localnet });
  
  // Get accounts
  const accounts = await client.request({ method: 'eth_accounts', params: [] });
  const payer = accounts[0];
  const payee = accounts[1] || accounts[0];
  
  console.log('Payer:', payer);
  console.log('Payee:', payee);
  
  // Get initial balances
  const balPayerBefore = await client.request({ method: 'eth_getBalance', params: [payer, 'latest'] });
  const balPayeeBefore = await client.request({ method: 'eth_getBalance', params: [payee, 'latest'] });
  console.log('Payer balance before:', balPayerBefore);
  console.log('Payee balance before:', balPayeeBefore);
  
  console.log('\n=== Tests passed - balances read successfully ===');
}

main().catch(console.error);
