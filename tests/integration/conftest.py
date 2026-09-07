"""Integration test fixtures for Agent Coordination System."""

import pytest
from gltest.clients import get_gl_client
from gltest.accounts import get_accounts
from gltest.contracts import Contract


# Existing deployed contract on Bradbury
BRADBURY_CONTRACT_ADDRESS = "0x471CFDa12A5C1a75279FC65a506beD210c6415d2"


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
        schema = client.get_contract_schema(BRADBURY_CONTRACT_ADDRESS)
        # Use existing deployed contract
        return Contract.new(
            address=BRADBURY_CONTRACT_ADDRESS,
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
