pragma solidity ^0.4.8;

import "./ILibSignatures.sol";
import "./INanocontract.sol";

contract PC is INanocontract {
    event EventVpcClosing(bytes32 indexed id);
    event EventVpcClosed(bytes32 indexed id, uint cashAlice, uint cashBob);

    // datatype for virtual state
    struct VpcState {
        uint AliceCash;
        uint BobCash;
        uint seqNo;
        uint validity;
        uint extendedValidity;
        bool open;
        bool waitingForAlice;
        bool waitingForBob;
        bool init;
    }

    // datatype for virtual state
    mapping (bytes32 => VpcState) public states;
    VpcState public s;
    bytes32 public id;
    ILibSignatures libSignatures;

    function PC(ILibSignatures libSignaturesAddress) {
        libSignatures = ILibSignatures(libSignaturesAddress);
    }

    /*
    * This function is called by any participant of the virtual channel
    * It is used to establish a final distribution of funds in the virtual channel
    */
    function close(address[] participants, uint sid, uint version, uint aliceCash, uint bobCash,
            bytes signA, bytes signB) {
        if (participants.length != 2) throw;
        if (msg.sender != participants[0] && msg.sender != participants[1]) throw;

        id = sha3(participants, sid);
        s = states[id];
        address alice = participants[0];
        address bob = participants[1];
        
        // verfiy signatures
        bytes32 msgHash = sha3(id, version, aliceCash, bobCash);
        if (!libSignatures.verify(alice, msgHash, signA)) return;
        if (!libSignatures.verify(bob, msgHash, signB)) return;

        // if such a virtual channel state does not exist yet, create one
        if (!s.init) {
            uint validity = now + 10 minutes;
            uint extendedValidity = validity + 10 minutes;
            s = VpcState(aliceCash, bobCash, version, validity, extendedValidity, true, true, true, true);
            EventVpcClosing(id);
        }

        // if channel is closed or timeouted do nothing
        if (!s.open || s.extendedValidity < now) return;
        if ((s.validity < now) && (msg.sender == alice || msg.sender == bob)) return;
 
        // check if the message is from alice or bob
        if (msg.sender == alice) s.waitingForAlice = false;
        if (msg.sender == bob) s.waitingForBob = false;

        // set values of Internal State
        if (version > s.seqNo) {
            s = VpcState(aliceCash, bobCash, version, s.validity, s.extendedValidity, true, s.waitingForAlice, s.waitingForBob, true);
        }

        // execute if both players responded
        if (!s.waitingForAlice && !s.waitingForBob) {
            s.open = false;
            EventVpcClosed(id, s.AliceCash, s.BobCash);
        }
        states[id] = s;
    }

    /*
    * For the virtual channel with id = (alice, ingrid, bob, sid) this function:
    *   returns (false, 0, 0) if such a channel does not exist or is neither closed nor timeouted, or
    *   return (true, a, b) otherwise, where (a, b) is a final distribution of funds in this channel
    */
    function finalize(address[] participants, uint sid) returns (bool, uint, uint) {
        id = sha3(participants, sid);
        if (states[id].init) {
            if (states[id].extendedValidity < now) {
                states[id].open = false;
                EventVpcClosed(id, states[id].AliceCash, states[id].BobCash);
            }
            if (states[id].open)
                return (false, 0, 0);
            else
                return (true, states[id].AliceCash, states[id].BobCash);
        }
        else
            return (false, 0, 0);
    }
}
