from datetime import timedelta, datetime
import pytest
from utils import *
from test_VPC import vpc

@pytest.fixture()
def balance(web3, parties):
    return [web3.eth.getBalance(party) for party in parties]

@pytest.fixture()
def msc(web3, chain, parties, setup):
    libSignaturesMock = chain.provider.get_or_deploy_contract('LibSignaturesMock')[0]
    return chain.provider.get_or_deploy_contract('MSContract', deploy_args=[parties[alice], parties[bob], mscId, libSignaturesMock.address])[0]

def check_balance(web3, expected):
    for party, exp_bal in expected:
        assert abs(exp_bal - web3.eth.getBalance(web3.eth.accounts[party])) < 10**7

def check_msc_balance(web3, chain, msc, expected, parties=[alice, bob]):
    for party, name in zip(parties, ['alice', 'bob']):
        assert call_transaction(web3, chain, msc, name, party, arguments=[])[0][1] == expected[party]

def test_MSContract_honest_simple(web3, chain, parties, msc, balance):
    for party in [alice, bob]:
        call_transaction(web3, chain, msc, 'confirm', party, arguments=[], value=cash[party])
    check_balance(web3, [(p, balance[p] - cash[p]) for p in [alice, bob]])
    check_msc_balance(web3, chain, msc, cash)
    for party in [alice, bob]:
        call_transaction(web3, chain, msc, 'close', party, arguments=[])
    check_balance(web3, [(p, balance[p]) for p in [alice, bob]])

def test_MSContract_vpc_honest_all(web3, chain, parties, vpc, balance, setup):
    libSignaturesMock = chain.provider.get_or_deploy_contract('LibSignaturesMock')[0]
    users = [[alice, ingrid], [ingrid, bob]]
    cashs = [{alice: 33 * 10**9, ingrid: 88 * 10**9}, {ingrid: 77 * 10**9, bob: 21 * 10**9}]
    change = [10 * 10**9, 13 * 10**9]
    mscs = []
    for mscId, u in enumerate(users):
        mscs.append(chain.provider.deploy_contract('MSContract', deploy_args=[parties[u[0]], parties[u[1]], mscId, libSignaturesMock.address])[0])
    check_balance(web3, [(p, balance[p]) for p in [alice, ingrid, bob]])

    for msc, cash, u in zip(mscs, list(cashs), users):
        for party in u:
            call_transaction(web3, chain, msc, 'confirm', party, arguments=[], value=cash[party])
        check_msc_balance(web3, chain, msc, cash, u)
        for party in u:
            call_transaction(web3, chain, msc, 'stateRegister', party, arguments=[nid, vpc.address, sid] + vpc_parties(web3) + change + [version] + ['\x01'] * 2)
    minus = {alice: cashs[0][alice], bob: cashs[1][bob], ingrid: cashs[0][ingrid] + cashs[1][ingrid]}
    check_balance(web3, [(p, balance[p] - minus[p]) for p in [alice, bob, ingrid]])
    for party in [alice, bob]:
        call_transaction(web3, chain, vpc, 'close', party, arguments=vpc_parties(web3) + [sid, version] + change[::-1] + ['\x01'] * 2)
    check_balance(web3, [(p, balance[p] - minus[p]) for p in [alice, bob, ingrid]])
    for msc, cash, u in zip(mscs, list(cashs), users):
        call_transaction(web3, chain, msc, 'execute', ingrid, arguments=[nid])
        for party in u:
            call_transaction(web3, chain, msc, 'close', party, arguments=[])

    difference = {alice: -change[0] + change[1], ingrid: 0, bob: change[0] - change[1]}
    check_balance(web3, [(p, balance[p] + difference[p]) for p in [alice, bob, ingrid]])

def test_MSContract_refund(web3, chain, parties, msc, balance):
    call_transaction(web3, chain, msc, 'confirm', alice, arguments=[], value=cash[alice])
    check_balance(web3, [(p, balance[p] - cash[p]) for p in [alice]])
    t = datetime.now()
    t = move_time(web3, t, timedelta(minutes=60))
    call_transaction(web3, chain, msc, 'refund', alice, arguments=[])
    check_balance(web3, [(p, balance[p] - cash[p]) for p in [alice]])
    t = move_time(web3, t, timedelta(minutes=60))
    call_transaction(web3, chain, msc, 'refund', alice, arguments=[])
    check_balance(web3, [(p, balance[p]) for p in [alice]])

def test_MSContract_finalizeClose(web3, chain, parties, msc, balance):
    for party in [alice, bob]:
        call_transaction(web3, chain, msc, 'confirm', party, arguments=[], value=cash[party])
    call_transaction(web3, chain, msc, 'close', alice, arguments=[])
    t = datetime.now()
    t = move_time(web3, t, timedelta(minutes=200))
    call_transaction(web3, chain, msc, 'finalizeClose', alice, arguments=[])
    check_balance(web3, [(p, balance[p] - cash[p]) for p in [alice]])
    t = move_time(web3, t, timedelta(minutes=200))
    call_transaction(web3, chain, msc, 'finalizeClose', alice, arguments=[])
    check_balance(web3, [(p, balance[p]) for p in [alice]])

def test_MSContract_vpc_finalizeRegister(web3, chain, parties, msc, vpc, balance):
    change = [7 * 10**9, 3 * 10**9]
    for party in [alice, bob]:
        call_transaction(web3, chain, msc, 'confirm', party, arguments=[], value=cash[party])
    call_transaction(web3, chain, msc, 'stateRegister', alice, arguments=[nid, vpc.address, sid] + vpc_parties(web3) + change + [version] + ['\x01'] * 2)
    call_transaction(web3, chain, vpc, 'close', alice, arguments=vpc_parties(web3) + [sid, version] + change + ['\x01'] * 2)
    t = datetime.now()
    t = move_time(web3, t, timedelta(minutes=120))
    call_transaction(web3, chain, msc, 'finalizeRegister', alice, arguments=[nid])
    call_transaction(web3, chain, msc, 'execute', alice, arguments=[nid])
    for party in [alice, bob]:
        call_transaction(web3, chain, msc, 'close', party, arguments=[])
    check_balance(web3, [(p, balance[p]) for p in [alice]])

def test_MSContract_stateRegister_diffrent_versions(web3, chain, parties, msc, vpc, balance):
    pass  # TODO
