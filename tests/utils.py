from datetime import timedelta, datetime
import pytest

sid = 42
version = 15
cash = [23, 11]
cash2 = [11, 23]

alice = 0
bob = 1
ingrid = 2
eve = 3

@pytest.fixture()
def now(web3):
    t = datetime.now()
    web3.testing.timeTravel(int(t.timestamp()))
    return t

@pytest.fixture()
def parties(web3):
    return web3.eth.accounts

@pytest.fixture()
def vpc_parties(web3):
    return [web3.eth.accounts[ix] for ix in [alice, ingrid, bob]]

def set_sender(web3, party):
    web3.eth.defaultAccount = web3.eth.accounts[party]

def move_time(web3, t, delta):
    small_delta = timedelta(seconds=20)
    t += delta - small_delta
    web3.testing.timeTravel(int(t.timestamp()))
    t += small_delta
    web3.testing.timeTravel(int(t.timestamp()))
    return t

def call_transaction(web3, chain, contract, function, sender, arguments, wait):
    set_sender(web3, sender)
    party = parties(web3)
    command = 'contract.%s().' + function + '(*arguments)'
    result = eval(command % 'call')
    txn_hash = eval(command % 'transact')
    if wait:
        txn = chain.wait.for_receipt(txn_hash)
        return result, txn
    else:
        return result, txn_hash

