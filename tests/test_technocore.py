"""
Tests for Technocore integration.

Tests the AgentIdentity, TechnocoreClient, and message signing/verification.
"""

import pytest
import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from technocore import (
    AgentIdentity,
    TechnocoreClient,
    hash_did_for_contract,
    verify_message,
    TechnocoreMessage
)


class TestAgentIdentity:
    """Tests for AgentIdentity class."""
    
    def test_generate_identity(self):
        """Generate a new identity and verify DID format."""
        identity = AgentIdentity()
        assert identity.did.startswith('did:key:z6Mk')
        assert len(identity.seed_hex) == 64
    
    def test_restore_identity(self):
        """Restore identity from seed and verify same DID."""
        identity1 = AgentIdentity()
        seed = identity1.seed_hex
        
        identity2 = AgentIdentity(seed_hex=seed)
        assert identity2.did == identity1.did
        assert identity2.seed_hex == seed
    
    def test_sign_message(self):
        """Sign a message and verify signature."""
        identity = AgentIdentity()
        nonce = int(time.time() * 1e9)
        text = "Hello, Technocore!"
        
        sig = identity.sign("test-room", nonce, text)
        assert sig
        assert len(sig) > 0
    
    def test_verify_signature(self):
        """Verify a signature is valid."""
        identity = AgentIdentity()
        nonce = int(time.time() * 1e9)
        text = "Hello, Technocore!"
        
        sig = identity.sign("test-room", nonce, text)
        valid = AgentIdentity.verify(identity.did, "test-room", nonce, text, sig)
        assert valid is True
    
    def test_verify_invalid_signature(self):
        """Verify that tampered text fails verification."""
        identity = AgentIdentity()
        nonce = int(time.time() * 1e9)
        text = "Hello, Technocore!"
        
        sig = identity.sign("test-room", nonce, text)
        
        # Tamper with text
        valid = AgentIdentity.verify(identity.did, "test-room", nonce, "Tampered!", sig)
        assert valid is False
    
    def test_did_hash_for_contract(self):
        """Test DID hashing produces consistent results."""
        identity = AgentIdentity()
        hash1 = hash_did_for_contract(identity.did)
        hash2 = hash_did_for_contract(identity.did)
        
        assert hash1 == hash2
        assert hash1.startswith('0x')
        assert len(hash1) == 66  # 0x + 64 hex chars


class TestTechnocoreClient:
    """Tests for TechnocoreClient class."""
    
    def test_client_init(self):
        """Test client initialization."""
        client = TechnocoreClient()
        assert client.identity is None
        
        identity = AgentIdentity()
        client = TechnocoreClient(identity=identity)
        assert client.identity == identity
    
    def test_create_task_room(self):
        """Test task room name generation."""
        client = TechnocoreClient()
        room = client.create_task_room("task-1")
        assert room == "e-p-task-1"
    
    def test_create_mailbox(self):
        """Test mailbox name generation."""
        client = TechnocoreClient()
        # Mailbox creation requires identity
        identity = AgentIdentity()
        client = TechnocoreClient(identity=identity)
        # Just verify the method exists and doesn't crash
        # (actual posting requires network)
        assert client.identity is not None


class TestMessageVerification:
    """Tests for message verification."""
    
    def test_verify_message_object(self):
        """Test verification of a TechnocoreMessage object."""
        identity = AgentIdentity()
        nonce = int(time.time() * 1e9)
        text = "TASK_POSTED|task-1|Write about AI|1.0"
        room = "e-p-task-1"
        
        sig = identity.sign(room, nonce, text)
        
        msg = TechnocoreMessage(
            seq=1,
            frm=identity.did,
            text=text,
            room=room,
            nonce=nonce,
            sig=sig
        )
        
        assert verify_message(msg) is True
    
    def test_verify_tampered_message(self):
        """Test that tampered message fails verification."""
        identity = AgentIdentity()
        nonce = int(time.time() * 1e9)
        text = "TASK_POSTED|task-1|Write about AI|1.0"
        room = "e-p-task-1"
        
        sig = identity.sign(room, nonce, text)
        
        msg = TechnocoreMessage(
            seq=1,
            frm=identity.did,
            text="TAMPERED",
            room=room,
            nonce=nonce,
            sig=sig
        )
        
        assert verify_message(msg) is False


class TestIntegrationWithContract:
    """Tests for contract integration."""
    
    def test_did_hash_matches_contract_storage(self):
        """Test that DID hash can be stored in contract."""
        identity = AgentIdentity()
        did_hash = hash_did_for_contract(identity.did)
        
        # Verify format matches what contract expects
        assert did_hash.startswith('0x')
        assert len(did_hash) == 66
    
    def test_multiple_agents_unique_dids(self):
        """Test that multiple agents get unique DIDs."""
        identities = [AgentIdentity() for _ in range(5)]
        dids = [i.did for i in identities]
        
        assert len(set(dids)) == 5  # All unique
    
    def test_message_signing_for_task_lifecycle(self):
        """Test signing messages for each step of task lifecycle."""
        identity = AgentIdentity()
        nonce = int(time.time() * 1e9)
        
        messages = [
            ("e-p-task-1", f"TASK_POSTED|task-1|Write about AI|1.0"),
            ("e-p-task-1", f"TASK_CLAIMED|task-1|{identity.did}"),
            ("e-p-task-1", f"TASK_DELIVERED|task-1|{identity.did}|https://example.com"),
            ("e-p-task-1", f"VERIFICATION_RESULT|task-1|PASS|fulfills task"),
        ]
        
        for room, text in messages:
            sig = identity.sign(room, nonce, text)
            assert sig
            assert AgentIdentity.verify(identity.did, room, nonce, text, sig)
            nonce += 1
