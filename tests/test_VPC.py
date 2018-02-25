from datetime import timedelta, datetime
from collections import defaultdict
import pytest
from ethereum import tester
from utils import *

@pytest.fixture()
def vpc(web3, chain, setup):
    libSignaturesMock = chain.provider.get_or_deploy_contract('LibSignaturesMock')[0]
    return chain.provider.get_or_deploy_contract('VPC', deploy_args=[libSignaturesMock.address])[0]


def call_close(web3, chain, vpc, sender, costs, version=version, cash=cash, sig=[True, True], sid=sid, wait=True):
    sig = [chr(x) for x in sig]
    return call_transaction(web3, chain, vpc, 'vpc', 'close', sender, arguments = vpc_parties(web3) + [sid, version] + list(cash) + sig, wait=wait, costs=costs)

def call_finalize(web3, chain, vpc, sender, costs, sid=sid, wait=True):
    return call_transaction(web3, chain, vpc, 'vpc', 'finalize', sender, arguments = vpc_parties(web3) + [sid], wait=wait, costs=costs)


def test_VPC_honest(web3, chain, parties, vpc):
    costs = defaultdict(int)
    call_close(web3, chain, vpc, alice, costs=costs)
    call_close(web3, chain, vpc, bob, costs=costs)
    assert call_finalize(web3, chain, vpc, ingrid, costs=costs)[0] == [True] + list(cash)
    print_costs(costs, 'VPC Honest')

def test_VPC_older_version(web3, chain, parties, vpc):
    costs = defaultdict(int)
    call_close(web3, chain, vpc, alice, costs=costs)
    call_close(web3, chain, vpc, bob, version=version-1, cash=list(cash2), costs=costs)
    assert call_finalize(web3, chain, vpc, ingrid, costs=costs)[0] == [True] + list(cash)
    print_costs(costs, 'VPC Older version')

def test_VPC_newer_version(web3, chain, parties, vpc):
    costs = defaultdict(int)
    call_close(web3, chain, vpc, alice, costs=costs)
    assert call_finalize(web3, chain, vpc, alice, costs=costs)[0][0] == False
    call_close(web3, chain, vpc, bob, version=version+1, cash=list(cash2), costs=costs)
    assert call_finalize(web3, chain, vpc, ingrid, costs=costs)[0] == [True] + list(cash2)
    print_costs(costs, 'VPC Newer version')

def test_VPC_ingrid_starts(web3, chain, parties, vpc):
    costs = defaultdict(int)
    call_close(web3, chain, vpc, ingrid, version=version-1, cash=list(cash2), costs=costs)
    assert call_finalize(web3, chain, vpc, alice, costs=costs)[0][0] == False
    call_close(web3, chain, vpc, alice, costs=costs)
    assert call_finalize(web3, chain, vpc, alice, costs=costs)[0][0] == False
    call_close(web3, chain, vpc, bob, costs=costs)
    assert call_finalize(web3, chain, vpc, ingrid, costs=costs)[0] == [True] + list(cash)
    print_costs(costs, 'VPC Ingrid starts')

def test_VPC_no_change(web3, chain, parties, vpc):
    costs = defaultdict(int)
    call_close(web3, chain, vpc, alice, costs=costs)
    call_close(web3, chain, vpc, bob, costs=costs)
    call_close(web3, chain, vpc, alice, version=version+1, cash=list(cash2), costs=costs)
    assert call_finalize(web3, chain, vpc, ingrid, costs=costs)[0] == [True] + list(cash)
    print_costs(costs, 'VPC No change')

def test_VPC_only_one_party(web3, chain, parties, vpc):
    costs = defaultdict(int)
    t = datetime.now()
    for party in [alice, bob, ingrid]:
        call_close(web3, chain, vpc, party, sid=party, costs=costs)
        t = move_time(web3, t, timedelta(minutes=25))
        assert call_finalize(web3, chain, vpc, ingrid, sid=party, costs=costs)[0] == [True] + list(cash)
    print_costs(costs, 'VPC Only one party')

def test_VPC_validity(web3, chain, parties, vpc):
    costs = defaultdict(int)
    t = datetime.now()
    call_close(web3, chain, vpc, ingrid, costs=costs)
    assert call_finalize(web3, chain, vpc, alice, costs=costs)[0][0] == False
    t = move_time(web3, t, timedelta(minutes=5))
    assert call_finalize(web3, chain, vpc, alice, costs=costs)[0][0] == False
    call_close(web3, chain, vpc, alice, costs=costs)
    assert call_finalize(web3, chain, vpc, alice, costs=costs)[0][0] == False
    t = move_time(web3, t, timedelta(minutes=10))
    call_close(web3, chain, vpc, bob, costs=costs)
    assert call_finalize(web3, chain, vpc, alice, costs=costs)[0][0] == False
    t = move_time(web3, t, timedelta(minutes=10))
    assert call_finalize(web3, chain, vpc, alice, costs=costs)[0] == [True] + list(cash)
    print_costs(costs, 'VPC Validity')

@pytest.mark.xfail(raises=tester.TransactionFailed, strict=True)
def test_VPC_wrong_sender(chain, web3, vpc):
    costs = defaultdict(int)
    call_close(web3, chain, vpc, eve, costs=costs)
    print_costs(costs, 'VPC Wrong sender')

