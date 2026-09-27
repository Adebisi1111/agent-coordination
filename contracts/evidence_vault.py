# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }

import json
import genlayer as gl
from genlayer.storage import allow as allow_storage
from dataclasses import dataclass

TreeMap = gl.storage.TreeMap


@allow_storage
@dataclass
class Claim:
    claim_id: str
    claim_text: str
    evidence_ref: str
    submitter: str
    status: str
    created_at: int


@allow_storage
@dataclass
class Evaluation:
    validator: str
    claim_id: str
    verdict: str
    reasoning: str
    submitted_at: int


@allow_storage
@dataclass
class ConsensusResult:
    claim_id: str
    final_verdict: str
    vote_counts: dict
    evaluations: list
    finalized_at: int


@allow_storage
class EvidenceVault(gl.contract.Contract):
    claims: TreeMap[str, str]
    evaluations: TreeMap[str, str]
    consensus_results: TreeMap[str, str]
    claim_counter: u256
    evaluation_counter: u256

    def __init__(self):
        pass

    def _now(self) -> int:
        import datetime
        return int(datetime.datetime.now(datetime.timezone.utc).timestamp())

    def _get_claim(self, claim_id: str) -> dict | None:
        raw = self.claims.get(claim_id)
        if raw is None:
            return None
        return json.loads(raw)

    def _save_claim(self, claim_id: str, claim: dict):
        self.claims[claim_id] = json.dumps(claim)

    def _get_evaluations(self, claim_id: str) -> list:
        raw = self.evaluations.get(claim_id)
        if raw is None:
            return []
        return json.loads(raw)

    def _save_evaluations(self, claim_id: str, evals: list):
        self.evaluations[claim_id] = json.dumps(evals)

    def _get_consensus(self, claim_id: str) -> dict | None:
        raw = self.consensus_results.get(claim_id)
        if raw is None:
            return None
        return json.loads(raw)

    def _save_consensus(self, claim_id: str, result: dict):
        self.consensus_results[claim_id] = json.dumps(result)

    @gl.public.write
    def submitClaim(self, claim_id: str, claim_text: str, evidence_ref: str) -> str:
        if not claim_id or not claim_text or not evidence_ref:
            raise gl.vm.UserError("claim_id, claim_text, and evidence_ref are required")
        if self._get_claim(claim_id) is not None:
            raise gl.vm.UserError("Claim already exists")

        claim = {
            "claim_id": claim_id,
            "claim_text": claim_text,
            "evidence_ref": evidence_ref,
            "submitter": gl.message.sender_address.as_hex,
            "status": "SUBMITTED",
            "created_at": self._now(),
        }
        self._save_claim(claim_id, claim)
        self.claim_counter += u256(1)
        return claim_id

    @gl.public.write
    def startVerification(self, claim_id: str) -> str:
        claim = self._get_claim(claim_id)
        if claim is None:
            raise gl.vm.UserError("Claim not found")
        if claim["status"] != "SUBMITTED":
            raise gl.vm.UserError("Claim must be SUBMITTED to start verification")
        sender = gl.message.sender_address.as_hex
        if sender != claim["submitter"]:
            raise gl.vm.UserError("Only the submitter can start verification")

        claim["status"] = "READY_FOR_VERIFICATION"
        self._save_claim(claim_id, claim)
        return "READY_FOR_VERIFICATION"

    @gl.public.write
    def requestVerification(self, claim_id: str) -> str:
        claim = self._get_claim(claim_id)
        if claim is None:
            raise gl.vm.UserError("Claim not found")
        if claim["status"] != "READY_FOR_VERIFICATION":
            raise gl.vm.UserError("Claim must be READY_FOR_VERIFICATION to request verification")

        claim["status"] = "VERIFYING"
        self._save_claim(claim_id, claim)
        return "VERIFYING"

    @gl.public.write
    def submitEvaluation(
        self,
        claim_id: str,
        verdict: str,
        reasoning: str,
    ) -> str:
        if verdict not in ("SUPPORTED", "CONTRADICTED", "INCONCLUSIVE"):
            raise gl.vm.UserError("Verdict must be SUPPORTED, CONTRADICTED, or INCONCLUSIVE")
        if not reasoning:
            raise gl.vm.UserError("Reasoning is required")

        claim = self._get_claim(claim_id)
        if claim is None:
            raise gl.vm.UserError("Claim not found")
        if claim["status"] != "VERIFYING":
            raise gl.vm.UserError("Claim must be VERIFYING to accept evaluations")

        sender = gl.message.sender_address.as_hex
        eval_data = {
            "validator": sender,
            "claim_id": claim_id,
            "verdict": verdict,
            "reasoning": reasoning,
            "submitted_at": self._now(),
        }

        evals = self._get_evaluations(claim_id)
        for e in evals:
            if e["validator"] == sender:
                raise gl.vm.UserError("Validator already submitted an evaluation")

        evals.append(json.dumps(eval_data))
        self._save_evaluations(claim_id, evals)
        self.evaluation_counter += u256(1)
        return verdict

    @gl.public.write
    def resolveConsensus(self, claim_id: str) -> str:
        claim = self._get_claim(claim_id)
        if claim is None:
            raise gl.vm.UserError("Claim not found")
        if claim["status"] != "VERIFYING":
            raise gl.vm.UserError("Claim must be VERIFYING to resolve consensus")

        evals = self._get_evaluations(claim_id)
        if len(evals) == 0:
            raise gl.vm.UserError("No evaluations submitted yet")

        counts = {"SUPPORTED": 0, "CONTRADICTED": 0, "INCONCLUSIVE": 0}
        for e_str in evals:
            e = json.loads(e_str)
            counts[e["verdict"]] += 1

        max_votes = max(counts.values())
        winners = [v for v, c in counts.items() if c == max_votes]

        if len(winners) == 1:
            final_verdict = winners[0]
        else:
            if set(winners) == {"SUPPORTED", "CONTRADICTED"}:
                final_verdict = "INCONCLUSIVE"
            else:
                final_verdict = "INCONCLUSIVE"

        result = {
            "claim_id": claim_id,
            "final_verdict": final_verdict,
            "vote_counts": counts,
            "evaluations": evals,
            "finalized_at": self._now(),
        }
        self._save_consensus(claim_id, result)

        claim["status"] = final_verdict
        self._save_claim(claim_id, claim)

        return final_verdict

    @gl.public.view
    def getClaim(self, claim_id: str) -> dict:
        claim = self._get_claim(claim_id)
        if claim is None:
            return {"exists": False}
        return claim

    @gl.public.view
    def getEvaluations(self, claim_id: str) -> dict:
        evals = self._get_evaluations(claim_id)
        return {"claim_id": claim_id, "count": len(evals), "evaluations": evals}

    @gl.public.view
    def getConsensus(self, claim_id: str) -> dict:
        result = self._get_consensus(claim_id)
        if result is None:
            return {"exists": False}
        return result

    @gl.public.view
    def getClaimCount(self) -> dict:
        return {"count": int(self.claim_counter)}

    @gl.public.view
    def getEvaluationCount(self) -> dict:
        return {"count": int(self.evaluation_counter)}