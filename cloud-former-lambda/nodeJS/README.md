# CloudFormer Alexa

We have created a VoiceOps Skill which allows a user to deploy and manage CloudFormation Stacks from CloudFormation Templates within AWS just by speaking to Alexa; neat, right! :)

## Alexa Skill Creation
This section details how you would set up the Alexa skill for Cloud Former

### Configuring Skill Information
1. Set the Skill Type to "Custom Interaction Model"
1. Select either English(UK) or English(US) for Language
1. Select either English(UK) or English(US) for Language
1. Create a new Alexa Skill and name it "CloudFormer" and give it an invocation name of "cloud former"
1. Select "No" for all Global Fields.

### Building the Interaction Model
1. Select the Launch Skill Builder (Beta) button.
1. Select </> Code Editor from left-hand menu and proceed to upload the file JSON interaction model located here: __~/cloud-former-alexa/alexa-skills-components/skill-builder.json__".
1. Scroll down the left-hand menu and find the Slot Type called People, within this slot you will add the first names/nicknames (lowercase) of Users to which you will grant elevated priveleges.
1. Hit save and then build the model, this should take a few minutes.

### Configuring Endpoints
1. Select __AWS Lambda ARN__ for the service endpoint
1. Select a geopgraphical region (or both)
1. Enter the Application Resource Name (ARN) of the lambda function which you will create in the __Lambda Function Configuration__ section.
1. Select __No__ for Account linking and then leave everything else unchecked.


## Lambda Function Configuration
There are a few components that need to be configured to setup the code for Lambda

Changes to the code are made in this file: __~/cloud-former-alexa/cloud-former-lambda/nodeJS/script.js__, unless specified otherwise.

### Configuring the Application Id for the Alexa Skill

You need to get the __Alexa Skill Application ID__ from the skill you created in the previous step assign it to the applicationId constant.
```
const applicationId = 'amzn1.ask.skill.<ID>';
```

### Configuring the authentication parameters
Located below is the code which can be configured to change the duration and range of the authentication code.

```
//Define the range of valid values for generated auth codes.
const authParams = {
  min: 1000,
  max: 9999,
  integer: true // Don't change this.
};

// The timeout count in seconds provided to the authentication key generated for valid users.
const AUTH_TIMEOUT = 120;
```
### Configuring the storage location within S3
Located below is the code which can be configured to change the location in which the CloudFormation Templates are stored in addition to access credentials.
```
// The Region in which the bucket is placed within S3.
const bucketRegion = 'eu-west-1';

// The Bucket name in which cloud formation templates are placed
// NOTE: Ensure that all templates are stored in the root of the S3 bucket.
const bucket = "cloudformer-eu-west-1";

const userFolder = "users/";

// The file path for the access file which contains permitted users
// NOTE: the access file should be stored in a folder within the bucket and not the root.
const userFile = userFolder + "access.json";
```

### Access File Layout
This file is to be stored in S3, in the path outlined by the constant: userFile, in the code snippet above.
```
{
  "users" : [
    {
      "name" : "joe",
      "contactNumber" : "+44XXXXXXXXXX",
    },

    {
      "name" : "blogs",
      "contactNumber" : "+44XXXXXXXXXX",
    },
  ]
}
```

### Lambda Function Creation
1. Use the __Alexa Skills Kit (ASK)__ for the lambda function trigger.
1. Give your lambda function a name and description.
1. Set the runtime to the latest NodeJS version available.
1. Change __Code entry type__ to Upload a .ZIP File.
1. Proceed to zip up __node_modules and script.js__ into a single zip file and upload said file to Lambda.
1. Set the handler name to script.createCloudHandler.
1. Under the __Role*__ option select __Create a custom role__ and then provide full access to every service within AWS (this allows CloudFormer to create any type of infrastructure).
1. Select Advanced Settings and change the __Timeout*__ to 5 Minutes (Maximum)



## API Reference

### Authentication Wrapper

Authentication wrapper is wrapped around any code that requires authenticating. Authentication works by sending an authorised user a OTP (One Time Password). 
You will need to add the user to the access.json file in your s3 bucket for this to work.

__NOTE:__ Authentication requires for the Intent which requires authenticating to meet the following prerequisites

1. Have a __Users__ slot which is assigned a custom slot type which contains list of permitted users names in lowercase.
1. Have an __AuthKey__ slot with a Slot Type of __AMAZON.NUMBER__
1. The developer has set up the equivalent of an users/access.json file within S3.

__NOTE:__ The Users slot for the intent can either contain a [Subset](https://en.wikipedia.org/wiki/Subset) of the users in the access file or be a [Perfect Set](https://en.wikipedia.org/wiki/Perfect_set).
This design approach allows for the developer to grant varying levels of access too different users of the CloudFormer skill. i.e. Granting a set of users access to one intent but not another.



```
'CloudFormer<ACTION-NAME>Intent' : function() {
  
  var self = this;
  
  authenticate(self, slotValuesFilled).then(

      //Authentication Successful, callback is passed back the users name.
      function(user) {
        //Protected Code, ran on successful authentication
      },
      
      //Authentication Failed, callback is passed back a null value.
      function(error){
        //Handle failed authentication.
      }
  );
}
````

## Contributors
* Rushil Soni - nodeJS
* Nagaraj Govindaraj - CloudFormation Templates

### Developer
* Rushil Soni

### Author
* Rushil Soni

## License

cloudformer-node npm package (mikgan) | https://www.npmjs.com/package/cloudformer-node | MIT OpenLicense

random-number npm package (ashnur) | https://www.npmjs.com/package/random-number | BSD 2-clause "Simplified" License

This project is Copyright (c) 2017 by Capgemini UK.
