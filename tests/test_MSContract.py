from datetime import timedelta, datetime
import pytest
from utils import *
from test_VPC import vpc

@pytest.fixture()
def msc(web3, chain, parties, setup):
    libSignaturesMock = chain.provider.get_or_deploy_contract('LibSignaturesMock')[0]
    return chain.provider.get_or_deploy_contract('MSContract', deploy_args=[parties[alice], parties[bob], libSignaturesMock.address])[0]

def test_MSContract_honest_simple(web3, chain, parties, msc):
    balance = {}
    for party in [alice, bob]:
        balance[party] = web3.eth.getBalance(parties[party])
        call_transaction(web3, chain, msc, 'confirm', party, arguments=[], value=cash[party])
        assert web3.eth.getBalance(parties[party]) < balance[party] - cash[party]
    for party in [alice, bob]:
        assert call_transaction(web3, chain, msc, party_name[party], party, arguments=[])[0][1] == cash[party]
    for party in [alice, bob]:
        call_transaction(web3, chain, msc, 'close', party, arguments=[])
    for party in [alice, bob]:
        assert web3.eth.getBalance(parties[party]) > balance[party] - cash[party]

def test_MSContract_refund(web3, chain, parties, msc):
    balance = web3.eth.getBalance(parties[alice])
    call_transaction(web3, chain, msc, 'confirm', alice, arguments=[], value=cash[alice])
    assert web3.eth.getBalance(parties[alice]) < balance - cash[alice]
    t = datetime.now()
    t = move_time(web3, t, timedelta(minutes=60))
    call_transaction(web3, chain, msc, 'refund', alice, arguments=[])
    assert web3.eth.getBalance(parties[alice]) < balance - cash[alice]
    t = move_time(web3, t, timedelta(minutes=60))
    call_transaction(web3, chain, msc, 'refund', alice, arguments=[])
    assert web3.eth.getBalance(parties[alice]) > balance - cash[alice]

def test_MSContract_finalizeClose(web3, chain, parties, msc):
    balance = {}
    for party in [alice, bob]:
        balance[party] = web3.eth.getBalance(parties[party])
        call_transaction(web3, chain, msc, 'confirm', party, arguments=[], value=cash[party])
    call_transaction(web3, chain, msc, 'close', alice, arguments=[])
    t = datetime.now()
    t = move_time(web3, t, timedelta(minutes=200))
    call_transaction(web3, chain, msc, 'finalizeClose', alice, arguments=[])
    assert web3.eth.getBalance(parties[alice]) < balance[alice] - cash[alice]
    t = move_time(web3, t, timedelta(minutes=200))
    call_transaction(web3, chain, msc, 'finalizeClose', alice, arguments=[])
    assert web3.eth.getBalance(parties[alice]) > balance[alice] - cash[alice]


