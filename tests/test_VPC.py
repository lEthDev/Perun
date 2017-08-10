from datetime import timedelta, datetime
from time import sleep
import pytest
import ethereum.tester
from utils import *

@pytest.fixture()
def vpc(web3, chain, now):
    libSignaturesMock = chain.provider.get_or_deploy_contract('LibSignaturesMock')[0]
    return chain.provider.get_or_deploy_contract('VPC', deploy_args=[libSignaturesMock.address])[0]


def call_close(web3, chain, vpc, sender, version=version, cash=cash, sig=[True, True], sid=sid, wait=True):
    sig = [chr(x) for x in sig]
    return call_transaction(web3, chain, vpc, 'close', sender, arguments = vpc_parties(web3) + [sid, version] + cash + sig, wait=wait)

def call_finalize(web3, chain, vpc, sender, sid=sid, wait=True):
    return call_transaction(web3, chain, vpc, 'finalize', sender, arguments = vpc_parties(web3) + [sid], wait=wait)


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

