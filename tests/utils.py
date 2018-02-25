from datetime import timedelta, datetime
import pytest

mscId = 0
nid = 0
sid = 42
version = 15

alice = 1
bob = 2
ingrid = 3
eve = 0
party_name = {alice: 'alice', bob: 'bob', ingrid: 'ingrid', eve: 'eve'}
cash = {alice: 23 * 10**9, bob: 11 * 10**9}
cash2 = {alice: cash[bob], bob: cash[alice]}

@pytest.fixture()
def setup(web3, parties):
    t = datetime.now()
    web3.testing.timeTravel(int(t.timestamp()))

@pytest.fixture()
def parties(web3):
    return web3.eth.accounts

@pytest.fixture()
def pc_parties(web3):
    return [web3.eth.accounts[ix] for ix in [alice, bob]]

@pytest.fixture()
def vpc_parties(web3):
    return [web3.eth.accounts[ix] for ix in [alice, ingrid, bob]]

def move_time(web3, t, delta):
    small_delta = timedelta(seconds=20)
    t += delta - small_delta
    web3.testing.timeTravel(int(t.timestamp()))
    t += small_delta
    web3.testing.timeTravel(int(t.timestamp()))
    return t

def call_transaction(web3, chain, contract, contractName, function, sender, arguments, costs, value=0, wait=True):
    party = parties(web3)
    command = 'contract.{type}({{"from":parties(web3)[sender], "value":{value}}}).{function}(*arguments)'
    result = eval(command.format(type='call', value=value, function=function))
    txn_hash = eval(command.format(type='transact', value=value, function=function))
    if wait:
        txn = chain.wait.for_receipt(txn_hash)
        costs[sender] += txn.gasUsed
        print(party_name[sender] +':', contractName + '.' + function, 'cost:', txn.gasUsed)
        return result, txn
    else:
        return result, txn_hash

def print_costs(costs, scenarios=''):
    print('Total costs in ' + scenarios, end=': ')
    for party in party_name:
        if costs[party] > 0:
            print(party_name[party] + ':', costs[party], end=', ')
    print('sum: ', sum(costs.values()))
