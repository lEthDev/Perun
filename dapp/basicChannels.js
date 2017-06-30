/**
 * Created by Lisa on 06.06.2017.
 */

$('#new-basic-channel').click(function () {
    $('#basic-user-address-pannel').show();
    $('#basic-channel-address-pannel').hide();
    var button = $('#modal-button');
    button[0].onclick = null;
    button.on("click", newChannel);
    button.text('Create');});

$('#add-basic-channel').click(function () {
    $('#basic-user-address-pannel').hide();
    $('#basic-channel-address-pannel').show();
    var button = $('#modal-button');
    button[0].onclick = null;
    button.on("click", addChannel);
    button.text('Add');
});



//////////////////    Deploy      //////////////////////////////////

newChannel = function () {
    var account = $("ul#channel-accounts  li.active").attr('id');
    var address = $('#basic-user-address').val();
    var userName = $('#basic-user-name').val();
    var channelName = $('#basic-chan-name').val();
    var contract = deployContract(account, address, basicChannelAbi, basicChannelCode, account, "new Basic Channel");
    var loader = '<div id="loader" ><div class="loader"></div></div>';
    $('#channel-list').append(loader);
    var deploymentCheckRuns = 0;
    var deploymentCheck = setInterval(function() {
        deploymentCheckRuns++;
        if (deploymentCheckRuns > 1000) {
            clearInterval(deploymentCheck);
            console.log('The contract could not be deployed. Watch the network and try to add the deployed contract.')
        }
        if (typeof contract.address !== "undefined") {
            clearInterval(deploymentCheck);
            addChannelToList(account, contract, userName, channelName);
        }
    }, 1000);
};

addChannel = function () {
    var account = $("ul#channel-accounts  li.active").attr('id');
    var name = $('#basic-user-name').val();
    var channelName = $('#basic-chan-name').val();
    var channelAddress = $('#basic-channel-address').val();
    var contract = web3.eth.contract(basicChannelAbi).at(channelAddress);
    addChannelToList(account, contract, name, channelName);
};

addChannelToList = function (account, contract, userName, channelName) {
    var nameLeft, nameRight, ownLeft;
    var addrLeft = contract.alice.call()[0];
    var addrRight = contract.bob.call()[0];
    if (account == addrLeft){
        nameLeft = "You";
        nameRight = userName;
        ownLeft = true;
    } else if (account == addrRight){
        nameRight = "You";
        nameLeft = userName;
        ownLeft = false;
    } else {
        msgAlert("there has been a problem connecting to contract "+ contract.address);
        return;
    }
    basicContract = {
        owner: account,
        contract: contract,
        address: contract.address,
        leftName: nameLeft,
        addrLeft : addrLeft,
        cashLeft: web3.fromWei(contract.alice.call()[1],"ether"),
        rightName: nameRight,
        addrRight : addrRight,
        cashRight: web3.fromWei(contract.bob.call()[1],"ether"),
        blocked: 0,
        version: [contract.c.call()[0]],
        sigLeft: "0",
        sigRight: "0",
        virtualSet: [contract.c.call()[1]],
        channelName: channelName,
        notification: "new",
        timeout: contract.timeout.call().c[0],
        leftIsOwner : ownLeft,
        updateRequest: ''
    };
    basicChannels.push(basicContract);
    addContractWatcher(basicContract);
    var index = $.inArray(basicContract, basicChannels);
    var elementName = 'li_'+contract.address;
    var element = $('<button type="button" class="list-group-item">');
    element.attr("id",elementName);
    element.click(function(){
        $('#fund-details').collapse("hide");
        channelSelect(index);
    });
    var badge = '<span class="badge" id="badge'+basicContract.address+'">'+basicContract.notification+'</span>';
    element.html('<strong>' + basicContract.channelName + '</strong> (with ' + (parseInt(basicContract.cashLeft) + parseInt(basicContract.cashRight)) + ' Ether)' + badge);
    $('#channel-list').find('#loader').remove();
    $('#channel-list').append(element);
};



//////////////////    Presentation     //////////////////////////////////


