# Agent Coordination System - Test Results

## Network: Studio Network (https://studio.genlayer.com/api)
## Contract: 0x50BD0a5C0AF880c5DC5DDbc899F8B6E2e7Af48a1

---

## ✅ Verified On-Chain

### Test 1: Payout (task-3)
- **Task**: "AI safety"
- **Delivery**: https://en.wikipedia.org/wiki/AI_safety
- **Result**: VERIFIED (AI consensus PASS)
- **Emitted Transfer**: 
  ```json
  {"to": "0x782abaE1C6C4aec093C964785a4c10C0991Fa01A", "amount": 500000000000000000, "type": "payout"}
  ```
- **External Transfer Log**:
  ```json
  {"to": "0x782abaE1C6C4aec093C964785a4c10C0991Fa01A", "amount": 500000000000000000, "type": "payout", "status": "emitted", "on": "finalized"}
  ```

### Test 2: Refund (task-1)
- **Task**: "Write a blog post about AI safety"
- **Delivery**: https://en.wikipedia.org/wiki/Artificial_intelligence
- **Result**: DISPUTED (AI consensus FAIL)
- **Emitted Transfer**:
  ```json
  {"to": "0x61fd0047595A30A067f1F21F3b28C4AE8A8e3Dc3", "amount": 500000000000000000, "type": "refund"}
  ```
- **External Transfer Log**:
  ```json
  {"to": "0x61fd0047595A30A067f1F21F3b28C4AE8A8e3Dc3", "amount": 500000000000000000, "type": "refund", "status": "emitted", "on": "finalized"}
  ```

---

## 📊 What This Proves

| Requirement | Status |
|-------------|--------|
| Emitted external transfers on-chain | ✅ Verified |
| Transfer amount matches reward (0.5 GEN) | ✅ Verified |
| Payout to agent on PASS | ✅ Verified |
| Refund to poster on DISPUTE | ✅ Verified |
| External transfer log with status "emitted" | ✅ Verified |

---

## 🧪 How to Run More Tests

To run additional tests, you need GEN on Studio Network. The contract is deployed and working.

```bash
cd /home/administrator/agent-coordination
node run_integration_tests.mjs
```

---

## 📋 Contract Details

- **Address**: 0x50BD0a5C0AF880c5DC5DDbc899F8B6E2e7Af48a1
- **Network**: Studio Network
- **RPC**: https://studio.genlayer.com/api
- **Chain ID**: 61999
