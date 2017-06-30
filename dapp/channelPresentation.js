/**
 * Created by Lisa on 15.06.2017.
 */
var currentBCIndex;


updateChannelsList = function () {
  updateChannelsListItem(currentBCIndex);
};

updateChannelsListItem = function (i) {
    var channel = basicChannels[i];
    var element = '#li_'+channel.address;
    var contract = channel.contract;
    var update = 0;
    var cashAlice = web3.fromWei(contract.alice.call()[1],"ether");
    if (channel.cashLeft.c[0] != cashAlice.c[0]) {
        console.log("update cash alice from " + channel.cashLeft + " to " + cashAlice);
        channel.cashLeft = cashAlice;
        update = 1;
    }
    var cashBob = web3.fromWei(contract.bob.call()[1],"ether");
    if (channel.cashRight.c[0] != cashBob.c[0]) {
        console.log("update cash bob from " + channel.cashRight + " to " + cashBob);
        channel.cashRight = cashBob;
        update = 1;
    }
    var blocked = web3.fromWei((contract.c.call()[3]+contract.c.call()[4]),"ether");
    if (channel.blocked != blocked) {
        console.log("update blocked cash from " + channel.blocked + " to " + blocked);
        channel.blocked = blocked;
        update = 1;
    }
    if (channel.version != contract.c.call()[5]) {
        console.log("update channel version from " + channel.version + " to " + contract.c.call()[5]);
        channel.version = contract.c.call()[5];
        update = 1;
    }
    if (channel.virtualSet != contract.c.call()[1]) {
        console.log("update virtual channel addr from " + channel.virtualSet + " to " + contract.c.call()[1]);
        channel.virtualSet = contract.c.call()[1];
        update = 1;
    }
    if (update != 0) {
        var badge = "";
        if (i != currentBCIndex) {
            if (channel.notification == "new") channel.notification = update;
            else {
                channel.notification += parseInt(update);
            }
            var badge = '<span class="badge" id="badge'+channel.address+'">'+channel.notification+'</span>';
        }
        var addr = channel.address;
        var sum = (0+ parseInt(channel.cashLeft) + parseInt(channel.cashRight));
        $(element).html('<strong>' + channel.channelName + '</strong> (with ' + sum + ' Ether)' + badge);

    }
};

channelSelect = function(i){

    currentBCIndex = i;
    var channel = basicChannels[i];
    var contract = channel.contract;
    var element = '#li_'+channel.address;
    updateChannelsListItem(i);
    if (channel.leftIsOwner && contract.alice.call()[2] && contract.status.call().c[0] == 0){
        $('#fund-details').removeClass("disabledpannel");
        $('#fund-button').removeClass('disabled');
    } else if (!channel.leftIsOwner && contract.bob.call()[2] && contract.status.call().c[0] == 0){
        $('#fund-details').removeClass("disabledpannel");
        $('#fund-button').removeClass('disabled');
    } else {
        $('#fund-details').addClass("disabledpannel");
        $('#fund-button').addClass('disabled');
    }
    $("#badge"+channel.address).hide();
    $('#chan-adr').text(channel.address);
    $('#chan-peer-1').text(channel.leftName);
    $('#chan-peer-1-fund').text(channel.cashLeft);
    $('#chan-peer-2').text(channel.rightName);
    $('#chan-peer-2-fund').text(channel.cashRight);
    $('#chan-blocked').text(channel.blocked);
    if (channel.contract.alice.call()[2] == 1) {
        $('#fund-button').disable;
        $('#update-button').enable;
    }
    else {
        $('#fund-button').enable;
        $('#update-button').disable;
    }
    $('#chan-interaction').show();
};

var timeoutfilter = web3.eth.filter('latest');




