from datetime import timedelta, datetime
from time import sleep
import pytest
import ethereum.tester

sid = 42
version = 15
cash = [23, 11]
cash2 = [11, 23]

alice = 0
bob = 1
ingrid = 2
eve = 3

@pytest.fixture()
def vpc(web3, chain):
    t = datetime.now()
    web3.testing.timeTravel(int(t.timestamp()))
    libSignaturesMock = chain.provider.get_or_deploy_contract('LibSignaturesMock')[0]
    return chain.provider.get_or_deploy_contract('VPC', deploy_args=[libSignaturesMock.address])[0]

@pytest.fixture()
def parties(web3):
    return web3.eth.accounts

def set_sender(web3, party):
    web3.eth.defaultAccount = web3.eth.accounts[party]

def call_transaction(web3, chain, txn, sender, wait, *args, **kwargs):
    set_sender(web3, sender)
    party = parties(web3)
    result, txn_hash = txn(party[alice], party[ingrid], party[bob], *args, **kwargs)
    if wait:
        txn = chain.wait.for_receipt(txn_hash)
        return result, txn
    else:
        return result, txn_hash

def call_close(web3, chain, vpc, sender, version=version, cash=cash, sig=[True, True], sid=sid, wait=True):
    sig = [chr(x) for x in sig]
    return call_transaction(web3, chain, lambda *args: (vpc.call().close(*args), vpc.transact().close(*args)), sender, wait, sid, version, cash[alice], cash[bob], sig[alice], sig[bob])

def call_finalize(web3, chain, vpc, sender, sid=sid, wait=True):
    return call_transaction(web3, chain, lambda *args: (vpc.call().finalize(*args), vpc.transact().finalize(*args)), sender, wait, sid)

def move_time(web3, t, delta):
    small_delta = timedelta(seconds=20)
    t += delta - small_delta
    web3.testing.timeTravel(int(t.timestamp()))
    t += small_delta
    web3.testing.timeTravel(int(t.timestamp()))
    return t



def test_VPC_honest(web3, chain, parties, vpc):
    call_close(web3, chain, vpc, alice)
    call_close(web3, chain, vpc, bob)
    assert call_finalize(web3, chain, vpc, ingrid)[0] == [True] + cash

def test_VPC_older_sig(web3, chain, parties, vpc):
    call_close(web3, chain, vpc, alice)
    call_close(web3, chain, vpc, bob, version-1, cash2)
    assert call_finalize(web3, chain, vpc, ingrid)[0] == [True] + cash

def test_VPC_newer_sig(web3, chain, parties, vpc):
    call_close(web3, chain, vpc, alice)
    assert call_finalize(web3, chain, vpc, alice)[0][0] == False
    call_close(web3, chain, vpc, bob, version+1, cash2)
    assert call_finalize(web3, chain, vpc, ingrid)[0] == [True] + cash2

def test_VPC_ingrid_starts(web3, chain, parties, vpc):
    call_close(web3, chain, vpc, ingrid, version-1, cash2)
    assert call_finalize(web3, chain, vpc, alice)[0][0] == False
    call_close(web3, chain, vpc, alice)
    assert call_finalize(web3, chain, vpc, alice)[0][0] == False
    call_close(web3, chain, vpc, bob)
    assert call_finalize(web3, chain, vpc, ingrid)[0] == [True] + cash

def test_VPC_no_change(web3, chain, parties, vpc):
    call_close(web3, chain, vpc, alice)
    call_close(web3, chain, vpc, bob)
    call_close(web3, chain, vpc, alice, version+1, cash2)
    assert call_finalize(web3, chain, vpc, ingrid)[0] == [True] + cash

def test_VPC_only_one_party(web3, chain, parties, vpc):
    t = datetime.now()
    for party in [alice, bob, ingrid]:
        call_close(web3, chain, vpc, party, sid=party)
        t = move_time(web3, t, timedelta(minutes=25))
        assert call_finalize(web3, chain, vpc, ingrid, sid=party)[0] == [True] + cash

def test_VPC_validity(web3, chain, parties, vpc):
    t = datetime.now()
    call_close(web3, chain, vpc, ingrid)
    assert call_finalize(web3, chain, vpc, alice)[0][0] == False
    t = move_time(web3, t, timedelta(minutes=5))
    assert call_finalize(web3, chain, vpc, alice)[0][0] == False
    call_close(web3, chain, vpc, alice)
    assert call_finalize(web3, chain, vpc, alice)[0][0] == False
    t = move_time(web3, t, timedelta(minutes=10))
    call_close(web3, chain, vpc, bob)
    assert call_finalize(web3, chain, vpc, alice)[0][0] == False
    t = move_time(web3, t, timedelta(minutes=10))
    assert call_finalize(web3, chain, vpc, alice)[0] == [True] + cash



@pytest.mark.xfail(raises=ethereum.tester.TransactionFailed, strict=True)
def test_VPC_wrong_sender(chain, web3, vpc):
    call_close(web3, chain, vpc, eve)

