// GenLayer client for Agent Coordination System
import { createClient } from 'genlayer-js';
import { testnetBradbury } from 'genlayer-js/chains';

export const CONTRACT = '0xbfe7b4002133410954FcD8B1c3156655889A241d';
export const EXPLORER_ADDR = 'https://explorer-bradbury.genlayer.com/address/';
export const EXPLORER_TX = 'https://explorer-bradbury.genlayer.com/tx/';
export const CHAIN_ID_HEX = '0x107d'; // 4221

let client = null;
let address = null;

export const getAddress = () => address;
export const isConnected = () => !!client && !!address;

function publicClient() {
  return createClient({ chain: testnetBradbury });
}

async function ensureChain() {
  const current = await window.ethereum.request({ method: 'eth_chainId' });
  if (current === CHAIN_ID_HEX) return;
  try {
    await window.ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: CHAIN_ID_HEX }],
    });
  } catch (err) {
    if (err && (err.code === 4902 || err.code === -32603)) {
      await window.ethereum.request({
        method: 'wallet_addEthereumChain',
        params: [{
          chainId: CHAIN_ID_HEX,
          chainName: 'GenLayer Bradbury Testnet',
          nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 },
          rpcUrls: ['https://rpc-bradbury.genlayer.com'],
          blockExplorerUrls: ['https://explorer-bradbury.genlayer.com'],
        }],
      });
    } else {
      throw err;
    }
  }
}

export async function connect() {
  if (!window.ethereum) throw new Error('No wallet detected. Open in MetaMask or Rabby.');
  const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
  if (!accounts || !accounts.length) throw new Error('No account authorised.');
  await ensureChain();
  address = accounts[0];
  client = createClient({
    chain: testnetBradbury,
    account: address,
    provider: window.ethereum,
  });
  return address;
}

export function disconnect() { client = null; address = null; }

export async function read(functionName, args = []) {
  const c = client ?? publicClient();
  return c.readContract({ address: CONTRACT, functionName, args });
}

export async function write(functionName, args = [], genAmount = '0') {
  if (!client) throw new Error('Connect your wallet first.');
  const value = BigInt(Math.round(parseFloat(genAmount || '0') * 1e18));
  const hash = await client.writeContract({ address: CONTRACT, functionName, args, value });
  const receipt = await client.waitForTransactionReceipt({ hash, retries: 100, interval: 5000 });
  let lr = receipt?.consensus_data?.leader_receipt;
  if (Array.isArray(lr)) lr = lr[0];
  const exec = receipt?.txExecutionResultName ?? lr?.execution_result;
  if (exec !== 'FINISHED_WITH_RETURN') {
    throw new Error(`Transaction did not finish cleanly (${exec ?? 'unknown'}).`);
  }
  return { hash, exec };
}

export async function getBalance() {
  if (!address) return 0;
  const wei = await window.ethereum.request({ method: 'eth_getBalance', params: [address, 'latest'] });
  return Number(BigInt(wei)) / 1e18;
}
