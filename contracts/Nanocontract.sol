pragma solidity ^0.4.8;

import "./ILibSignatures.sol";
import "./INanocontract.sol";

contract Nanocontract is INanocontract {
    // TODO: Events
    enum Status {Empty, ConflictExec, ConflictFinal, Executing, Finished}

    // datatype for virtual state
    struct State {
        Status status;
        uint aliceCash;
        uint bobCash;
        uint version;
        uint validity;
        uint extendedValidity;
        bool waitingForAlice;
        bool waitingForBob;
    }

    // datatype for virtual state
    mapping (bytes32 => State) public states;
    ILibSignatures libSignatures;
    bytes32 public id;
    bytes32 public msgHash;
    function init(ILibSignatures libSignaturesAddress) {
        libSignatures = ILibSignatures(libSignaturesAddress);
    }

    /*
        TODO
    */
    function updateState(address alice, address ingrid, address bob, uint sid, 
                         uint version, uint aliceCash, uint bobCash, bytes32 data, bool isFinal,
                         bytes sigA, bytes sigB) internal returns (bytes32, bool) {
        require(msg.sender == alice || msg.sender == ingrid || msg.sender == bob);
        id = sha3(alice, ingrid, bob, sid);
        var accepted = false;

        // verfiy signatures
        if (states[id].status == Status.Executing || states[id].status == Status.Finished) return (id, accepted);
        if (isFinal)
           msgHash = sha3(id, version, aliceCash, bobCash);
       else
           msgHash = sha3(id, version, aliceCash, bobCash, data);
        if (!libSignatures.verify(alice, msgHash, sigA)) return (id, accepted);
        if (!libSignatures.verify(bob, msgHash, sigB)) return (id, accepted);

        // if such a virtual channel state does not exist yet, create one
        if (states[id].status == Status.Empty) {
            states[id].validity = now + 10 minutes;
            states[id].extendedValidity = states[id].validity + 10 minutes;
            states[id].waitingForAlice = true;
            states[id].waitingForBob = true;
            if (isFinal)
                states[id].status = Status.ConflictFinal;
            else
                states[id].status = Status.ConflictExec;
        }
        else {
            // if channel is closed or timeouted do nothing
            if (states[id].extendedValidity < now) return (id, accepted);
            if ((states[id].validity < now) && (msg.sender == alice || msg.sender == bob)) return (id, accepted);
        }
 
        // check if the message is from alice or bob
        if (msg.sender == alice) {
            states[id].waitingForAlice = false;
        }
        if (msg.sender == bob) {
            states[id].waitingForBob = false;
        }

        // set values of Internal State
        if (version > states[id].version) {
            states[id].aliceCash = aliceCash;
            states[id].bobCash = bobCash;
            states[id].version = version;
            accepted = true;
        }

        // execute if both players responded
        if (!states[id].waitingForAlice && !states[id].waitingForBob) {
            if (states[id].status == Status.ConflictFinal)
                states[id].status = Status.Finished;
            else
                states[id].status = Status.Executing;
        }
        return (id, accepted);
    }

    /*
        TODO
    */
    function finalize(address alice, address ingrid, address bob, uint sid) returns (bool, uint, uint) {
        var id = sha3(alice, ingrid, bob, sid);
        var st = states[id];
        if (st.status == Status.Finished)
            return (true, st.aliceCash, st.bobCash);
        else if (st.status == Status.ConflictFinal && st.extendedValidity < now) {
            st.status = Status.Finished;
            return (true, st.aliceCash, st.bobCash);
        }
        else
            return (false, 0, 0);
    }
}
