pragma solidity ^0.4.0;

interface ILibSignatures {
    function verify(address _address, bytes32 _message, bytes _signature) constant returns(bool);
}
