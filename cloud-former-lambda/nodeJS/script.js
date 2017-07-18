/*
 * Lambda function code for the CloudFormer Amazon Alexa Skill
 * Currently Supported Features: Dynamic Create, Dynamic Delete, List Templates, Template Count and Status of CloudFormer stacks.
 *
 * @author rush.soni@capgemini.com
 * @version 1.4
 */

'use strict';

//Add AWS sdk dependency
const AWS = require('./node_modules/aws-sdk');

//Add dependency to CloudFormer scripts
const Stack = new require('./node_modules/cloudformer-node');

//Add dependency to Alexa SDK
const Alexa = new require('./node_modules/alexa-sdk');

//Create an object used to access S3
const s3 = new AWS.S3({
  apiVersion: '2006-03-01'
});

const cloudFormation = new AWS.CloudFormation({
  apiVersion: '2010-05-15'
});

var bucket = "cloudformer-eu-west-1";

var bucket_region = 'eu-west-1';

//Promise used when checking maps accquired from AWS using the AWS SDK
var mapPromise = new Promise(
  function(resolve, reject) {

    var map = getS3BucketObjects(bucket, 1000);

    if (map != null && map != {}) {
      resolve(map);
    } else {

      var errorMsg;

      if (map == {}) {
        errorMsg = "There are no keys in" + bucket;
      } else if (map == null) {
        errorMsg = "The S3 Bucket you specified doesn't exist."
      }

      reject(errorMsg);
    }
  });

//Handling of intents from Alexa Skills Kit
var handlers = {

  //Logic for creating a Stack
  'CloudFormerCreateIntent': function() {

    var self = this;

    //Function logic for processing mapPromise for Listing maps.
    mapPromise.then(

      // Success: Case where the mapPromise has been sucessfully resolved and map contains objects..
      function(map) {

        //Get the user specified option
        var optionNumber = self.event.request.intent.slots.OptionNumber.value;

        if (map[optionNumber] != null) {

          var stackName = validateStackName(map[optionNumber].name);
          var theStack = new Stack(stackName);

          //Create stack from amazon web services
          theStack.apply(map[optionNumber].url, {
            Parameters: {},
            DisableRollback: false,
            Capabilities: [],
            NotificationARNs: [],
            Tags: {
              Name: "cloudformer:" + map[optionNumber].name
            },
          }, console.log);

          return self.emit(':tell', "your stack, " + alexaOutputStackName(map[optionNumber].name) + " has been created ");

        } else {
          console.error("Item not found within the S3 bucket.");
          return self.emit(':tell', "The option number you specified doesn't exist within the S3 bucket");
        }
      },
      // Fail: Case where the map returns empty
      function(errorMsg) {

        //log error in console and then have alexa emit the message.
        console.error(errorMsg);
        return self.emit(':tell', errorMsg);

      }
    );
  },

  //Logic for deleteing Stack
  'CloudFormerDeleteIntent': function() {
    var self = this;

    //Function logic for processing mapPromise for Listing maps.
    mapPromise.then(

      // Success: Case where the mapPromise has been sucessfully resolved and map contains objects..
      function(map) {

        //Get the user specified option
        var optionNumber = self.event.request.intent.slots.OptionNumber.value;

        if (map[optionNumber] != null) {
          var stackName = validateStackName(map[optionNumber].name);
          var alexaOutputStackName = alexaOutputStackName(map[optionNumber].name);
          var theStack = new Stack(stackName);

          //Create stack from amazon web services
          theStack.delete(console.log);

          return self.emit(':tell', "your stack, " + alexaOutputStackName + "has been deleted");

        } else {
          console.error("Cannot find stack with the name " + alexaOutputStackName + "in the list of running stacks.");
          return self.emit(':tell', "Cannot find stack with the name " + alexaOutputStackName + "in the list of running stacks.");
        }
      },
      // Fail: Case where the map returns empty
      function(errorMsg) {

        //log error in console and then have alexa emit the message.
        console.error(errorMsg);
        return self.emit(':tell', errorMsg);

      }
    );
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
      function(errorMsg) {

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
      function(errorMsg) {

        //log error in console and then have alexa emit the message.
        console.error(errorMsg);
        self.emit(':tell', errorMsg);

      }
    );
  },

  'CloudFormerStatusIntent': function() {

    var self = this;

    mapPromise.then(

      function(map) {

        getStatus(map).then(

          function(statusMap) {

            if (statusMap.length != 0) {
              var shortPause = "<break time='1s'/>";
              var speechOutput = "Here is a list of stacks created by cloud former and their statuses,";
              var counter = 1;

              for (var stack in statusMap) {
                  speechOutput += shortPause + counter + shortPause + statusMap[stack].name + shortPause + "Status, " + statusMap[stack].state;
                  counter++;
              }

              return self.emit(':tell', speechOutput);
            }
            else {
              return self.emit(':tell', 'There are no stacks running which have been created by cloud former');
            }


          }).catch(function(err) {
          console.log(err)
        });

      },
      function(errorMsg) {
        console.log(errorMsg);
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

/*
 * Produces a mapping of  (Integer -> CloudFormation Template URL)
 */
function getS3BucketObjects(bucketName, maxKeyCount) {

  var params = {
    Bucket: bucketName,
    MaxKeys: maxKeyCount
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
    function(data) {
      //for each cloudformation template key in the bucket add it to a map.
      for (var i = 0; i < data.Contents.length; i++) {

        var bucket_item = data.Contents[i];

        if (bucket_item.Key.includes(".json") && bucket_item.Key.indexOf('/') == -1) {

          //increment counter for new map address.
          template_counter++;

          // get the cloud formation key.
          var cloudformation_template_key = bucket_item.Key;
          var url = "https://s3-" + bucket_region + ".amazonaws.com/" + bucketName + "/" + cloudformation_template_key;

          var stackName = cloudformation_template_key.replace(/\.[^/.]+$/, "");

          bucket_list[template_counter] = {
            'name': stackName,
            'url': url
          };
        }
      }

      return bucket_list;

    },
    //Failure: couldn't get a list of objects with the provided parameters.
    function(error) {
      console.log("The bucket you provided doesn't exist");
      return null;
    }
  );

}

/*
 * Check if the inputed CloudFormation template has been instantiated.
 */
function getStatus(map) {

  //TODO get this working

  var params = {
    StackStatusFilter: ['CREATE_COMPLETE']
  };


  // fetch the list from cloudformation stacks, look at the stackName and compare it to that from the map
  var promise = cloudFormation.listStacks(params).promise();

  var statusMap = promise.then(
    function(data) {

      var cloudFormerStacks = [];

      for (var stack in data.StackSummaries) {
        for (var key in map) {
          if (data.StackSummaries[stack].StackName == validateStackName(map[key].name)) {
            cloudFormerStacks.push({
              'name': replaceAll(data.StackSummaries[stack].StackName, '-', ' '),
              'state': alexaOutputStackName(data.StackSummaries[stack].StackStatus)
            });
          }
        }
      }

      return cloudFormerStacks;
    },
    function(err) {
      console.log(err);
    }
  ).catch(function(err) {
    console.log(err);
  });

  return statusMap;


}

/*
 * Formats cloudformation stack name.
 */
function validateStackName(name) {
  return replaceAll(name, '_', '-');
}

/*
 * Formats stack name so that alexa can output it in an acceptable format.
 */
function alexaOutputStackName(name) {
  return replaceAll(name, '_', ' ');
}

/*
 * Remove all instances of charToReplace from input string and replaces them with replacementChar.
 */
function replaceAll(name, charToReplace, replacementChar) {

  if (name.indexOf(charToReplace) == -1) {
    return name;
  }

  return replaceAll(name.replace(charToReplace, replacementChar), charToReplace, replacementChar);

}
