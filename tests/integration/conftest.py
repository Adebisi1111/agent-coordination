"""Integration test fixtures for Agent Coordination System."""

import pytest
from gltest.clients import get_gl_client
from gltest.accounts import get_accounts
from gltest.contracts import Contract


# Existing deployed contract on Studio Network
STUDIO_CONTRACT_ADDRESS = "0x50BD0a5C0AF880c5DC5DDbc899F8B6E2e7Af48a1"


@pytest.fixture(scope="session")
def integration_vm():
    """Provide integration VM with balance checking."""
    client = get_gl_client()
    
    class IntegrationVM:
        def __init__(self, c):
            self.client = c
        
        def get_balance(self, account):
            addr = account.address if hasattr(account, 'address') else account
            return self.client.get_balance(addr)
    
    return IntegrationVM(client)


@pytest.fixture(scope="session")
def integration_deploy():
    """Use existing deployed contract."""
    def _deploy(contract_path):
        client = get_gl_client()
        # Get schema from existing deployed contract
        schema = client.get_contract_schema(STUDIO_CONTRACT_ADDRESS)
        # Use existing deployed contract
        return Contract.new(
            address=STUDIO_CONTRACT_ADDRESS,
            schema=schema,
            account=get_accounts()[0]
        )
    return _deploy


@pytest.fixture(scope="session")
def integration_alice():
    """First test account."""
    accounts = get_accounts()
    return accounts[0]


@pytest.fixture(scope="session")
def integration_bob():
    """Second test account."""
    accounts = get_accounts()
    return accounts[1]
