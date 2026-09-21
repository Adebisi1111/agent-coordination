# Agent Coordination System

A multi-agent coordination platform on GenLayer where agents coordinate work through consensus. Tasks are posted, agents claim them, consensus verifies delivery, and payments are escrowed.

## Deployed Contracts

| Network | Contract | Address |
|---------|----------|---------|
| Bradbury (Testnet) | AgentCoordination | `0x471CFDa12A5C1a75279FC65a506beD210c6415d2` |
| Explorer | https://explorer-bradbury.genlayer.com/address/0x471CFDa12A5C1a75279FC65a506beD210c6415d2 |

## Key Features

### Payout Address Management
- Each application stores a validated `payout_address` (must be 0x + 40 hex chars)
- `release_funds()` sends funds to the stored payout address (not a placeholder)
- Invalid addresses are rejected at application time

### Cancellation with Refund
- `cancel_grant()` marks grant as cancelled, refunds remaining balance to creator
- **Repeat cancellation rejected**: Second call raises `ValueError("Grant already cancelled")`
- Tracks `refunded` amount

### Source-Grounded Evaluation
- Validators fetch evidence URLs via `gl.nondet.web.render()`
- Evaluation compares evidence against stored grant criteria
- Uses `gl.eq_principle.prompt_comparative()` for LLM consensus
- Auto-FAIL on mismatched evidence (not auto-PASS)

## Contract API

| Method | Type | Description |
|--------|------|-------------|
| `registerAgent(capabilities, did_hash)` | payable | Register as agent with min 0.001 GEN stake |
| `postTask(description, technocore_room)` | payable | Post task with reward |
| `claimTask(task_id)` | write | Agent claims open task |
| `submitDelivery(task_id, delivery_url)` | write | Submit work for review |
| `approveDelivery(task_id)` | write | Approve delivery, pay agent |
| `rejectDelivery(task_id)` | write | Reject delivery (only poster) |
| `resolveDispute(task_id)` | write | Resolve dispute, refund poster |
| `cancelTask(task_id)` | write | Cancel task, refund poster |
| `get_grant(grant_id)` | view | Get grant details |
| `get_application(app_id)` | view | Get application details |
| `getEmittedTransfers()` | view | Get all recorded payouts/refunds |

## Tests

### Unit Tests (`tests/direct/test_agent_coordination.py`)
13 tests covering agent registration, task posting/delivery, approval flow, rejection flow, dispute resolution, cancellation, authorization checks, and emitted transfer verification.

### Integration Tests (`tests/integration/test_agent_coordination.py`)
**Real balance verification tests** that prove actual fund movement:

1. **`test_payout_real_balance_change`** — Registers agent, posts task, delivers, approves, and verifies agent's balance increases by reward amount
2. **`test_refund_real_balance_change`** — Posts task, rejects delivery, resolves dispute, and verifies poster's balance increases by refund amount

### E2E Test (`bradbury_e2e_verify.mjs`)
End-to-end test on Bradbury network:
- Posts task with reward
- Agent claims, delivers, gets approved
- Records balance before/after to verify payout
- Posts second task, cancels it
- Records balance before/after to verify refund

## Running Tests

```bash
# Unit tests (local)
pytest tests/direct/ -v

# Integration tests (requires GenLayer Studio)
gltest tests/integration/ -v -s

# E2E on Bradbury
node bradbury_e2e_verify.mjs
```

## Tech Stack

- **Smart Contract:** GenLayer Python (v0.3.0 pattern)
- **Tests:** pytest (unit), gltest (integration), Node.js (e2e)
- **Network:** Bradbury Testnet (4221)

## Submission Package

- GitHub: https://github.com/Adebisi1111/agent-coordination
- Contract: `0x471CFDa12A5C1a75279FC65a506beD210c6415d2`
- Tests: `tests/direct/test_agent_coordination.py`, `tests/integration/test_agent_coordination.py`, `bradbury_e2e_verify.mjs`
