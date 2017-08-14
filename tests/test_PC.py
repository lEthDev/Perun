from datetime import timedelta, datetime
import pytest
import ethereum.tester
from utils import *

@pytest.fixture()
def pc(web3, chain, setup):
    libSignaturesMock = chain.provider.get_or_deploy_contract('LibSignaturesMock')[0]
    return chain.provider.get_or_deploy_contract('PC', deploy_args=[libSignaturesMock.address])[0]


def call_close(web3, chain, pc, sender, version=version, cash=cash, sig=[True, True], sid=sid, wait=True):
    sig = [chr(x) for x in sig]
    return call_transaction(web3, chain, pc, 'close', sender, arguments = [pc_parties(web3), sid, version] + list(cash) + sig, wait=wait)

def call_finalize(web3, chain, pc, sender, sid=sid, wait=True):
    return call_transaction(web3, chain, pc, 'finalize', sender, arguments = [pc_parties(web3), sid], wait=wait)


def test_PC_honest(web3, chain, parties, pc):
    call_close(web3, chain, pc, alice)
    call_close(web3, chain, pc, bob)
    assert call_finalize(web3, chain, pc, alice)[0] == [True] + list(cash)

def test_PC_older_sig(web3, chain, parties, pc):
    call_close(web3, chain, pc, alice)
    call_close(web3, chain, pc, bob, version-1, list(cash2))
    assert call_finalize(web3, chain, pc, alice)[0] == [True] + list(cash)

def test_PC_newer_sig(web3, chain, parties, pc):
    call_close(web3, chain, pc, alice)
    assert call_finalize(web3, chain, pc, alice)[0][0] == False
    call_close(web3, chain, pc, bob, version+1, list(cash2))
    assert call_finalize(web3, chain, pc, bob)[0] == [True] + list(cash2)

def test_PC_no_change(web3, chain, parties, pc):
    call_close(web3, chain, pc, alice)
    call_close(web3, chain, pc, bob)
    call_close(web3, chain, pc, alice, version+1, list(cash2))
    assert call_finalize(web3, chain, pc, bob)[0] == [True] + list(cash)

def test_PC_only_one_party(web3, chain, parties, pc):
    t = datetime.now()
    for party in [alice, bob]:
        call_close(web3, chain, pc, party, sid=party)
        t = move_time(web3, t, timedelta(minutes=25))
        assert call_finalize(web3, chain, pc, party, sid=party)[0] == [True] + list(cash)

def test_PC_validity(web3, chain, parties, pc):
    t = datetime.now()
    assert call_finalize(web3, chain, pc, alice)[0][0] == False
    call_close(web3, chain, pc, alice)
    assert call_finalize(web3, chain, pc, alice)[0][0] == False
    t = move_time(web3, t, timedelta(minutes=10))
    call_close(web3, chain, pc, alice)
    assert call_finalize(web3, chain, pc, alice)[0][0] == False
    t = move_time(web3, t, timedelta(minutes=15))
    assert call_finalize(web3, chain, pc, alice)[0] == [True] + list(cash)

@pytest.mark.xfail(raises=ethereum.tester.TransactionFailed, strict=True)
def test_PC_wrong_sender(chain, web3, pc):
    call_close(web3, chain, pc, eve)

