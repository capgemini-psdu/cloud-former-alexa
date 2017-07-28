/*
 * Lambda function code for the CloudFormer Amazon Alexa Skill
 * Currently Supported Features: Dynamic Create (protected), Dynamic Delete (protected), List Templates, Template Count, Status of CloudFormer stacks, Advanced Help
 *
 * @author rush.soni@capgemini.com
 * @version 1.6.4
 */

'use strict';

//Add AWS sdk dependency
const AWS = require('./node_modules/aws-sdk');

//Add dependency to CloudFormer scripts
const Stack = new require('./node_modules/cloudformer-node');

//Add dependency to Alexa SDK
const Alexa = new require('./node_modules/alexa-sdk');

//Package required for producing a random auth code.
const auth = new require('./node_modules/random-number');

const sns = new AWS.SNS({
  apiVersion: '2010-03-31'
});

const s3 = new AWS.S3({
  apiVersion: '2006-03-01'
});

const cloudFormation = new AWS.CloudFormation({
  apiVersion: '2010-05-15'
});

//Define the range of valid values for generated auth codes.
const authParams = {

  min: 1000,
  max: 9999,
  integer: true
};

const applicationId = 'amzn1.ask.skill.c2500316-170e-41cc-9c25-45788bd2b814';

//The timeout count in seconds provided to the authentication key generated for valid users.
const authTimeout = 120;

//The Region in which the bucket is placed within S3.
const bucketRegion = 'eu-west-1';

//The Bucket name in which cloud formation templates are placed.
const bucket = "cloudformer-eu-west-1";

const userFolder = "users/";

//The file path for the access file which contains permitted users.
const userFile = userFolder + "access.json";

const shortPause = "<break time='1s'/>";

//Processes map object according to success and failure of s3.listObjectsV2
const mapPromise = new Promise(
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
const handlers = {

  //Logic for creating a Stack
  'CloudFormerCreateIntent': function() {

    var self = this;

    //Have alexa request required slots to be filled.
    delegateToAlexa(self);

    var slots = self.event.request.intent.slots;

    //Validate mandatory slots input.
    var optionFilled = validateSlot(slots.OptionNumber);

    var userFilled = validateSlot(slots.Users);

    //Get boolean evaluation
    var slotValuesFilled = optionFilled && userFilled;

    //Code to execute upon promise resolution
    authenticate(self, slotValuesFilled).then(
      function(user) {
        //Function logic for processing mapPromise for Listing maps.
        mapPromise.then(

          //Success: Case where the mapPromise has been sucessfully resolved and map contains objects..
          function(map) {

            //Get the user specified option
            var optionNumber = self.event.request.intent.slots.OptionNumber.value;

            if (map[optionNumber] != null) {

              var stackName = validateStackName(map[optionNumber].name);
              var theStack = new Stack(stackName);

              //Create stack from amazon web services from the chosen template placed based within the specified bucket.
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

            }
            else {
              console.error("Item not found within the S3 bucket.");
              return self.emit(':tell', "The option number you specified doesn't exist within the S3 bucket");
            }
          },
          //Fail: Case where the map returns empty
          function(errorMsg) {

            //log error in console and then have alexa emit the message.
            console.error(errorMsg);
            return self.emit(':tell', errorMsg);

          }
        );

      },
      function(error) {
        self.emit(':tell', 'Access Denied');
      }
    );

  },

  //Logic for deleteing Stack
  'CloudFormerDeleteIntent': function() {
    var self = this;

    //Have alexa request required slots to be filled.
    delegateToAlexa(self);

    var slots = self.event.request.intent.slots;

    //Validate mandatory slots input.
    var optionFilled = validateSlot(slots.OptionNumber);
    var userFilled = validateSlot(slots.Users);

    //Get boolean evaluation
    var slotValuesFilled = optionFilled && userFilled;

    //Code to execute upon promise resolution
    authenticate(self, slotValuesFilled).then(
      function(user) {
        //Function logic for processing mapPromise for Listing maps.
        mapPromise.then(

          //Success: Case where the mapPromise has been sucessfully resolved and map contains objects..
          function(map) {

            //Get the user specified option
            var optionNumber = self.event.request.intent.slots.OptionNumber.value;

            if (map[optionNumber] != null) {
              var stackName = validateStackName(map[optionNumber].name);
              var stackNameOutput = alexaOutputStackName(map[optionNumber].name);
              var theStack = new Stack(stackName);

              //Create stack from amazon web services
              theStack.delete(console.log);

              return self.emit(':tell', "your stack, " + stackNameOutput + "has been deleted");

            }
            else {
              console.error("Cannot find stack with the name " + stackNameOutput + "in the list of running stacks.");
              return self.emit(':tell', "Cannot find stack with the name " + stackNameOutput + "in the list of running stacks.");
            }
          },
          //Fail: Case where the map returns empty
          function(errorMsg) {

            //log error in console and then have alexa emit the message.
            console.error(errorMsg);
            return self.emit(':tell', errorMsg);

          }
        );
      },
      function(error) {
        self.emit(':tell', 'Access Denied');
      }
    );
  },

  //Logic for listing the available templates
  'CloudFormerListTemplateIntent': function() {

    //Used to access alexa-sdk for emiting from a Alexa Device
    var self = this;
    var speechOutput = 'Here is a list of cloud formation templates available in your S3 bucket' + shortPause;

    //Function logic for processing mapPromise for Listing maps.
    mapPromise.then(

      //Success: Case where the mapPromise has been sucessfully resolved and map contains objects..
      function(map) {
        for (var key in map) {
          //add each [option,name] pair followed by a pause to the output
          speechOutput += key + "; " + map[key].name + shortPause;
        }

        self.emit(':tell', speechOutput);
      },
      //Fail: Case where the map returns empty
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

      //Case where the mapPromise has been sucessfully resolved and map contains objects.
      function(map) {
        self.emit(':tell', 'There are' + map.length - 1 + " cloud formation templates in your bucket");
      },
      //Case where the map returns empty
      function(errorMsg) {
        //Log error in console and then have alexa emit the message.
        console.error(errorMsg);
        self.emit(':tell', errorMsg);

      }
    );
  },

  //List created stacks from cloud former.
  'CloudFormerStatusIntent': function() {

    var self = this;

    mapPromise.then(

      function(map) {
        //Returns a list of CloudFormation stacks launched from cloud former
        getStatus(map).then(

          function(statusMap) {

            if (statusMap.length != 0) {
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
          },
          function(errorMsg) {
            console.log(errorMsg);
          }
        );

      },
      function(error) {
        console.log(error);
      }
    );
  },

  //Get the template name from it's corresponding option number.
  'CloudFormerOptionInfoIntent': function() {

    var self = this;

    delegateToAlexa(self);

    mapPromise.then(
      function(map) {

        var optionNumber = self.event.request.intent.slots.OptionNumber.value;

        //Options slot unfilled due to not specifiying the option number, so elicit the slot to fill it.
        if (typeof optionNumber === 'undefined') {
          self.emit(":elicitSlot", "OptionNumber", "What option number would you like to know the name for", null, null);
        }

        //Output information associated with option
        if (map[optionNumber] != null && map[optionNumber] != {} && typeof map[optionNumber] !== 'undefined') {
          self.emit(':tell', "Here is the name of the template associated with option " + optionNumber + " " + shortPause + alexaOutputStackName(map[optionNumber].name));
        }
        //Option number not associated with a CloudFormation template.
        else {
          self.emit(':tell', "There isn't a template associated with option number " + optionNumber + shortPause + " there are only " + (map.length - 1) + " templates in the bucket");
        }
      },
      function(error) {
        self.emit(':tell', 'there are no cloud formation templates in ' + bucket);
      }
    );
  },

  //Handle help regarding custom cloud former intents
  'CloudFormerHelpIntent' : function () {

    var slots = this.event.request.intent.slots;

    var message = "Here is a list of actions that can be invoked using Cloud Former." + shortPause;

    var actionsList = "Create, Delete, List, Count, Status, Option";

    var askSlot = shortPause + " Please specify one of the option names";

    //Check if the help slot has been filled, otherwise elicit a value.
    if(!validateSlot(slots.HelpTopics)){
      this.emit(":elicitSlot", "HelpTopics", message + actionsList + askSlot, null, null);
    }

    //Check intents and provide specific help
    switch(slots.HelpTopics.value){

      case "create":
        this.emit(':tell', "Cloud Former supports the creation of stacks from templates;"
          + "invocation of this action will require elevated privilege." + shortPause +
          "simply ask Cloud Former to make a stack to invoke this action");
        break;

      case "delete":
        this.emit(':tell', "Cloud Former supports the deletion of stacks from templates, created by cloudformer;"
          + "invocation of this action will require elevated privilege." + shortPause +
          "simply ask Cloud Former to destroy a stack to invoke this action");
        break;

      case "count":
        this.emit(':tell', "You can ask Cloud Former to give you a count of templates in your bucket, created by cloudformer;"
         + shortPause + "simply ask Cloud Former how many temples are there to invoke this action");
        break;

      case "list":
        this.emit(':tell', "You can ask Cloud Former to list the option number and the associated name of all templates in your bucket;"
         + shortPause + "simply ask Cloud Former to list available templates to invoke this action");
        break;

      case "status":
        this.emit(':tell', "You can ask Cloud Former to give you a list of running stacks which have been created by Cloud Former;"
         + shortPause + "simply ask Cloud Former to show the status to invoke this action");
        break;

      case "option":
        this.emit(':tell', "You can ask Cloud Former for name of a template which is associated to an option number;"
         + shortPause + "simply ask Cloud Former to tell me about an option to invoke this action");
        break;

      default:
        this.emit(':tell', "Sorry, i don't know how to help you with this");
        break;

    }

  },

  'Unhandled': function() {
    this.emit(':tell', "Sorry i didn't quite catch that, please try again");
  }

};

/*
 * Register alexa handlers, which deal with intent specific calls for the cloud former skill.
 */
exports.createCloudHandler = (event, context, callback) => {

  var alexa_handler = Alexa.handler(event, context, callback);
  alexa_handler.appId = applicationId;
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

  //Counter used to keep track of templates in bucket.
  var template_counter = 0;

  var self = this;

  //POST a request to aws to list objects in the specified bucket
  var request = s3.listObjectsV2(params);

  var promise = request.promise();

  var listOfObjects = promise.then(
    //Success: successfully returned response object.
    function(data) {

      var bucketList = [];

      //for each CloudFormation template key in the bucket add it to a map.
      for (var i = 0; i < data.Contents.length; i++) {

        var bucketItem = data.Contents[i];

        if (bucketItem.Key.includes(".json") && bucketItem.Key.indexOf('/') == -1) {

          //increment counter for new map address.
          template_counter++;

          //get the cloud formation key.
          var cloudformation_template_key = bucketItem.Key;
          var url = "https://s3-" + bucketRegion + ".amazonaws.com/" + bucketName + "/" + cloudformation_template_key;

          var stackName = cloudformation_template_key.replace(/\.[^/.]+$/, "");

          bucketList[template_counter] = {
            'name': stackName,
            'url': url
          };

        }
      }

      return bucketList;
    },
    //Failure: couldn't get a list of objects with the provided parameters.
    function(error) {
      console.log("The bucket you provided doesn't exist");
      return null;
    }
  );

  return listOfObjects;

}

/*
 * Check if the inputed CloudFormation template has been instantiated.
 */
function getStatus(map) {

  var params = {
    StackStatusFilter: ['CREATE_COMPLETE']
  };

  //Fetch the list of CloudFormation stacks, look at the stackName and compare it to that from the options map
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
      //return to be used in another promise.
      return cloudFormerStacks;
    },
    //Case where there are no stacks
    function(err) {
      console.log("Couldn't get the list of completed stacks from Cloud Formation.");
    }

  );

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

/*
 * Authenticates the spoken user name.
 */
function authenticateUsers(spokenUser, self, callback) {

  var topicParams = {
    Name: 'AuthKey'
  };

  //generate an auth key
  var authKey = auth(authParams);

  //Send Auth Code.
  return sns.createTopic(topicParams, function(err, data) {

    //Handle initial error in creating topic.
    if (err) {
      console.log("Couldn't create a topic for registering users to SMS alerts for AuthKeys.", err.stack);
      return false;
    }
    //Topic created.
    else {
      var topicKey = data.TopicArn;

      //get JSON file used to store user details.
      var objectParams = {
        Bucket: bucket,
        Key: userFile
      };

      //get access file for set of users.
      s3.getObject(objectParams, function(errorMsg, response) {

        if (errorMsg) {
          console.log("Couldn't locate " + userFile + " object from within the " + bucket);
          return false;
        }
        else {
          //Read in and parse access file into a JSON object
          var contactsString = response.Body.toString();
          var contacts = JSON.parse(contactsString);

          var userString = spokenUser.toString().toLowerCase();

          //Get user from slot.
          if (userString != null && userString != "") {

            var validUser = false;

            //check if the user exists within the allowed users.
            for (var key in contacts.users) {
              //Valid user, begin auth process.
              if (userString == contacts.users[key].name) {

                //validate user.
                validUser = true;

                var authUser = contacts.users[key];

                //get user specific auth key.
                var fileKey = userFolder + authUser.name + "_" + "auth_request.json";

                var authFileParams = {
                  Bucket: bucket,
                  Key: fileKey
                };

                //Check if auth file exists, if it doesn't create one and then send the key. if it does exist send the exisiting key
                var authFilePromise = s3.getObject(authFileParams).promise();

                authFilePromise.then(
                  function(fileFound) {

                    console.log("fileFound");

                    var keyJSON = JSON.parse(fileFound.Body.toString());

                    var authCode = keyJSON.authKey;

                    //Subscribes authorised user if they haven't already, otherwise gets the default subscription
                    var subscribeParams = {
                      Protocol: "sms",
                      TopicArn: topicKey,
                      Endpoint: authUser.contactNumber,
                    };

                    //Subscribe User
                    sns.subscribe(subscribeParams).send();

                    //POST authKey to user phoneNumber
                    var smsParams = {
                      PhoneNumber: authUser.contactNumber,
                      Message: 'AuthKey : ' + authCode
                    };

                    //Send verified user an sms containing the authKey
                    sns.publish(smsParams).send();

                    console.log("Sent Auth Key to device");

                    console.log("Saved AuthKey: " + authCode);

                    var slots = self.event.request.intent.slots;

                    //Check if not set, otherwise recursive call overides the slot value.
                    if (!validateSlot(slots.AuthKey)) {
                      self.emit(':elicitSlot', 'AuthKey', "You will have been sent a key to your mobile device, please tell me the key", null, null);
                    }

                    var userAuthKey = self.event.request.intent.slots.AuthKey.value;

                    console.log("Spoken AuthKey: " + userAuthKey);

                    //Accept user if keys match
                    if (userAuthKey == authCode) {
                      deleteAuthKey(userString, self);
                      callback(true);
                    }
                    else {
                      callback(false);
                    }

                  }
                ).catch(
                  //Create file and recurse function (could loop infinitely if theres an error in file found code.)
                  function(fileNotFound) {

                    console.log("fileNotFound");

                    //write authKey with timestamp to s3 bucket;
                    var authRequest = {
                      authKey: authKey,
                      permissions: authUser.permissions
                    };

                    var output = JSON.stringify(authRequest);

                    var putParams = {
                      Body: output,
                      Bucket: bucket,
                      Key: fileKey,
                    };

                    //only send text after the object has been written
                    var keyPutPromise = s3.putObject(putParams).promise();

                    //Upon sucessfully writing json file containing auth key to S3, recall authenticateUsers function
                    keyPutPromise.then(function(data) {
                      authenticateUsers(spokenUser, self, callback);
                    });
                  }
                );

                break;
              }
            }

            //invalid user.
            if (!validUser) {
              console.log("Invalid user name, please request access from an administrator");
              self.emit(':tell', spokenUser + shortPause + "You are not authorised to call this action, please request access from an administrator");
              return;
            }
          }
        }
      });
    }

  });
}

/*
 * Wrapper function used for verification when carrying out costed intents.
 */
function authenticate(self, slotValuesFilled) {
  //Make sure users authenticated before continuing
  return new Promise(function(resolve, reject) {

    console.log("Slots Filled: " + slotValuesFilled);

    var slots = self.event.request.intent.slots;

    if (!slotValuesFilled) {
      reject(null);
    }
    else {
      authenticateUsers(slots.Users.value, self, function(validated) {

        if (validated) {
          //Pass name back if validation passes.
          resolve(slots.Users.value);
        }
        else {
          //Pass null to indicate failure
          reject(null);
        }

      });
    }
  });
}

/*
 * Wrapper function used to delete the users auth key in S3.
 */
function deleteAuthKey(user, self) {

  var params = {
    Bucket: bucket,
    Key: userFolder + user + "_auth_request.json"
  };

  console.log(userFolder + user + "_auth_request.json");
  return s3.deleteObject(params).send();
}

/*
 * Has alexa to fill required slots at the start of the skill
 */
function delegateToAlexa(self) {
  //Manually request dialog delegate to fill required slots as self.emit(:delegate) would end the session
  if (self.event.request.dialogState == "STARTED" || self.event.request.dialogState == "IN_PROGRESS") {
    self.context.succeed({
      "response": {
        "directives": [{
          "type": "Dialog.Delegate"
        }],
        "shouldEndSession": false
      },
      "sessionAttributes": {}
    });
  }
}

/*
 * Validates the value for slots.
 */
function validateSlot(slot) {
  return typeof slot.value !== 'undefined' && slot.value != null;
}
