pragma solidity ^0.4.8;

import "./ILibSignatures.sol";
import "./INanocontract.sol";

contract MSContract {
    event EventInitializing(address addressAlice, address addressBob);
    event EventInitialized(uint cashAlice, uint cashBob);
    event EventRefunded();
    event EventStateRegistering(uint nid);
    event EventStateRegistered(uint blockedAlice, uint blockedBob);
    event EventClosing();
    event EventClosed();
    event EventNotClosed();

    modifier AliceOrBob {require(msg.sender == alice.id || msg.sender == bob.id); _;}

    //Data type for Internal Contract
    struct Party {
        address id;
        uint cash;
        bool waitForInput;
    }

    enum NanoStatus {Empty, WaitingForAlice, WaitingForBob, Active, Finished}

    //Data type for Internal Contract
    struct InternalContract {
        NanoStatus status;
        INanocontract addr;
        uint sid;
        address[] participants;
        uint blockedA;
        uint blockedB;
        uint version;
        uint timeout;
    }

    // State options
    enum ChannelStatus {Init, Open, WaitingToClose}

    // MSContract variables
    Party public alice;
    Party public bob;
    uint id;
    uint public timeout;
    mapping (uint => InternalContract) public nano;
    uint public maxNid;
    ChannelStatus public status;
    ILibSignatures libSignatures;


    /*
    * Constructor for setting initial variables takes as input
    * addresses of the parties of the basic channel
    */
    function MSContract(address addressAlice, address addressBob, uint mscId, ILibSignatures libSignaturesAddress) {
        // set addresses
        alice.id = addressAlice;
        bob.id = addressBob;
        id = mscId;
        libSignatures = ILibSignatures(libSignaturesAddress);

        // set limit until which Alice and Bob need to respond
        timeout = now + 100 minutes;
        alice.waitForInput = true;
        bob.waitForInput = true;

        // set other initial values
        status = ChannelStatus.Init;
        EventInitializing(addressAlice, addressBob);
    }

    /*
    * This functionality is used to send funds to the contract during 100 minutes after channel creation
    */
    function confirm() AliceOrBob payable {
        require(status == ChannelStatus.Init);

        // Response (in time) from Player A
        if (alice.waitForInput && msg.sender == alice.id) {
            alice.cash = msg.value;
            alice.waitForInput = false;
        }

        // Response (in time) from Player B
        if (bob.waitForInput && msg.sender == bob.id) {
            bob.cash = msg.value;
            bob.waitForInput = false;
        }

        // execute if both players responded
        if (!alice.waitForInput && !bob.waitForInput) {
            status = ChannelStatus.Open;
            timeout = 0;
            EventInitialized(alice.cash, bob.cash);
        }
    }

    /*
    * This function is used in case one of the players did not confirm the MSContract in time
    */
    function refund() AliceOrBob {
        require(status == ChannelStatus.Init);

        if (now > timeout) {
            // refund money
            if (alice.waitForInput && alice.cash > 0) {
                require(alice.id.send(alice.cash));
            }
            if (bob.waitForInput && bob.cash > 0) {
                require(bob.id.send(bob.cash));
            }
            EventRefunded();

            // terminate contract
            selfdestruct(alice.id);
            return;
        }
    }

    /*
    * This functionality is called whenever the channel state needs to be established
    * it is called by both, alice and bob
    * Afterwards the parties have to interact directly with the nanocontract
    * and at the end they should call the execute function
    * @param     nanocontract index: nid
                 contract address: nanoAddr, sid,
                 blocked funds from A and B: blockedA and blockedB,
                 version parameter (should be greater than 0): version,
    *            signature parameter (from A and B): sigA, sigB
    */
    function stateRegister(uint nid, address nanoAddr, uint sid, address nanoAlice, address nanoIngrid, address nanoBob,
                           uint blockedA, uint blockedB, uint version, bytes sigA, bytes sigB) AliceOrBob {
        // verfify correctness of the signatures
        bytes32 msgHash = sha3(id, nid, nanoAddr, sid, nanoAlice, nanoIngrid, nanoBob, blockedA, blockedB, version);
        if (!libSignatures.verify(alice.id, msgHash, sigA)) return;
        if (!libSignatures.verify(bob.id, msgHash, sigB)) return;

        // get the nanocontract corresponding to nid
        var currNano = nano[nid];
        if (currNano.status == NanoStatus.Active || currNano.status == NanoStatus.Finished) return;

        // check if the parties have enough funds in the contract
        require((nanoAddr != address(0x00) && blockedA >= 0 && blockedB >= 0) || (nanoAddr == address(0x00) && blockedA + blockedB == 0));
        if (alice.cash + currNano.blockedA < blockedA || bob.cash + currNano.blockedB < blockedB) return;

        // execute on first call
        if (currNano.status == NanoStatus.Empty) {
            if (msg.sender == alice.id) currNano.status = NanoStatus.WaitingForBob;
            if (msg.sender == bob.id) currNano.status = NanoStatus.WaitingForAlice;
            currNano.timeout = now + 100 minutes;
            if (nid > maxNid)
                maxNid = nid;
            EventStateRegistering(nid);
        }

        // set values of InternalContract
        if (version > currNano.version) {
            currNano.addr = INanocontract(nanoAddr);
            currNano.sid = sid;
            currNano.participants = [nanoAlice, nanoIngrid, nanoBob];
            alice.cash += currNano.blockedA - blockedA;
            bob.cash += currNano.blockedB - blockedB;
            currNano.blockedA = blockedA;
            currNano.blockedB = blockedB;
            currNano.version = version;
        }

        // execute if both players responded
        if ((msg.sender == alice.id && currNano.status == NanoStatus.WaitingForAlice) ||
            (msg.sender == bob.id && currNano.status == NanoStatus.WaitingForBob)) {
                if (currNano.addr == address(0x00))
                    currNano.status == NanoStatus.Finished;
                else
                    currNano.status = NanoStatus.Active;
                currNano.timeout = 0;
                EventStateRegistered(currNano.blockedA, currNano.blockedB);
        }
    }

    /*
    * This function is used in case one of the players did not confirm the state
    */
    function finalizeRegister(uint nid) AliceOrBob {
        var currNano = nano[nid];
        if (currNano.status != NanoStatus.WaitingForAlice && currNano.status != NanoStatus.WaitingForBob) return;

        // execute if timeout passed
        if (now > currNano.timeout) {
            if (currNano.addr == address(0x00))
                currNano.status == NanoStatus.Finished;
            else
                currNano.status = NanoStatus.Active;
            currNano.timeout = 0;
            EventStateRegistered(currNano.blockedA, currNano.blockedB);
        }
    }

    /*
    * This functionality executes the internal Nanocontract Machine when its state is settled
    * The function takes as input addresses of the parties of the virtual channel
    */
    function execute(uint nid) AliceOrBob {
        var currNano = nano[nid];
        if (currNano.status != NanoStatus.Active) return;

        // call virtual payment machine on the params
        var (s, a, b) = currNano.addr.finalize(currNano.participants[0], currNano.participants[1], currNano.participants[2], currNano.sid);

        // check if the result makes sense
        if (!s) return;
        if (a + b != currNano.blockedA + currNano.blockedB) {
            a = currNano.blockedA;
            b = currNano.blockedB;
        }

        // finalize nanocontract
        alice.cash += a;
        bob.cash += b;
        currNano.status = NanoStatus.Finished;
    }

    /*
    * This functionality closes the channel when there is no internal machine
    */
    function close() AliceOrBob {
        if (status == ChannelStatus.Open) {
            status = ChannelStatus.WaitingToClose;
            timeout = now + 300 minutes;
            alice.waitForInput = true;
            bob.waitForInput = true;
            EventClosing();
        }

        if (status != ChannelStatus.WaitingToClose) return;

        // Response (in time) from Player A
        if (alice.waitForInput && msg.sender == alice.id)
            alice.waitForInput = false;

        // Response (in time) from Player B
        if (bob.waitForInput && msg.sender == bob.id)
            bob.waitForInput = false;

        if (!alice.waitForInput && !bob.waitForInput) {
            terminateChannel();
        }
    }

    function finalizeClose() AliceOrBob {
        if (status != ChannelStatus.WaitingToClose) {
            EventNotClosed();
            return;
        }

        // execute if timeout passed
        if (now > timeout) {
            terminateChannel();
        }
    }

    function terminateChannel() private {
        // force close all nanocontracts
        for (uint nid = 0; nid <= maxNid; nid++) {
            var currNano = nano[nid];
            if (currNano.status != NanoStatus.Empty && currNano.status != NanoStatus.Finished) {
                var (s, a, b) = currNano.addr.finalize(currNano.participants[0], currNano.participants[1], currNano.participants[2], currNano.sid);

                // if the result doesn't make sense, use default values
                if (!s || a + b != currNano.blockedA + currNano.blockedB) {
                    a = currNano.blockedA;
                    b = currNano.blockedB;
                }

                // finalize nanocontract
                alice.cash += a;
                bob.cash += b;
                currNano.status = NanoStatus.Finished;
            }
        }

        // send funds to A and B
        if (alice.id.send(alice.cash)) alice.cash = 0;
        if (bob.id.send(bob.cash)) bob.cash = 0;

        // terminate channel
        if (alice.cash == 0 && bob.cash == 0) {
            selfdestruct(alice.id);
            EventClosed();
        }
    }
}

