"""Integration test fixtures for Agent Coordination System."""

import pytest
from gltest.clients import get_gl_client
from gltest.accounts import get_accounts
from gltest.contracts import Contract


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
    """Deploy a fresh contract for testing."""
    def _deploy(contract_path):
        client = get_gl_client()
        account = get_accounts()[0]
        contract = client.deploy_contract(
            contract_path=contract_path,
            account=account,
        )
        return contract
    return _deploy


@pytest.fixture(scope="session")
def integration_alice():
    """First test account - agent."""
    accounts = get_accounts()
    return accounts[0]


@pytest.fixture(scope="session")
def integration_bob():
    """Second test account - poster."""
    accounts = get_accounts()
    return accounts[1]
