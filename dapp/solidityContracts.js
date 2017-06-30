/**
 * Created by Lisa on 07.06.2017.
 */

var libSignatureAddress = '';
//var libSignatureAddress = 'B871f3Cf039A6f604045A2D92006BbCfd2F2A45c';
 var libSignatureAddress = 'B94a471575269415b851AED039526c93A3b27974'; //geth --rpc --rpcdomain='*' --dev

var libSignatureCode, libSignatureAbi;
var basicChannelAbi, basicChannelCode, basicChannelCodeGasEstimate;
var virtualChannelAbi, virtualChannelCode;

$.getJSON("contracts/LibSignatures.json", function (json, error) {
    if (error != 'success'){
        console.log(error);
        return;
    }
    libSignatureAbi = json.abi;
    libSignatureCode = json.unlinked_binary;
    if (libSignatureAddress == ''){
        libSignatureAddress = deployContract('', '', libSignatureAbi, libSignatureCode, accounts[0], "Signature Library");
    };
});

$.getJSON("contracts/MSContract.json", function (json, error) {
    if (error!= 'success'){
        console.log(error);
        return;
    }
    basicChannelAbi = json.abi;
    basicChannelCode= json.unlinked_binary.replace("__LibSignatures_________________________", libSignatureAddress).replace("__LibSignatures_________________________", libSignatureAddress);
    //basicChannelCode= basicChannelCode.replace("0x", '');
});

$.getJSON("contracts/VPC.json", function (json, error) {
    if (error!= 'success'){
        console.log(error);
        return;
    }
    virtualChannelAbi = json.abi;
    virtualChannelCode = json.unlinked_binary.replace("__LibSignatures_________________________", libSignatureAddress);
});


deployContract = function (param1, param2, abi, code, sender, name) {
    var contractObject = web3.eth.contract(abi);
    var contractData = contractObject.new.getData(param1, param2, {data: code});
    var gasEstimate = web3.eth.estimateGas({data: contractData});
    var contractInstance = web3.eth.contract(abi).new(param1, param2, {data: code, from: sender, gas: gasEstimate}, function(error, result){
        if (error){
            console.log(error);
            return;
        }
        // If we have an address property, the contract was deployed
        if (result.address) {
            console.log("The "+name+" contract was deployed at "+result.address);
        }
    });
    return contractInstance;
};
