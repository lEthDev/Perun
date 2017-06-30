/**
 * Created by Lisa on 06.06.2017.
 */

var accounts = web3.eth.accounts;
var totalBalance = 0;
$.each(accounts, function (i,addr) {

    var balance = web3.fromWei(web3.eth.getBalance(addr).toString(),'ether')
    totalBalance += parseInt(balance);

});
totalBalance = (Math.round(totalBalance*100))/100;
$('#balance').html(totalBalance);


    var htmlContent = '';
    $("#channel-accounts").html('');
    $.each(accounts, function (i, addr) {

        var balance = web3.fromWei(web3.eth.getBalance(addr).toString(),'ether')
        balance = (Math.round(balance*10000))/10000;
        var account = '<li id='+addr+' ><a  data-toggle="tab" style="padding:10px;">';
        account += '<h4>Account '+i+'</h4>'+balance+' Ether';
        account += '<br>'+addr.slice(0,10)+'...</a></li>';
        $("#channel-accounts").append(account);
    });
    $('#'+accounts[0]).addClass("active");


