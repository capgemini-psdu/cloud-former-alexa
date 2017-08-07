# CloudFormation Alexa Python

### Prerequisites

Before getting started with this project, you will require:

* An Amazon Echo or Echo Dot (or be willing to use the Amazon simulator.)
* An installation of Python 2.7 on your device, found [here](https://www.python.org/downloads/).
* An Amazon Web Services account.
* An Amazon Developer account.
* Some pre-obtained knowledge on the functionality of AWS [Lambda](https://aws.amazon.com/lambda/) and [Alexa Skills Kit](https://developer.amazon.com/edw/home.html#/skills).

It is also advised to install the necessary module [virtualenv](https://virtualenv.pypa.io/en/stable/), as this will be required during the deployment process. This can be achieved by:

```
setx PATH "%PATH%;C:\Python27\Scripts" (Windows only - Optional)

pip install virtualenv
```

Note: The first line enables 'pip' to be used to install Python modules, and you can skip this line if you have used 'pip' on your machine previously. Additionally, if an error occurs, you may need to close and reopen your CMD terminal window after entering the first line before installing virtualenv.

## Getting Started

First of all, you will need to create an S3 bucket on Amazon Web Services ([AWS](https://aws.amazon.com/)), with permissions available only to yourself, and not public. This bucket will contain user-data, such as phone numbers for Two-Factor Authentication, and so this is important. You will then need to create a directory on your local device, such as "Alexa_Skill", and download the [lambda_function.py file](https://github.com/capgemini-psdu/cloud-former-alexa/blob/master/cloud-former-lambda/Python/tempf/lambda_function.py) to that location. It is important that the filename is not altered throughout this process.

Furthermore, ensure that the region you are in (found at in the top bar of the AWS console) is the same as where you intend the Alexa skill to be used. In this readme, Ireland (eu-west-1) is used, but this can be changed as needed.

### AWS Credentials

Zappa requires [AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/installing.html), the Amazon Command Line Interface. To install this, the following Python module is needed:

```
pip install awscli
```

To obtain the credentials to configure awscli, navigate to [AWS IAM Roles](https://console.aws.amazon.com/iam/):

* Navigate to 'users'.
* Add a user.
* Choose a username, such as 'Zappa-Deployment-User'.
* Enable: Programmatic Access.
* Navigate to the next page.
* Choose 'Attach existing policies directly'.

At this stage, you must decide which permissions you with to grant to Zappa program. The easiest solution is to provide 'AdministratorAccess', but if you wish to be more restrictive, the following are the minimum essentials:

* APIGatewayAdministrator
* AWSLambdaFullAccess
* IAMReadOnlyAccess

(Depending on whether you choose to use AdministratorAccess or minimal permissions, sections of this readme will vary, so please ensure you follow the correct instructions.)

Create and confirm the creation of the user, then note the Access key ID & secret access key, as you will need them momentarily.

(It is possible to be increasingly further restrictive, and is a [topic of open discussion.](https://github.com/Miserlou/Zappa/issues/244))

To configure the AWS CLI, type:

```
aws configure
```

* AWS Access Key ID: (Use the key obtained previously.)
* AWS Secret Access Key: (Use the key obtained previously.)
* Default region name: (Select the region of your S3 bucket location.)
* Default output format: (Select a format you prefer, as this does not impact on this installation. Default = None.)

At this point, discard the secret access key, as it is no longer needed.

### Zappa

Due to the dependencies of the Python modules used within lambda_function.py, there is only one method of deploying the function to AWS Lambda. The automated and simplified deployment service [Zappa](https://github.com/Miserlou/Zappa) can be used, and a detailed guide can be found for using Zappa on the corresponding [Github](https://github.com/Miserlou/Zappa). Alternatively, this readme will demonstrate the required method.

First, navigate to the directory where the lambda_function.py file is stored. Open the file, and then modify the constants at the top of the file with the name and region of your S3 bucket. (The region you choose **MUST** match the true location of the S3 bucket, or the Alexa skill will fail.) For example:

```
userbucketname='s3-bucket-name-example'
userbucketregion='eu-west-1'
```
Save and exit the file. Then, create a Python Virtual Environment (in Terminal/CMD) in the directory you made (eg Alexa_Skill) by
```
virtualenv virtual-env
```
where 'virtual-env' is the name of the environment. The name of this can be user-specified, and can vary however needed.

Then, activate the virtual environment by (for Windows):
```
virtual-env\Scripts\activate.bat
```
or (for macOS):
```
source  virtual-env/bin/activate
```

If this is successful, the environment name (virtual-env) will appear on the left in the terminal window, to inform you that you are based within the virtual environment. Next, install the following modules:

```
pip install zappa
pip install boto3
pip install botocore
pip install flask
pip install flask_ask
```

(Note, installing boto3 is optional and should already function on AWS Lambda. However, it has been stated here for completeness.)

Now, to initialise Zappa, type:

```
zappa init
```

Zappa will ask you what production stage this program is in. You can call this anything, but for this readme, it will be called 'dev' or 'development'.

```
dev
```

Then you have to decide the name of your bucket. You can use the same bucket as the one created previously at the start of this readme. Enter that here.

```
s3-bucket-name-example
```

You will then be asked the name of your app's function. The default option given is required here.

```
lambda_function.app
```

Then you must decide if you wish to deploy the function globally. This choice is yours, but it is unlikely to be the case. For this readme, 'n' (no) will be chosen.

Then confirm the settings with 'y'.

Now navigate to the folder where 'lambda_function.py' is stored, and open 'zappa_settings.json'. It should look like the code below. Add in the lines with (ADD) attached.

```
{
    "dev": {
        "app_function": "lambda_function.app",
        "aws_region": "eu-west-1",
        "profile_name": "default",
        "s3_bucket": "s3-bucket-name-example",
        "keep_warm": false, (ADD THIS LINE)
        "timeout_seconds": 30, (ADD THIS LINE)
        "memory_size": 256, (ADD THIS LINE)
        "manage_roles": false, (ADD THIS LINE - BUT SET TO 'TRUE' IF USING 'AdministratorAccess' WHEN YOU CREATED THE USER ROLE.)
        "role_name":"alexa-skill-lambda-role-zappa-dev" (ADD THIS LINE)
    }
}
```

The additional lines perform the following:

* "keep_warm": Calls the Lambda function every 4 minutes. For development/testing, this isn't necessary, but can be enabled if needed.
* "timeout_seconds": How long the Lambda function is allowed to run before timing out. Usually this requires no more than 30 seconds, but the maximum limit is 5 minutes.
* "memory_size": Amount of RAM that is allocated to the function. 256MB is usually plenty, but can be increased if needed.
* "manage_roles": This prevents Zappa from trying to manage the IAM roles. **SET THIS TO 'TRUE' IF USING 'AdministratorAccess'.**
* "role_name": This can be whichever name you prefer, just make sure it is memorable.

## Deployment

Before deploying the Lambda function, you must first create the role which the function will use. There are two ways of doing this, depending on whether you are using AdministratorAccess on your user role.

### AWS Lambda - Without Administrator Access

If you are **NOT** using Administrator access on the user role you created previously, do the following:

* You will need to create the IAM role for Zappa to allow CloudFormation to take place. To start this, navigate to [AWS IAM Roles](https://console.aws.amazon.com/iam).
* Then navigate to 'roles'.
* Create a custom role.
* Choose AWS Service Role > AWS Lambda.
* Enable EC2FullAccess, SNSFullAccess, VPCFullAccess, S3FullAccess, CloudWatchFullAccess.
* Choose next, and give the role a name, and create the role.

* Click on  'Add inline policy' or 'Create role policy', at the bottom of the page.
* Choose 'Custom policy'.
* Paste in the contents of [this file.](https://github.com/capgemini-psdu/cloud-former-alexa/tree/master/cloud-former-lambda/Python/CloudFormation_Templates/ZappaPermissions1.json) These are the default permissions assigned by Zappa, but can be further restricted if needed.
* Repeat this process with a new custom policy, but this time paste the contents of [this file.](https://github.com/capgemini-psdu/cloud-former-alexa/tree/master/cloud-former-lambda/Python/CloudFormation_Templates/ZappaPermissions2.json) This enables the Lambda function to perform Cloud Formation.

Then to create the Lambda function:

* In terminal, still within the virtual environment described earlier, write:

```
zappa deploy dev
```
where 'dev' is the development stage you named when setting up Zappa. This will .zip your code and automatically upload and create your Lambda function for you. **This step will take a few minutes to complete.**

### AWS Lambda - With Administrator Access

Alternatively, if you **ARE** using Administrator access on the user role you created previously, do the following:

* Create the Lambda function using terminal, still within the virtual environment described earlier, write:

```
zappa deploy dev
```
where 'dev' is the development stage you named when setting up Zappa. This will .zip your code and automatically upload and create your Lambda function for you. **This step will take a few minutes to complete.**

* Then click on the [AWS IAM role](https://console.aws.amazon.com/iam) named 'alexa-skill-lambda-role-zappa-dev', which was created automatically by Zappa, but named by you in an earlier step.
* This role is already permitted to access S3, SNS, but additional policies will need to be manually granted. To do this, click on 'Attach Policy'.
* Add the following: EC2FullAccess, SNSFullAccess, VPCFullAccess, S3FullAccess, CloudWatchFullAccess. Then attach the policies.
* Next, click on 'Create Role Policy' or 'Add inline policy'.
* Navigate to policy generator.
* Choose AWS Service: AWS CloudFormation.
* Actions: All Actions.
* ARN Name. Type in the box: *
* Click on 'Add Statement'.
* Click on 'Next Step', and then 'Apply Policy'.

***Regardless of whether or not you used AdministratorAccess, the process is now identical from this point on:***

* When the process has completed, Zappa will provide you with a URL, and this will be used later when setting up the Alexa skill. It will be in the form:

```
https://XXXXXXXXXX.execute-api.XXXXXXXXXX.amazonaws.com/dev
```

Now navigate to the [Lambda](https://aws.amazon.com/lambda/) function.

* Ensure that your Lambda function is present. It will be in the form 'XXXXXXXXXX-dev', where 'dev' is the development stage set when setting up Zappa previously.
* If the function is not present, within Zappa, try redeploying the function with:

```
zappa update dev
```

This command will automatically update the Lambda function with any changes you make to the code. **You won't have to reconfigure the IAM's roles again.**

The Lambda function is now created and ready to use.

### Amazon Alexa Skill Setup

Within your Amazon Developer Portal, navigate to the [Alexa Skills Kit](https://developer.amazon.com/edw/home.html#/skills). Then:

* Add a new skill.
* Change the language to the relevant location. (Note: This skill was tested with English UK.) (This language CANNOT be changed at a later date.)
* Choose a name for the skill, and an invocation name. This is what users will say to initiate your skill.
* For the 'Intent Schema', copy and paste the text in the file /Python/CloudFormation_Templates/intentschema.json on [Github](https://github.com/capgemini-psdu/cloud-former-alexa/blob/master/cloud-former-lambda/Python/CloudFormation_Templates/intentschema.json).
* For the 'Sample Utterances', copy and paste the text in the file /Python/CloudFormation_Templates/sampleutterances.txt on [Github](https://github.com/capgemini-psdu/cloud-former-alexa/blob/master/cloud-former-lambda/Python/CloudFormation_Templates/sampleutterances.txt).
* In 'Custom Slot Types', create a slot called 'user', and enter the names of the users who you wish to have access to the Two-Factor Authentication codes. For example, you could use first names, such as 'John', or 'Bethany'.
* In 'Custom Slot Types', create a slot called 'topic', and copy the following:
```
launch
launching
launching a stack
launching a template
delete
deleting
terminating
terminating a stack
deleting a stack
list templates
listing templates
list
list stacks
listing stacks
two factor authentication
authentication
cost estimation
costs
reset
reset skill
```
* In configuration, choose HTTPS, and then select the geographical region of your Lambda function. In the text box, paste in the URL Zappa provided to you previously, in the form:

```
https://XXXXXXXXXX.execute-api.XXXXXXXXXX.amazonaws.com/dev
```

* For 'Certificate for EU Endpoint', choose 'My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority'.

The Alexa skill should now be ready for testing...

### Testing

In the testing panel, type:

"What is the date."

and the skill should respond with:

"date/month"

if the skill is functioning. If you receive an error, investigate the CloudWatch logs and diagnose accordingly.

**There is currently a bug in the Alexa simulator, which will cause this skill to fail. To counter this, write a request in written English, copy the corresponding JSON request and then re-send that, as a temporary workaround. This should be fixed shortly by Amazon directly.**

## Additional Requirements

You will require at least one CloudFormation template in your S3 bucket. An example of this can be found in /Python/CloudFormation_Templates/basic_ec2_instance.json on [Github](https://github.com/capgemini-psdu/cloud-former-alexa/blob/master/cloud-former-lambda/Python/CloudFormation_Templates/basic_ec2_instance.json). This will launch a Linux EC2 instance within the Free Tier of AWS.

Furthermore, you will need a file entitled 'contacts.csv', in the S3 bucket, in the format:

```
john,+44XXXXXXXXXX,0
bethany,+44XXXXXXXXXX,1
```

The number at the end is the authentication level. *(In-development.)*

* 0: Can create stacks only.
* 1: Can create and delete stacks.
* -1: Can neither create and delete stacks. This user has no authentication.

**It is vital that the names match those on the 'Custom Slot Types' specified when setting up the Alexa Skill.**

## Features and Functionality

The following assumes the invocation name is "Cloud".

### Initiating/Resetting the Skill

*	“Alexa, ask Cloud to…” for a specific question, or: “Alexa, launch Cloud” if you do not have a specific question.
(You can invoke this at any time if the skill pauses, and it will remember where you left off.)
*	To reset the conversation, say “Alexa, ask Cloud to reset skill.”

### Creating a Stack

(Alexa responses are in *italics*.)

(**The skill will NOT let you launch a stack without asking for available templates beforehand - to prevent you launching an incorrect and potentially expensive template.**)

*	“(Alexa, ask Cloud to) List available templates.” (**Must do this the first time you use the skill.**)
*	*“1. Basic instance. 2. Secondary instance.”*
*	“Launch stack” / “Start stack” / “Launch stack (number)”. (Specifying a number is optional.)
*	*“Which stack would you like to launch?”*
*	“One” / “Number one” / “Stack one”.
*	*“Please specify your name/username.”*
*	“Jordan” / “(username)”.
*	*“You have been sent a 2FA code to your phone. Say that code now.”*
*	“One two three four” / “(code)”. (There is a 60-second period to do this step.)
*	*“Stack (number) has been launched.”*

### Deleting a Stack

(Alexa responses are in *italics*.)

*	“(Alexa, ask Cloud to) List all stacks.”
*	*“Name: Cloud-Former-1. Status: CREATE COMPLETE. Name: Cloud-Former-2. Status: CREATE COMPLETE. ……”*
*	“Terminate stack” / “Delete stack” / “Delete stack (number)”. (Specifying a number is optional.)
*	*“Which stack would you like to delete?”*
*	“One” / “Number one” / “Stack one”.
*	*“Please specify your name/username.”*
*	“Jordan” / “(username)”.
*	*“You have been sent a 2FA code to your phone. Say that code now.”*
*	“One two three four” / “(code)”. (There is a 60-second period to do this step.)
*	*“Stack (number) has been deleted.”*

### Describing a Specific Stack

(Alexa responses are in *italics*.)

*	“Alexa, ask Cloud to list Stack Status (number).”
*	*“(Stack status and resources).” Or “That stack either does not exist, or has been deleted.”*

### Estimating Template Costs

(Alexa responses are in *italics*.)

*	“Alexa, ask Cloud how much stack (number) will cost.”
*	*“Please specify your name/username.”*
*	“Jordan” / “(username)”.
*	*“The cost URL has been sent to your mobile device.”*

This URL directs you to AWS, which will contain the estimated monthly cost of the instance to be launched.

## Adding Modifications to the Python Code

If you make any changes to lambda_function.py after the initial deployment with Zappa, updating the code is incredibly simple - and this is the key benefit to Zappa.

First, activate the virtual environment by (for Windows):
```
virtual-env\Scripts\activate.bat
```
or (for macOS):
```
source  virtual-env/bin/activate
```

Then, type
```
zappa update dev
```
and that's it. After Zappa has deployed your code, it should be ready to use immediately.

## Debugging

If you find the skill is not performing as expected, navigate to the Alexa Skill simulator within your [Alexa Skills Kit](https://developer.amazon.com/edw/home.html#/skills). This way, you will be able to see the response returned by the Lambda function. If the response returned is

```
There was an error calling the remote endpoint, which returned (error here).
```
or
```
The response is invalid.
```

then viewing the CloudWatch log for your Lambda function should help diagnose why the skill failed.

If any help is required, please contact the developer for this skill.

## Built With

* [Flask](http://flask.pocoo.org/) - A microframework for Python.
* [Flask-Ask](https://github.com/johnwheeler/flask-ask) - Flask extension used to simplify the Python code when building the Alexa skill.
* [Zappa](https://github.com/Miserlou/Zappa) - A Python 2.7 server-less deployment package.

## Authors

* **Jordan Lindsey** - [Github](https://github.com/jlindsey1)

See also the [main repository](https://github.com/capgemini-psdu/cloud-former-alexa) for all those who participated in this project.

## License

Flask is Copyright (c) 2015 by Armin Ronacher and contributors. Some rights reserved.

Flask-Ask is licensed under the Apache License 2.0.

Zappa is provided under the MIT License.

This project is Copyright (c) 2017 by Capgemini UK.

## Acknowledgments

* The main nodeJS version of this skill can be found [here](https://github.com/capgemini-psdu/cloud-former-alexa/tree/master/cloud-former-lambda/nodeJS).
