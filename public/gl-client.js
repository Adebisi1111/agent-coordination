// GenLayer client for Agent Coordination System
import { createClient } from 'genlayer-js';
import { testnetBradbury } from 'genlayer-js/chains';

export const CONTRACT = '0xbfe7b4002133410954FcD8B1c3156655889A241d';
export const EXPLORER_ADDR = 'https://explorer-bradbury.genlayer.com/address/';
export const EXPLORER_TX = 'https://explorer-bradbury.genlayer.com/tx/';

const client = createClient({ chain: testnetBradbury });

export async function contractCall(method, type, args = [], value = 0) {
  if (type === 'view') {
    return client.readContract({
      address: CONTRACT,
      functionName: method,
      args,
    });
  }
  return client.writeContract({
    address: CONTRACT,
    functionName: method,
    args,
    value: value.toString(),
  });
}
