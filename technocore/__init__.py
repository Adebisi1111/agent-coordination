"""
Technocore integration for Agent Coordination.

Provides signed messaging between AI agents using Technocore.chat.
Each agent has an Ed25519 DID, and all task-related messages are signed
and posted to Technocore rooms for non-repudiation and auditability.
"""

import json
import time
import hashlib
import base64
import base58
from typing import Optional
from dataclasses import dataclass


@dataclass
class TechnocoreMessage:
    seq: int
    frm: str
    text: str
    room: str
    nonce: int
    sig: str


class AgentIdentity:
    """Manages an agent's Ed25519 DID for Technocore signing."""
    
    def __init__(self, seed_hex: str = None):
        if seed_hex:
            self._seed = bytes.fromhex(seed_hex)
        else:
            import os
            self._seed = os.urandom(32)
        self._private_key = None
        self._public_key = None
        self._did = None
        self._derive_keys()
    
    def _derive_keys(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        
        self._private_key = Ed25519PrivateKey.from_private_bytes(self._seed)
        self._public_key = self._private_key.public_key()
        
        # Generate did:key:z6Mk... (Ed25519 multicodec prefix)
        pub_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        # multicodec prefix for Ed25519: 0xed, 0x01, then 32 bytes
        multicodec = b'\xed\x01' + pub_bytes
        self._did = 'did:key:z6Mk' + base58.b58encode(multicodec).decode()
    
    @property
    def did(self) -> str:
        return self._did
    
    @property
    def seed_hex(self) -> str:
        return self._seed.hex()
    
    def sign(self, room: str, nonce: int, text: str) -> str:
        """Sign a message for Technocore."""
        payload = f"{room}|{nonce}|{text}"
        signature = self._private_key.sign(payload.encode())
        return base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
    
    @staticmethod
    def verify(did: str, room: str, nonce: int, text: str, sig: str) -> bool:
        """Verify a Technocore signature."""
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            
            # Extract public key from did:key:z6Mk...
            encoded = did.replace('did:key:z6Mk', '')
            multicodec = base58.b58decode(encoded)
            # Skip multicodec prefix (0xed, 0x01)
            pub_bytes = multicodec[2:]
            public_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
            
            payload = f"{room}|{nonce}|{text}"
            # Add padding back
            padding = 4 - len(sig) % 4
            if padding != 4:
                sig += '=' * padding
            signature = base64.urlsafe_b64decode(sig)
            
            public_key.verify(signature, payload.encode())
            return True
        except Exception:
            return False


class TechnocoreClient:
    """HTTP client for Technocore.chat API."""
    
    BASE_URL = "https://technocore.chat"
    
    def __init__(self, identity: AgentIdentity = None):
        self.identity = identity
    
    def _get(self, path: str, params: dict = None) -> str:
        import urllib.request
        import urllib.parse
        
        url = f"{self.BASE_URL}{path}"
        if params:
            url += '?' + urllib.parse.urlencode(params)
        
        req = urllib.request.Request(url, method='GET')
        req.add_header('Accept', 'text/plain')
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode()
    
    def read_room(self, room: str, since: int = 0) -> list:
        """Read messages from a room."""
        result = self._get(f"/room/{room}", {"since": since})
        messages = []
        for line in result.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 5:
                messages.append(TechnocoreMessage(
                    seq=int(parts[0]),
                    frm=parts[1],
                    text=parts[2],
                    room=room,
                    nonce=int(parts[3]),
                    sig=parts[4]
                ))
        return messages
    
    def say(self, room: str, text: str) -> Optional[int]:
        """Post a signed message to a room. Returns sequence number."""
        if not self.identity:
            raise ValueError("Identity required for posting")
        
        nonce = int(time.time() * 1e9)  # nanosecond nonce
        sig = self.identity.sign(room, nonce, text)
        
        import urllib.request
        import urllib.parse
        
        url = f"{self.BASE_URL}/room/{room}"
        data = urllib.parse.urlencode({
            'frm': self.identity.did,
            'text': text,
            'nonce': nonce,
            'sig': sig
        }).encode()
        
        req = urllib.request.Request(url, data=data, method='GET')
        req.add_header('Accept', 'text/plain')
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = resp.read().decode()
                # Response is the sequence number
                return int(result.strip())
        except Exception as e:
            print(f"Failed to post: {e}")
            return None
    
    def create_mailbox(self, name: str) -> bool:
        """Create a private mailbox (mb-p- prefix)."""
        if not self.identity:
            raise ValueError("Identity required")
        
        # Mailbox creation is just posting to it
        result = self.say(f"mb-p-{name}", f"Mailbox created by {self.identity.did}")
        return result is not None
    
    def create_task_room(self, task_id: str) -> str:
        """Create a room for a task and return the room name."""
        room = f"e-p-{task_id}"
        return room
    
    def post_task_announcement(self, task_id: str, description: str, reward: str):
        """Post a task to the lobby."""
        text = f"TASK_POSTED|{task_id}|{description}|{reward}"
        return self.say("lobby", text)
    
    def post_claim(self, task_id: str, agent_did: str):
        """Post a claim message."""
        room = self.create_task_room(task_id)
        text = f"TASK_CLAIMED|{task_id}|{agent_did}"
        return self.say(room, text)
    
    def post_delivery(self, task_id: str, agent_did: str, delivery_url: str):
        """Post a delivery message."""
        room = self.create_task_room(task_id)
        text = f"TASK_DELIVERED|{task_id}|{agent_did}|{delivery_url}"
        return self.say(room, text)
    
    def post_verification_result(self, task_id: str, verdict: str, reason: str):
        """Post verification result."""
        room = self.create_task_room(task_id)
        text = f"VERIFICATION_RESULT|{task_id}|{verdict}|{reason}"
        return self.say(room, text)
    
    def post_settlement(self, task_id: str, settlement_type: str, amount: str, recipient: str):
        """Post settlement receipt."""
        room = self.create_task_room(task_id)
        text = f"SETTLEMENT|{task_id}|{settlement_type}|{amount}|{recipient}"
        return self.say(room, text)


def hash_did_for_contract(did: str) -> str:
    """Hash a DID for on-chain storage (privacy-preserving)."""
    return '0x' + hashlib.sha256(did.encode()).hexdigest()


def verify_message(message: TechnocoreMessage) -> bool:
    """Verify a Technocore message signature."""
    return AgentIdentity.verify(
        message.frm,
        message.room,
        message.nonce,
        message.text,
        message.sig
    )
