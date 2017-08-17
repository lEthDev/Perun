pragma solidity ^0.4.0;

interface INanocontract {
    // if there is no intermediary ingrid her address should be set to 0x00
    function finalize(address alice, address ingrid, address bob, uint sid) returns (bool, uint, uint);
}
