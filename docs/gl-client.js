// GenLayer client for Agent Coordination System
import { createClient } from 'genlayer-js';
import { testnetBradbury } from 'genlayer-js/chains';

export const CONTRACT = '0x07DCEc4A77AB245a7F66144eDDa6A6D9C05789eD';
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
