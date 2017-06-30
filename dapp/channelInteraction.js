/**
 * Created by Lisa on 19.06.2017.
 */



$('#confirm-fund').click(function (){
    $('#fund-details').addClass("disabledpannel");
    $('#fund-button').addClass('disabled');
    var channelContract = basicChannels[currentBCIndex].contract;
    var amount = web3.toWei($('#fund-value').val());
    var sender = basicChannels[currentBCIndex].owner;
    var gasEstimate = 120000;
    channelContract.confirm({from: sender, gas: gasEstimate, value: amount});
});

$('#fund-button').click(function (){
    channel = basicChannels[currentBCIndex];
    var timeleft = channel.timeout - (Date.now()/1000);
    $('#timeout').html(Math.floor(timeleft/60));
    if (timeleft < 0 && channel.contract.status.call().c[0] == 0){
        $('#timeout').html('<button type="button" class="btn btn-default" onclick="refund()">Refund Deposit</button>');
    }
});


/////////////////////////////   Refund and Terminate Channel ///////////////////////////////////

refund = function (){
    var channelContract = basicChannels[currentBCIndex].contract;
    var sender = basicChannels[currentBCIndex].owner;
    var gasEstimate = 1200000;
    channelContract.refund({from: sender, gas: gasEstimate}, function (err, result){
        console.log(result, err);
    });
};


terminateChannel = function (){
    var channelContract = basicChannels[currentBCIndex].contract;
    var sender = basicChannels[currentBCIndex].owner;
    var gasEstimate = 1200000;
    channelContract.close({from: sender, gas: gasEstimate}, function (err, result){
        console.log(result, err);
    });
};

/////////////////////////////   Update Channel ///////////////////////////////////


$('#update-button').click(function () {
    $('.nanopayment').hide();
    $("#update-channel")[0].onclick = null;
    $('#update-channel').on("click", sendFunds);
});

$('#add-nanocontract-button').click(function () {
    $('.nanopayment').show();
    $("#update-channel")[0].onclick = null;
    $('#update-channel').on("click", addNanopayments);
});


updateResponse = function (){

};

updateChannelRequest = function (nanoAddress, sid, blockedA, blockedB){
    var channel = basicChannels[currentBCIndex];
    var signA, signB, xA, xB;
    if (channel.leftIsOwner) {
        xA = $('#send-funds').val();
        xB = $('#receive-funds').val();
    }
    else if (!channel.leftIsOwner) {
        xB = $('#send-funds').val();
        xA = $('#receive-funds').val();
    }
    var version = channel.version[0]+1;
    var sha = web3.sha3(nanoAddress, sid, blockedA, blockedB, version);
    var sig = web3.eth.sign(channel.owner, sha);
    if (channel.leftIsOwner) signA = sig;
    else signB = sig;
    $('#your-signature').text(sig);
    channel.updateRequest = {xA: xA, xB: xB, nanoAddress: nanoAddress, sid: sid, blockedA: blockedA, blockedB: blockedB, signA: signA, signB: signB};
    $('#update-details').collapse("show");
};

sendFunds = function (){
    updateChannelRequest('', '', 0, 0);
};

addNanopayments = function (){
    var blockedA, blockedB;
    if (basicChannels[currentBCIndex].leftIsOwner) {
        blockedA = $('#block-money-you').val();
        blockedB = $('#block-money-other').val();
    }
    else {
        blockedB = $('#block-money-you').val();
        blockedA = $('#block-money-other').val();
    }

    updateChannelRequest($('.add-nanopayment').val(), $('.add-sid').val(), blockedA, blockedB);
};


executeUpdate = function (nanoAddress, sid,  blockedA, blockedB, version, sigA, sigB){
    var channelContract = basicChannels[currentBCIndex].contract;
    var sender = basicChannels[currentBCIndex].owner;
    var gasEstimate = 1200000;
    channelContract.stateRegister(nanoAddress, sid,  blockedA, blockedB, version, sigA, sigB,{from: sender, gas: gasEstimate}, function (err, result){
        console.log(result, err);
    });
};
