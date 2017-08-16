pragma solidity ^0.4.0;

interface INanocontract {
    function finalize(address[] participants, uint sid) returns (bool, uint, uint);
}
