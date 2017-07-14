/*
* Lambda function code for the CloudFormer Amazon Alexa Skill
* Currently Supported Features: Create, Delete, List Templates, Template Count and Output to Console (CloudWatch Log)
*
* @author rush.soni@capgemini.com
* @version 1.2
*/

'use strict';

//Add AWS sdk dependency
var AWS = require('./node_modules/aws-sdk');

//Add dependency to CloudFormer scripts
var Stack = new require('./node_modules/cloudformer-node');

//Add dependency to Alexa SDK
var Alexa = new require('./node_modules/alexa-sdk');

//Create an object used to access S3
var s3 = new AWS.S3({apiVersion: '2006-03-01'});

var bucket = "cloudformer-eu-west-1";

//Promise used when checking maps accquired using the AWS SDK
var mapPromise = new Promise(
  function(resolve, reject){

    var map = produceKeyUrlMap(bucket, 1000);

    if(map != null && map != {}){
      resolve(map);
    }
    else {

      var errorMsg;

      if(map == {}){
        errorMsg = "There are no keys in" + bucket;
      }
      else if(map == null){
        errorMsg = "The S3 Bucket you specified doesn't exist."
      }

      reject(errorMsg);
    }
});


//Handling of intents from Alexa Skills Kit
var handlers = {

  //Logic for creating a Stack
  'CloudFormerCreateIntent': function() {

    //Initialise Stack instance.
    var stackName = 'cloudformer-stack-test';
    var theStack = new Stack(stackName);

    //Create stack from amazon web services
    theStack.apply('https://s3-eu-west-1.amazonaws.com/cloudformer-eu-west-1/cloudformer_basic_template.json', {
      Parameters: {},
      DisableRollback: false,
      Capabilities: [],
      NotificationARNs: [],
      Tags: {
        Name: stackName
      },
    }, console.log);

    this.emit(':tell', "your stack has been created");
    return;

  },

  //Logic for deleteing Stack
  'CloudFormerDeleteIntent': function() {

    //Initialise Stack instance.
    var stackName = 'cloudformer-stack-test';
    var theStack = new Stack(stackName);

    //Request the stack be deleted.
    theStack.delete(console.log);

    this.emit(':tell', "your stack has been deleted");
  },

  //Logic for listing the available templates
  'CloudFormerListTemplateIntent': function() {

    //Used to access alexa-sdk for emiting from a Alexa Device
    var self = this;

    var shortPause = "<break time='1s'/>";
    var speechOutput = 'Here is a list of cloud formation templates available in your S3 bucket' + shortPause;

    //Function logic for processing mapPromise for Listing maps.
    mapPromise.then(

      // Success: Case where the mapPromise has been sucessfully resolved and map contains objects..
      function(map) {
        //for each object within the bucket output it's description
        for (var key in map) {

          //Trims key removing the file extension
          speechOutput += key + "; " + map[key].name + shortPause;

        }

        self.emit(':tell', speechOutput);
      },
      // Fail: Case where the map returns empty
      function(errorMsg){

        //log error in console and then have alexa emit the message.
        console.error(new Error(errorMsg));
        self.emit(':tell', errorMsg);

      }
    );

    },

  //Logic to output the count of JSON templates within an S3 Bucket
  'CloudFormerOutputTemplateCountIntent': function() {

    var self = this;

    //Function logic for processing mapPromise for returning the count of objects in the s3 bucket.
    mapPromise.then(

      // Case where the mapPromise has been sucessfully resolved and map contains objects..
      function(map) {

        var template_counter = 0;

        //for each object within the bucket output it's description
        for (var key in map) {
          template_counter += 1;
        }

        self.emit(':tell', 'Your S3 bucket has ' + template_counter + " cloud formation templates.");
      },
      // Case where the map returns empty
      function(errorMsg){

        //log error in console and then have alexa emit the message.
        console.error(new Error(errorMsg));
        self.emit(':tell', errorMsg);

      }
    );
  }
}

/*
* Register alexa handlers, which deal with intent specific calls for the cloud former skill.
*/
exports.createCloudHandler = (event, context, callback) => {

      var alexa_handler = Alexa.handler(event, context, callback);
      alexa_handler.appId = 'amzn1.ask.skill.c2500316-170e-41cc-9c25-45788bd2b814';
      alexa_handler.registerHandlers(handlers);
      alexa_handler.execute();

};

/*
* Produces a mapping of  (Integer -> CloudFormation Template URL)
*/
function produceKeyUrlMap(bucketName, maxKeyCount){

  var params = {
    Bucket: bucketName,
    MaxKeys : maxKeyCount
  };

  //Counter used to keep track of read in templates.
  var template_counter = 0;

  var self = this;

  //POST a request to aws to list objects in the specified bucket
  var request = s3.listObjectsV2(params);

  var promise = request.promise();

  var bucket_list = [];

  return promise.then(
    //Success: successfully returned response object.
    function(data){
      //for each cloudformation template key in the bucket add it to a map.
      for(var i = 0; i < data.Contents.length; i++){

          var bucket_item = data.Contents[i];

          if(bucket_item.Key.includes(".json")){

            //increment counter for new map address.
            template_counter++;

             // get the cloud formation key.
             var cloudformation_template_key = bucket_item.Key;

             //Parameters for GET request for URL associated with the key.
             var params = {
               Bucket: 'cloudformer-eu-west-1',
               Key: cloudformation_template_key
             };

             //Create a javascript object map to contain
             bucket_list[template_counter] = {
               'name': params.Key.replace(/\.[^/.]+$/, ""), //removes extension from file name
               'url' : s3.getSignedUrl('getObject', params) // gets the signed url.
             };
          }
      }
      return bucket_list;

    },
    //Failure: couldn't get a list of objects with the provided parameters.
    function(error){
      console.log("The bucket you provided doesn't exist");
      return null;
    }
  );

}
