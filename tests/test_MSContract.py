from datetime import timedelta, datetime
from collections import defaultdict
import pytest
from utils import *
from test_VPC import vpc

@pytest.fixture()
def balance(web3, parties):
    return [web3.eth.getBalance(party) for party in parties]

@pytest.fixture()
def costs():
    return defaultdict(int)

def deploy_msc(chain, u1, u2, libSignaturesAddr, costs, sender=alice):
    msc = chain.provider.deploy_contract('MSContract', deploy_args=[u1, u2, mscId, libSignaturesAddr])
    txn = chain.wait.for_receipt(msc[1])
    costs[sender] += txn.gasUsed
    print(party_name[sender] + ':', "msc deploy cost: ", txn.gasUsed)
    return msc[0]

@pytest.fixture()
def msc(web3, chain, parties, setup, costs):
    libSignaturesMock = chain.provider.get_or_deploy_contract('LibSignaturesMock')[0]
    return deploy_msc(chain, parties[alice], parties[bob], libSignaturesMock.address, costs)

def check_balance(web3, expected):
    for party, exp_bal in expected:
        assert abs(exp_bal - web3.eth.getBalance(web3.eth.accounts[party])) < 10**7

def check_msc_balance(web3, chain, msc, expected, costs, parties=[alice, bob]):
    for party, name in zip(parties, ['alice', 'bob']):
        assert call_transaction(web3, chain, msc, 'msc', name, party, arguments=[], costs=costs)[0][1] == expected[party]


def test_MSContract_honest_simple(web3, chain, parties, msc, balance, costs):
    for party in [alice, bob]:
        call_transaction(web3, chain, msc, 'msc', 'confirm', party, arguments=[], value=cash[party], costs=costs)
    check_balance(web3, [(p, balance[p] - cash[p]) for p in [alice, bob]])
    check_msc_balance(web3, chain, msc, cash, costs=costs)
    for party in [alice, bob]:
        call_transaction(web3, chain, msc, 'msc', 'close', party, arguments=[], costs=costs)
    check_balance(web3, [(p, balance[p]) for p in [alice, bob]])
    print_costs(costs, 'MSC Honest simple')

def test_MSContract_vpc_honest_all(web3, chain, parties, vpc, balance, setup, costs):
    libSignaturesMock = chain.provider.get_or_deploy_contract('LibSignaturesMock')[0]
    users = [[alice, ingrid], [ingrid, bob]]
    cashs = [{alice: 33 * 10**9, ingrid: 88 * 10**9}, {ingrid: 77 * 10**9, bob: 21 * 10**9}]
    change = [10 * 10**9, 13 * 10**9]
    mscs = []
    for mscId, u in enumerate(users):
        mscs.append(deploy_msc(chain, parties[u[0]], parties[u[1]], libSignaturesMock.address, costs, u[0]))
    check_balance(web3, [(p, balance[p]) for p in [alice, ingrid, bob]])

    for msc, cash, u in zip(mscs, list(cashs), users):
        for party in u:
            call_transaction(web3, chain, msc, 'msc', 'confirm', party, arguments=[], value=cash[party], costs=costs)
        check_msc_balance(web3, chain, msc, cash, parties=u, costs=costs)
        for party in u:
            call_transaction(web3, chain, msc, 'msc', 'stateRegister', party, arguments=[nid, vpc.address, sid] + vpc_parties(web3) + change + [version] + ['\x01'] * 2, costs=costs)
    minus = {alice: cashs[0][alice], bob: cashs[1][bob], ingrid: cashs[0][ingrid] + cashs[1][ingrid]}
    check_balance(web3, [(p, balance[p] - minus[p]) for p in [alice, bob, ingrid]])
    for party in [alice, bob]:
        call_transaction(web3, chain, vpc, 'vpc', 'close', party, arguments=vpc_parties(web3) + [sid, version] + change[::-1] + ['\x01'] * 2, costs=costs)
    check_balance(web3, [(p, balance[p] - minus[p]) for p in [alice, bob, ingrid]])
    for msc, cash, u in zip(mscs, list(cashs), users):
        call_transaction(web3, chain, msc, 'msc', 'execute', ingrid, arguments=[nid], costs=costs)
        for party in u:
            call_transaction(web3, chain, msc, 'msc', 'close', party, arguments=[], costs=costs)

    difference = {alice: -change[0] + change[1], ingrid: 0, bob: change[0] - change[1]}
    check_balance(web3, [(p, balance[p] + difference[p]) for p in [alice, bob, ingrid]])
    print_costs(costs, 'MSC Honest all')

def test_MSContract_refund(web3, chain, parties, msc, balance, costs):
    call_transaction(web3, chain, msc, 'msc', 'confirm', alice, arguments=[], value=cash[alice], costs=costs)
    check_balance(web3, [(p, balance[p] - cash[p]) for p in [alice]])
    t = datetime.now()
    t = move_time(web3, t, timedelta(minutes=60))
    call_transaction(web3, chain, msc, 'msc', 'refund', alice, arguments=[], costs=costs)
    check_balance(web3, [(p, balance[p] - cash[p]) for p in [alice]])
    t = move_time(web3, t, timedelta(minutes=60))
    call_transaction(web3, chain, msc, 'msc', 'refund', alice, arguments=[], costs=costs)
    check_balance(web3, [(p, balance[p]) for p in [alice]])
    print_costs(costs, 'MSC Refund')

def test_MSContract_finalizeClose(web3, chain, parties, msc, balance, costs):
    for party in [alice, bob]:
        call_transaction(web3, chain, msc, 'msc', 'confirm', party, arguments=[], value=cash[party], costs=costs)
    call_transaction(web3, chain, msc, 'msc', 'close', alice, arguments=[], costs=costs)
    t = datetime.now()
    t = move_time(web3, t, timedelta(minutes=200))
    call_transaction(web3, chain, msc, 'msc', 'finalizeClose', alice, arguments=[], costs=costs)
    check_balance(web3, [(p, balance[p] - cash[p]) for p in [alice]])
    t = move_time(web3, t, timedelta(minutes=200))
    call_transaction(web3, chain, msc, 'msc', 'finalizeClose', alice, arguments=[], costs=costs)
    check_balance(web3, [(p, balance[p]) for p in [alice]])
    print_costs(costs, 'MSC Finalize close')

def test_MSContract_vpc_finalizeRegister(web3, chain, parties, msc, vpc, balance, costs):
    change = [7 * 10**9, 3 * 10**9]
    for party in [alice, bob]:
        call_transaction(web3, chain, msc, 'msc', 'confirm', party, arguments=[], value=cash[party], costs=costs)
    call_transaction(web3, chain, msc, 'msc', 'stateRegister', alice, arguments=[nid, vpc.address, sid] + vpc_parties(web3) + change + [version] + ['\x01'] * 2, costs=costs)
    call_transaction(web3, chain, vpc, 'vpc', 'close', alice, arguments=vpc_parties(web3) + [sid, version] + change + ['\x01'] * 2, costs=costs)
    t = datetime.now()
    t = move_time(web3, t, timedelta(minutes=120))
    call_transaction(web3, chain, msc, 'msc', 'finalizeRegister', alice, arguments=[nid], costs=costs)
    call_transaction(web3, chain, msc, 'msc', 'execute', alice, arguments=[nid], costs=costs)
    for party in [alice, bob]:
        call_transaction(web3, chain, msc, 'msc', 'close', party, arguments=[], costs=costs)
    check_balance(web3, [(p, balance[p]) for p in [alice]])
    print_costs(costs, 'MSC Finalize register')

def test_MSContract_stateRegister_diffrent_versions(web3, chain, parties, msc, vpc, balance, costs):
    pass  # TODO
