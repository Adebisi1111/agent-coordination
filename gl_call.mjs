import { createClient, createAccount } from 'genlayer-js';
import { testnetBradbury } from 'genlayer-js/chains';
import { readFileSync } from 'fs';
import { Wallet } from 'ethers';

const FACTORY = process.env.FACTORY;
const keystore = readFileSync('/home/administrator/.genlayer/keystores/testwallet.json', 'utf8');
const wallet = Wallet.fromEncryptedJsonSync(keystore, process.env.GLPASS);
const account = createAccount(wallet.privateKey);
const client = createClient({ chain: testnetBradbury, account });

const [fn, args, value] = process.argv.slice(2);
const argsParsed = JSON.parse(args);
const val = value ? BigInt(value) : 0n;

console.log(`calling ${fn}(${argsParsed.join(',')}) value=${val}`);
const { hash } = await client.writeContract({ address: FACTORY, functionName: fn, args: argsParsed, value });
console.log('tx hash:', hash);
const receipt = await client.waitForTransactionReceipt({ hash, retries: 100, interval: 5000 });
let lr = receipt?.consensus_data?.leader_receipt;
if (Array.isArray(lr)) lr = lr[0];
const exec = receipt?.txExecutionResultName ?? lr?.execution_result;
console.log('exec  :', exec);
