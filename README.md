## Perun Implementation

In this Git you will find a proof of concept implementation of the Perun Channels. The goal of this project is to build a decentralized trustless state channel network, which runs offline, fast and cheap based on top of the Ethereum Blockchain.

We are currently working on release 0.2 but we do not recomend to use this software to send real Ether, since this is still ongoing development.

## Release 0.1 (Basic Channel Support)
This realease includes 3 solidity contracts: 

#### Basic Channel Contract (MSContract.sol)
This is the contract to set up a basic state channel in which two parties agree (offline) on a intenal contract (e.g., a virtual payment machine VPM) and execute this contract offline. 

#### Virutal Payment Machine (VPM.sol)
The virtual payment machine is a contract which distributes funds between two users depending on statements, which are signed by them. This contract can be run in the basic channel since the VPM can be executed even without the interaction of both users. It is sufficient to have a signed message from them. This allows execution even if one party aborts.  

#### Signature Library (LibnatureLib.sol)
This library allows efficient verification of ecdsa signatures. Both MSContract and VPM both use this library internally. 

## Release 0.2 (DAPP supporting Basic Channels)

This release will include a user interface for PERUN channels:
* You can open channel with other parties on any network you like (private, test or main)
* Send money through the channels
* Support sample nanocontract

Further versions of this release might include:

* Support of wider range of nanocontracts
* Support multiple nanocontracts
* Support higher level state channels (Channel Network Infratructure)

## Release 0.3 (Payment Hub Support)
This release will allow any to conntect to a Payment Hubs (using basic channels) then route payments to any other connection through this Hub.

* Implement server side Payment Hub
* Deploy automatic Payment Hub in testnetwork
* Security Analysis and Proof

Further versions of this release might include:

* Support of wider range of nanocontracts
* Development of client side (standalone) payment wallet


## Usage

To test the User Interface you need to run the DAPP with the Metamask Wallet:
See here for more information: https://metamask.io/

To test solidity contracts using unit tests first install populus library http://populus.readthedocs.io/en/latest/ and then run 'pytest tests'
