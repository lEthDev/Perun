pragma solidity ^0.4.0;

library LibSignaturesMock {
    function verify(address _address, bytes32 _message, bytes _signature) constant returns(bool) {
        return bytes(_signature)[0] != 0;
    }
}

