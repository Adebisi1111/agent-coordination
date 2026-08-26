# Frontend for Agent Coordination System

This PR adds the browser frontend for the Agent Coordination System.

## What's included

- `public/index.html` — full UI with wallet connection, task board, agent registration
- `public/gl-client.js` — GenLayer client wrapper (read + write through MetaMask)
- `docs/` — GitHub Pages deployment

## Wallet connection

- MetaMask connect via `eth_requestAccounts`
- GenLayer Bradbury Testnet auto-switch
- Balance display

## Transaction flow

1. Post task → `postTask(description)` with GEN value
2. Register agent → `registerAgent(capabilities)` with stake
3. Claim task → `claimTask(taskId)`
4. Verify delivery → `verifyDelivery(taskId)`

All transactions are sent through the connected wallet via genlayer-js `writeContract`.
