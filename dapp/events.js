/**
 * Created by Lisa on 27.06.2017.
 */
var log = $('#log');
var filterList;
addContractWatcher = function (channel) {
    var events = channel.contract.allEvents({fromBlock: 0, toBlock: 'latest'});


    // watch for changes
    events.watch(function(error, event){
        var events ='';
        if (!error){
            if(event.event == "EventInitializing"){
                var timeago = (Date.now()/1000) - web3.eth.getBlock(event.blockNumber).timestamp;
                $('#timeout').text(Math.floor(timeago/60));
                events = ("A request for opening channel "+channel.name+" has been made ("+Math.floor(timeago/60)+" minutes ago)<br>");
            }
            if(event.event == "EventInitialized"){
                var timeago = (Date.now()/1000) - web3.eth.getBlock(event.blockNumber).timestamp;
                $('#timeout').text(Math.floor(timeago/60));
                events = ("Channel "+channel.name+" was succesfully openened ("+Math.floor(timeago/60)+" minutes ago)<br>");
            }
            log.prepend(events);
        }
    });

    var contractFilter = web3.eth.filter({address: channel.address});
    // filterList.add({filter:contractFilter, id:contract.address});
    contractFilter.watch(function(error, result){
        // if (error != "null") console.error(error);
        web3.eth.getTransactionReceipt(result.hash, function (receipt) {
            console.log({TransactionReceipt: receipt});
        });
        $.each(basicChannels, function (i, channel) {
            updateChannelsListItem(i);
        });
    });

};
