/**
 * Created by Lisa on 06.06.2017.
 */

// set providor
if (typeof web3 !== 'undefined') {
    console.info('Web3 already initialized, re-using provider.');
    web3 = new Web3(web3.currentProvider);
} else {
    console.info('Web3 not yet initialized, doing so now with HttpProvider.');
    web3 = new Web3(new Web3.providers.HttpProvider('http://localhost:8545'));
}

var basicChannels = [];


msgAlert =function (string, errorlevel){
    var status = $('#status');
    var msg = '<a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>';
    status.removeClass('alert-info', 'alert-success', 'alert-warning', 'alert-danger');
    if (errorlevel == 0){
        status.addClass('alert-info');
        msg.append('<strong>Info!</strong>');
    }
    if (errorlevel == 1){
        status.addClass('alert-success');
        msg.append('<strong>Success!</strong>');
    }
    if (errorlevel == 2){
        status.addClass('alert-warning');
        msg.append('<strong>Warning!</strong>');
    }
    if (errorlevel == 3){
        status.addClass('alert-danger');
        msg.append('<strong>Danger!</strong>');
    }
    status.html(msg+'string');
};