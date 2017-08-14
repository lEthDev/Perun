pragma solidity ^0.4.0;

interface INanocontract {
    function close(address[] participants, uint sid, uint version, uint aliceCash, uint bobCash,
                   bytes signA, bytes signB);

    function finalize(address[] participants, uint sid) returns (bool, uint, uint);
}
