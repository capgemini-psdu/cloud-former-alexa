/*
* Lambda function code for the CloudBuilder Amazon Alexa Skill
* Currently Supported Features: Create, Delete, Output to Console (CloudWatch Log)
*
* @author rush.soni@capgemini.com
* @version 1.0
*/

'use strict';

//Add AWS sdk dependency
var AWS = require('./node_modules/aws-sdk');

//Add dependency to CloudFormer scripts
var Stack = new require('./node_modules/cloudformer-node');

//Add dependency to Alexa SDK
var Alexa = new require('./node_modules/alexa-sdk');

//Handling of intents from Alexa Skills
var handlers = {

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

  'CloudFormerDeleteIntent' : function () {

    //Initialise Stack instance.
    var stackName = 'cloudformer-stack-test';
    var theStack = new Stack(stackName);

    //Request the stack be deleted.
    theStack.delete(console.log);

    this.emit(':tell', "your stack has been deleted");
  }

}

/*
* Handler: contains lambda function logic.
*/
exports.createCloudHandler = (event, context, callback) => {

      var alexa_handler = Alexa.handler(event, context, callback);
      alexa_handler.appId = 'amzn1.ask.skill.c2500316-170e-41cc-9c25-45788bd2b814';
      alexa_handler.registerHandlers(handlers);
      alexa_handler.execute();

};
