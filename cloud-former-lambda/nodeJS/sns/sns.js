var Alexa = require('alexa-sdk');
var AWS = require('aws-sdk');
var randomstring = require("randomstring");
var sns = new AWS.SNS();


sns.createTopic({
	Name: 'raj'
}, function(err, data) {
  if (err) console.log(err, err.stack); // an error occurred
  else     console.log("Topic created", data);           // successful response

  
  var TopicArn = data.TopicArn;

var s3 = new AWS.S3();


s3.getObject({ Bucket: 'cloudformer-eu-west-1', Key: 'mycontacts.json' }, function(err, data)
{
    if (!err)
        console.log(data.Body.toString());
		
		var json = JSON.parse(data.Body.toString());
		console.log("data", json);
    //var fileContents = data.Body.toString();

    sns.subscribe({
    	//Name: json.users.[Name],
		Protocol: 'sms',
		TopicArn: TopicArn,
		Endpoint: TopicArn
    }, function(error, data) {
        if (err) console.log("error when subscribe", error);
        else console.log("Subscribed Successfully", data);

//sns.subscribe(subscription1);
//sns.subscribe(subscription2);

		//var SubscriptionArn = data.SubscriptionArn;

var ran = randomstring.generate({
	length: 6,
	charset: 'numeric'
});

console.log("token generated successfully: ", ran);

/**function(err, data) {
	if (json.users.Name = " ") console.log(sns.publish());
	else (err) console.log("cannot send message", data);**/
//for(var i = 0; i < json.users[i]; i++){


    sns.publish({
    	//Name: json.users[0].Name,
    	PhoneNumber: json.users[0].PhoneNumber,
    	//MessageStructure: 'json',
		Message: 'Your unique code is: ' + ran
    }, function(err_publish, data) {

            if (err_publish) console.log('Error sending a message', err_publish);
                else console.log('Sent message:', data.MessageId);
                
            /**sns.unsubscribe({
            	SubscriptionArn: SubscriptionArn
            }, function(err, data) {
                if (err) console.log("err when unsubscribe", err);
                else console.log("Unsubscribed Successfully", data);
                });**/
             });
    });
});
});

 

exports.handler = function(event, context) {
    console.log("\n\nSuccessful!\n\n");

};

