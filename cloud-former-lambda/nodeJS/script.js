/*
* Lambda function code for the CloudFormer Amazon Alexa Skill
* Currently Supported Features: Create, Delete, List Templates, Template Count and Output to Console (CloudWatch Log)
*
* @author rush.soni@capgemini.com
* @version 1.1
*/

'use strict';

//Add AWS sdk dependency
var AWS = require('./node_modules/aws-sdk');

//Add dependency to CloudFormer scripts
var Stack = new require('./node_modules/cloudformer-node');

//Add dependency to Alexa SDK
var Alexa = new require('./node_modules/alexa-sdk');

//Handling of intents from Alexa Skills Kit
var handlers = {

   //Logic for creating a Stack
  'CloudFormerCreateIntent': function () {

    //Initialise Stack instance.
    var stackName = 'cloudformer-stack-test';
    var theStack = new Stack(stackName);

      //Create stack from amazon web services
      theStack.apply('https://s3-eu-west-1.amazonaws.com/cloudformer-eu-west-1/cloudformer_basic_template.json', {
          Parameters : {},
          DisableRollback : false,
          Capabilities : [],
          NotificationARNs : [],
          Tags : {
              Name : stackName
          },
      }, console.log);

      this.emit(':tell', "your stack has been created");
      return;

  },

   //Logic for deleteing Stack
  'CloudFormerDeleteIntent' : function () {

    //Initialise Stack instance.
    var stackName = 'cloudformer-stack-test';
    var theStack = new Stack(stackName);

    //Request the stack be deleted.
    theStack.delete(console.log);

    this.emit(':tell', "your stack has been deleted");
  },

   //Logic for listing the available templates
  'CloudFormerListTemplateIntent' : function () {

    //Create an object used to access S3
    var s3 = new AWS.S3({apiVersion: '2006-03-01'});

    //Pass parameters for getting information from buckets
    var params = {
      Bucket : "cloudformer-eu-west-1",
      MaxKeys : 1000
    };

    //POST a request to aws to list objects in the specified bucket
    var request = s3.listObjectsV2(params, function (err, data){

      //Get a list of  JSON objects from the bucket
      if (err) {
        //an error occured.
        console.log(err, err.stack); // an error occurred
      }
      else{
        return data;
      }

    });

    var self = this;

    //success response
    var success_response = request.on('success', function(response){

      //Succesfully located the bucket an it's contents
      var template_counter = 1;


      var shortPause = "<break time='1s'/>";
      var speechOutput = 'Here is a list of cloud formation templates available in your S3 bucket' + shortPause;


      //for each object within the bucket output it's description
      for(var i = 0; i < response.data.Contents.length; i++){

          var bucket_item = response.data.Contents[i];

          if(bucket_item.Key.includes(".json")){

             var cloudformation_template = bucket_item;

             //Trims key removing the file extension
             var cloudformation_template_name = cloudformation_template.Key.replace(/\.[^/.]+$/, "");

             speechOutput +=  template_counter + "; " + cloudformation_template_name + shortPause;

             template_counter += 1;

          }

      }

      self.emit(':tell', speechOutput);

      return;

    });

  },

   //Logic to output the count of JSON templates within an S3 Bucket
  'CloudFormerOutputTemplateCountIntent' : function () {

    //Create an object used to access S3
    var s3 = new AWS.S3({apiVersion: '2006-03-01'});

    //Pass parameters for getting information from buckets
    var params = {
      Bucket : "cloudformer-eu-west-1",
      MaxKeys : 1000
    };

    //POST a request to aws to list objects in the specified bucket
    var request = s3.listObjectsV2(params, function (err, data){

      //Get a list of  JSON objects from the bucket
      if (err) {
        //an error occured.
        console.log(err, err.stack); // an error occurred
      }
      else{
        return data;
      }

    });

    var self = this;

    //success response
    var success_response = request.on('success', function(response){

      //Succesfully located the bucket an it's contents
      var template_counter = 0;

      //for each object within the bucket output it's description
      for(var i = 0; i < response.data.Contents.length; i++){

          var bucket_item = response.data.Contents[i];

          if(bucket_item.Key.includes(".json")){
             template_counter += 1;
          }

      }

      self.emit(':tell', 'Your S3 bucket has ' + template_counter + " cloud formation templates.");

      return;

    });

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
