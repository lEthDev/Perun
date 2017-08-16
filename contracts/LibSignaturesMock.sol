pragma solidity ^0.4.0;

library LibSignaturesMock {
    function verify(address addr, bytes32 message, bytes signature) constant returns(bool) {
        return bytes(signature)[0] != 0;
    }
}

