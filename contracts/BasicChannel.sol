pragma solidity ^0.4.8;

import "./ILibSignatures.sol";

contract BasicChannel {
    uint constant confirmTime = 100 minutes;
    uint constant closingTime = 100 minutes;
    string constant alreadyClosed = " already closed";

    event EventBasicChannelOpening(uint id);
    event EventBasicChannelOpened();
    event EventBasicChannelNotOpened();
    event EventBasicChannelClosing();
    event EventBasicChannelClosed();
    
    event EventVirtualChannelClosingInit(uint vid);
    event EventVirtualChannelClosing(uint vid);
    event EventVirtualChannelClose(uint vid, uint cash1, uint cash2, uint ver, bytes sig, bytes sigB);
    event EventVirtualChannelCloseFinal(uint vid, uint cash1A, uint cash2A, uint versionA, bytes sigA, bytes sigAB,
                                                uint cash1B, uint cash2B, uint versionB, bytes sigB, bytes sigBA);

    modifier AliceOrBob {require(msg.sender == alice.id || msg.sender == bob.id); _;}

    // Data type for BasicContract.
    struct Party {
        address id;
        int totalTransfers;
        uint cash;
    }

    // State options.
    enum BasicChannelStatus {Init, Open, ClosingByAlice, ClosingByBob}

    enum VirtualStatus {Empty, Closing, WaitingToClose, ClosingFinal, Timeouted, Closed}

    // Data type for Internal Contract.
    struct VirtualContract {
        address p1;
        uint cash1;
        uint subchan1;
        address Ingrid;
        address p2;
        uint cash2;
        uint subchan2;
        uint validity;
        VirtualStatus status;
        uint cashFinal1;
        uint cashFinal2;
        uint timeout;
    }

    // MSContract variables
    Party public alice;
    Party public bob;
    uint id;
    uint public timeout;
    
    uint lastVersion;
    uint lastCash1;
    uint lastCash2;
    
    mapping (uint => VirtualContract) public virtual;
    BasicChannelStatus public status;
    ILibSignatures libSignatures;


    /*
    * Constructor for setting initial variables takes as input address of the other party of the basic channel.
    * Additionally Alice sends her money in it.
    */
    function BasicChannel(address addressBob, uint bcId, ILibSignatures libSignaturesAddress) public payable {
        // set addresses
        alice.id = msg.sender;
        alice.cash = msg.value;
        bob.id = addressBob;
        id = bcId;
        libSignatures = ILibSignatures(libSignaturesAddress);

        // set limit until which Bob needs to respond
        timeout = now + confirmTime;

        // set other initial values
        status = BasicChannelStatus.Init;
        EventBasicChannelOpening(id);
    }

    /*
    * This functionality is used by Bob to send funds to the contract after channel creation.
    */
    function BasicChannelOpen() public payable {
        require(msg.sender == bob.id && status == BasicChannelStatus.Init);

        bob.cash = msg.value;
        status = BasicChannelStatus.Open;
        timeout = 0;
        EventBasicChannelOpened();
    }

    /*
    * This function is used in case Bob did not confirm the BasicChannel in time.
    */
    function BasicChannelOpenTimeout() public {
        require(msg.sender == alice.id && status == BasicChannelStatus.Init && now > timeout);
        EventBasicChannelNotOpened();
        selfdestruct(alice.id);
    }
    
    function CheckSignature(address verifier, uint vid, address p1, uint cash1, uint subchan1, address Ingrid,
                                    address p2, uint cash2, uint subchan2, uint validity, uint version, bytes sig) private view returns (bool) {
        bytes32 msgHash = keccak256(vid, p1, cash1, subchan1, Ingrid, p2, cash2, subchan2, validity, version);
        return libSignatures.verify(verifier, msgHash, sig);                                
    }
    
    function CheckVersion(address verifierA, address verifierB, uint vid, VirtualContract memory vc, uint version, bytes sigA, bytes sigB) private view returns (bool) {
        if (!CheckSignature(verifierA, vid, vc.p1, vc.cash1, vc.subchan1, vc.Ingrid, vc.p2, vc.cash2, vc.subchan2, vc.validity, version, sigA))
            return false;
        bytes32 msgHash = keccak256(vid, vc.p1, vc.cash1, vc.subchan1, vc.Ingrid, vc.p2, vc.cash2, vc.subchan2, vc.validity, version, sigA);
        return libSignatures.verify(verifierB, msgHash, sigB); 
    }

    function Other(address p, address p1, address p2) private pure returns (address) {
        if (p == p1) return p2;
        else return p1;
    }

    function VirtualChannelCloseInit(uint vid, address p1, uint cash1, uint subchan1, address Ingrid,
                                               address p2, uint cash2, uint subchan2, uint validity, bytes sig) AliceOrBob public {
        require(now > validity && Ingrid == msg.sender && virtual[vid].status == VirtualStatus.Empty);
        require(id == subchan1 || id == subchan2);
        require(CheckSignature(Other(msg.sender, alice.id, bob.id), vid, p1, cash1, subchan1, Ingrid, p2, cash2, subchan2, validity, 0, sig));
        
        virtual[vid] = VirtualContract(p1, cash1, subchan1, Ingrid, p2, cash2, subchan2, validity, VirtualStatus.Closing, 0, 0, now + closingTime);
        EventVirtualChannelClosingInit(vid);
    }
    
    function VirtualChannelAlreadyClosed(uint vid, bytes sig) AliceOrBob public {
        require((msg.sender != virtual[vid].Ingrid && (virtual[vid].status == VirtualStatus.Closing || virtual[vid].status == VirtualStatus.ClosingFinal)) ||
            (msg.sender == virtual[vid].Ingrid && virtual[vid].status == VirtualStatus.Timeouted));
        bytes32 msgHash = keccak256(vid, alreadyClosed);
        require(libSignatures.verify(Other(msg.sender, alice.id, bob.id), msgHash, sig));
        EventBasicChannelClosed();
        selfdestruct(msg.sender);
    }
    
    function VirtualChannelClose(uint vid, uint cash1, uint cash2, uint version, bytes sig, bytes sigB) AliceOrBob public {
        VirtualContract memory vc = virtual[vid];
        require(vc.status == VirtualStatus.Closing);
        require(msg.sender != vc.Ingrid);
        vc.cash1 = cash1;
        vc.cash2 = cash2;
        require(CheckVersion(Other(msg.sender, vc.p1, vc.p2), msg.sender, vid, vc, version, sig, sigB));
        EventVirtualChannelClose(vid, cash1, cash2, version, sig, sigB);
        virtual[vid].status = VirtualStatus.WaitingToClose;
    }
    
    function VirtualChannelCloseInitTimeout(uint vid) AliceOrBob public {
        require(virtual[vid].status == VirtualStatus.Closing && msg.sender == virtual[vid].Ingrid);
        require(now > virtual[vid].timeout);
        EventBasicChannelClosed();
        selfdestruct(msg.sender);
    }
    
    // Ingrid needs to call VirtualChannelCloseInit before she can call VirtualChannelCloseFinal.
    function VirtualChannelCloseFinal(uint vid, uint cash1A, uint cash2A, uint versionA, bytes sigA, bytes sigAB,
                                                uint cash1B, uint cash2B, uint versionB, bytes sigB, bytes sigBA) AliceOrBob public {
        VirtualContract memory vc = virtual[vid];
        require(msg.sender == vc.Ingrid && (vc.status == VirtualStatus.WaitingToClose || vc.status == VirtualStatus.Closing));
        
        require(CheckVersion(vc.p1, vc.p2, vid, vc, versionA, sigA, sigAB));
        require(CheckVersion(vc.p2, vc.p1, vid, vc, versionB, sigB, sigBA));
        if (versionA >= versionB) {
            vc.cashFinal1 = cash1A;
            vc.cashFinal2 = cash2A;
        }
        else {
            vc.cashFinal1 = cash1B;
            vc.cashFinal2 = cash2B;
        }
        vc.status = VirtualStatus.ClosingFinal;
        vc.timeout = now + closingTime;
        virtual[vid] = vc;
        EventVirtualChannelCloseFinal(vid, cash1A, cash2A, versionA, sigA, sigAB, cash1B, cash2B, versionB, sigB, sigBA);
    }
    
    function VirtualChannelCloseFinalTimeout(uint vid) AliceOrBob public {
        VirtualContract memory vc = virtual[vid];
        require(vc.status == VirtualStatus.ClosingFinal && msg.sender == vc.Ingrid);
        require(now > vc.timeout);
        
        alice.totalTransfers += int(vc.cashFinal1) - int(vc.cash1);
        bob.totalTransfers += int(vc.cashFinal2) - int(vc.cash2);
        
        virtual[vid].status = VirtualStatus.Closed;
        EventBasicChannelClosed();
    }
    
    function VirtualChannelCloseTimeout(uint vid, address p1, uint cash1, uint subchan1, address Ingrid,
                                                  address p2, uint cash2, uint subchan2, uint validity, bytes sig) AliceOrBob public {
        require(virtual[vid].status != VirtualStatus.Closed && msg.sender != Ingrid);
        require((Ingrid == alice.id || Ingrid == bob.id) && (msg.sender == p1 || msg.sender == p2));
        require(id == subchan1 || id == subchan2);
        require(CheckSignature(Ingrid, vid, p1, cash1, subchan1, Ingrid, p2, cash2, subchan2, validity, 0, sig));
        require(now > validity + 2 * closingTime);
        virtual[vid].status = VirtualStatus.Timeouted;
        virtual[vid].Ingrid = Ingrid;
        virtual[vid].timeout = now + closingTime;
        EventVirtualChannelClosing(vid);
    }
    
    function VirtualChannelCloseTimeoutTimeout(uint vid) AliceOrBob public {
        VirtualContract memory vc = virtual[vid];
        require(vc.status == VirtualStatus.Timeouted && msg.sender != vc.Ingrid);
        require(now > vc.timeout);
        EventBasicChannelClosed();
        selfdestruct(msg.sender);
    }
    
    function BasicChannelClose(uint32 cash1, uint cash2, uint version, bytes sig) AliceOrBob public {
        require(status == BasicChannelStatus.Open || (status == BasicChannelStatus.ClosingByAlice && msg.sender == bob.id) ||
                                                     (status == BasicChannelStatus.ClosingByBob && msg.sender == alice.id));
        bytes32 msgHash = keccak256(id, alice.id, cash1, bob.id, cash2, version);
        require(libSignatures.verify(Other(msg.sender, alice.id, bob.id), msgHash, sig));
        if (status == BasicChannelStatus.Open) {
            lastVersion = version;
            lastCash1 = cash1;
            lastCash2 = cash2;
            timeout = now + 3*closingTime;
            EventBasicChannelClosing();
        }
        else {
            if (version > lastVersion) {
                lastCash1 = cash1;
                lastCash2 = cash2;
            }
            require(alice.id.send(uint(int(lastCash1) + alice.totalTransfers)));
            require(bob.id.send(uint(int(lastCash2) + bob.totalTransfers)));
            EventBasicChannelClosed();
            selfdestruct(msg.sender);
        }
    }
    
    function ActiveVirtualChannel(uint vid, address p1, uint cash1, uint subchan1, address Ingrid,
                                            address p2, uint cash2, uint subchan2, uint validity, bytes sig) AliceOrBob public {
        require((status == BasicChannelStatus.ClosingByAlice && msg.sender == bob.id) ||
                (status == BasicChannelStatus.ClosingByBob && msg.sender == alice.id));
        require(CheckSignature(Other(msg.sender, alice.id, bob.id), vid, p1, cash1, subchan1, Ingrid, p2, cash2, subchan2, validity, 0, sig));
        require(now < validity + closingTime);
        EventBasicChannelClosed();
        selfdestruct(msg.sender);
    }
    
    function BasicChannelCloseTimeout() AliceOrBob public {
        require((status == BasicChannelStatus.ClosingByAlice && msg.sender == alice.id) || 
                (status == BasicChannelStatus.ClosingByBob && msg.sender == bob.id));
        require(now > timeout);
        require(alice.id.send(uint(int(lastCash1) + alice.totalTransfers)));
        require(bob.id.send(uint(int(lastCash2) + bob.totalTransfers)));
        EventBasicChannelClosed();
        selfdestruct(msg.sender);
    }
}

