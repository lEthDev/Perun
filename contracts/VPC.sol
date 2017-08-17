pragma solidity ^0.4.8;

import "./ILibSignatures.sol";
import "./Nanocontract.sol";

contract VPC is Nanocontract {
    function VPC(ILibSignatures libSignaturesAddress) {
        init(libSignaturesAddress);
    }

    function close(address alice, address ingrid, address bob, uint sid,
                   uint version, uint aliceCash, uint bobCash,
                   bytes sigA, bytes sigB) {
        updateState(alice, ingrid, bob, sid, version, aliceCash, bobCash, 0, true, sigA, sigB);
    }
}
