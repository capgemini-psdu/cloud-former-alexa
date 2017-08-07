##
#Alexa Python (2.7) Lambda Skill
#Author: Jordan Lindsey
#Email: jordan.lindsey@capgemini.com
#Version: 4.1
#Date: 07/08/2017
#Features: Can give current date/time. Creation of AWS stack. Deletion of AWS stack. Conversations. SMS Verification. Dynamic Stack Formation. Stack descriptions.
#https://github.com/capgemini-psdu/cloud-former-alexa
#This code is (C) Copyright 2017 by Capgemini UK.
##

##Begin function

from __future__ import print_function

##Imports the required modules for the function to run.
import json
import time
import boto3
import botocore
import botocore.exceptions
from flask_ask import Ask, statement, question, session, convert_errors
from flask import Flask, render_template
from random import randint
import csv
import ast

print('Loading function')

##User-specific constants. These need to be set before running the Alexa skill:
userbucketname='jlindsey-bucket-eu-west-1' #This setting MUST be specified!
userbucketregion='eu-west-1' #(Default = eu-west-1)
usertimeout=60 ##Modify this setting to change 2FA code timeout time (seconds). Shorter time = Increased security. (Default = 60)
usercodelength=4 ##Modify this setting to change 2FA code length. Larger code = Increased security. (Default = 4)
userrollbacktime=5 ##Modify this setting to determine the length of time a stack should be allowed to launch before timing out (minutes). (Default = 5)
##

##Define global variables:
s3 = boto3.resource('s3')
client = boto3.client('cloudformation')
sns = boto3.client('sns')
BUCKET_NAME = userbucketname
app = Flask(__name__)
ask = Ask(app, '/')
##

##This is the intent that runs if the Alexa skill is launched without any specific requests.
@ask.launch
def launched():
    return question('Welcome to Cloud Former. You can ask me to launch or terminate stacks, along with listing available stacks and templates. Ask me a question to get started, or for further assistance, ask for help, followed by the topic you require.')

@ask.intent("HelpIntent")
def help_intent(topic):
    if topic == "launch" or topic == "launching" or topic == "launching a stack" or topic == "launching a template":
        return question("To launch a stack, you must first request which templates are available in the S3 bucket. Then, ask me to launch a stack, followed by the corresponding template number. Note, this intent will require elevated priviledges ")
    elif topic == "delete" or topic == " deleting" or topic == "terminating" or topic == "terminating a stack" or topic == "deleting a stack":
        return question("To delete a stack, it is advised that you first request which stacks are available in Cloud Formation. Then, ask me to delete a stack, followed by the corresponding number. Note, this intent will require elevated priviledges ")
    elif topic == "list templates" or topic == " listing templates" or topic == "list":
        return question("Simply ask me to list available templates, and I will list all Cloud Formation templates in your S3 bucket. I will also list the resources that each template will use.")
    elif topic == "list stacks" or topic == "listing stacks":
        return question("If you ask me to list all stacks, I will read out each name, and their formation status. If you ask me about the status of a specific stack, I will read out the name, formation status, and resources used.")
    elif topic == "two factor authentication" or topic == "authentication":
        return question("If you wish to create or delete a stack, you will require elevated priviledges. This means that the process won't proceed until a code has been sent to your mobile device. If you need help adding a user to the list of available contacts, a guide is available on the Capgemini github.")
    elif topic == "cost estimation" or topic == "costs":
        return question("If you would like an estimate of the monthly cost of any given template, ask me for the cost, followed by the template number. You will then be sent a link to your mobile device, taking you to the Amazon page with the cost estimation available. ")
    elif topic == "reset" or topic == "reset skill":
        return question("As this skill remembers your conversation using S3 buckets, you can ask me to reset, which will delete the current conversation.")
    else:
        return question('Which task would you like help with? Please respond with the word, help, followed by a particular topic.').reprompt('If you are unsure, you can ask about launching or deleting stacks, requesting templates, listing stacks, or two-factor authentication.')

    #return question('This Python Alexa Skill uses S3 buckets to remember the conversation, so you have a choice. You can state an entire request, or part of a request, and I will complete the rest. For example, if you wish to launch a stack, you can either say Launch stack one as user john, or more simply, say Launch a stack, and I will ask for the rest. ')

@ask.intent('AMAZON.StopIntent')
def stop():
    return statement("")

@ask.intent('AMAZON.CancelIntent')
def cancel():
    return statement("")

@ask.session_ended
def session_ended():
    return "{}", 200

##This intent deletes any previous conversation, by clearing the text files stored in S3.
@ask.intent("ResetSkill")
def reset_skill():
    s3 = boto3.client('s3')
    open("/tmp/blank.txt","w").close()
    with open('/tmp/blank.txt', 'rb') as data:
        s3.upload_fileobj(data, userbucketname, 'availabletemplates.txt')
    with open('/tmp/blank.txt', 'rb') as data:
        s3.upload_fileobj(data, userbucketname, 'number.txt')
    with open('/tmp/blank.txt', 'rb') as data:
        s3.upload_fileobj(data, userbucketname, 'request.txt')
    with open('/tmp/blank.txt', 'rb') as data:
        s3.upload_fileobj(data, userbucketname, 'securitycode.txt')
    with open('/tmp/blank.txt', 'rb') as data:
        s3.upload_fileobj(data, userbucketname, 'unknown.txt')
    with open('/tmp/blank.txt', 'rb') as data:
        s3.upload_fileobj(data, userbucketname, 'user.txt')
    speech_output = "Skill reset."
    return statement(speech_output)

##Debug intent: used to test the skills functions and returns a valid response.
@ask.intent("GetDateIntent")
def get_current_date():
    speech_output = (time.strftime("%d/%m"))
    return statement(speech_output)

##Debug intent: used to test the skills functions and returns a valid response.
@ask.intent("GetTimeIntent")
def get_current_time():
    speech_output = (time.strftime("%H:%M"))
    return statement(speech_output)

##Used to create 'n' digit code for the 2FA verification.
def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

##Intent used to launch an instance.
##This skill will check if the user has requested available templates before proceeding, to ensure the user does not launch the wrong instance.
@ask.intent("LaunchInstance")
def launch_instance(number,code,user):
    downloadattempt = download_file("availabletemplates","availabletemplates")
    if downloadattempt == True:
        return statement("An error has occured. Please check the Alexa configuration.")

    file=open("/tmp/availabletemplates.txt","r")
    availabletemplates=file.read()

    if availabletemplates == None or availabletemplates == "":
        return question("Please request which templates are available before proceeding. This is to prevent lanching the incorrect stack.")

    write_upload_textfile("request","LaunchInstance")

    if number == None or number == "?":
        write_upload_textfile("unknown","numberrequest")
        return question("Please specify which stack you would like to launch. This is in the form of a number, such as stack two.").reprompt("Please specify which stack you would like to launch.")

    write_upload_textfile("number",number)

    if code == None:
        if user == None:
            write_upload_textfile("unknown","userrequest")
            return question("Which user are you?")
        else:
            requestcheck=security_request(user,0)
            if requestcheck == False:
                return question("The user is not recognised, or does not have the required permissions, please suggest a different user.").reprompt("Please suggest a different user.")

            write_upload_textfile("unknown","coderequest")
            return question("You have been sent a code to your mobile device. Please state that code.").reprompt("Please state the code sent to your mobile device.")

    securitycheck=security_check(int(code))
    if securitycheck == True:
        response=stackformation(int(number))
        return statement(str(response))
    else:
        return question("Incorrect code, please try again.").reprompt("Please state the code sent to your device.")

##Intent used to delete an instance.
##This intent is almost identical to the 'launch' intent, but calls the delete function at the end.
@ask.intent("TerminateInstance")
def delete_instance(number,code,user):
    write_upload_textfile("request","DeleteInstance")

    if number == None  or number == "?":
        write_upload_textfile("unknown","numberrequest")
        return question("Please specify which stack you would like to delete. This is in the form of a number, such as stack two.").reprompt("Please specify which stack you would like to delete.")

    write_upload_textfile("number",number)

    if code == None:
        if user == None:
            write_upload_textfile("unknown","userrequest")
            return question("Which user are you?")
        else:
            write_upload_textfile("user",user)
            requestcheck=security_request(user,1)
            if requestcheck == False:
                return question("The user is not recognised, or does not have the required permissions, please suggest a different user.").reprompt("Please suggest a different user.")

            write_upload_textfile("unknown","coderequest")
            return question("You have been sent a code to your mobile device. Please state that code.").reprompt("Please state the code sent to your mobile device.")

    securitycheck=security_check(int(code))
    if securitycheck == True:
        response=stackdeletion(int(number))
        return statement(str(response))
    else:
        return question("Incorrect code, please try again.").reprompt("Please state the code sent to your device.")

##This intent is a 'catch-all', which tries to interpret a response from the user if no request is given.
##For example, if a user says 'launch stack one', the 'launch' intent will run. When that intent requests a code
##from the user, the user might simply reply with 'one two three four'. In this case, the intent below is called,
##which will try to decide how to proceed using textfiles in the S3 bucket.
@ask.intent("UnknownRequest")
def unknown_request(number,code,user):
    if number == None and code == None and user == None:
        return question("I'm sorry, I did not understand your request or statement. Please try again.")

    KEY = 'request.txt'
    KEY2 = 'number.txt'
    KEY3 = 'unknown.txt'
    try:
        s3.Bucket(BUCKET_NAME).download_file(KEY, '/tmp/request.txt')
        s3.Bucket(BUCKET_NAME).download_file(KEY2, '/tmp/number.txt')
        s3.Bucket(BUCKET_NAME).download_file(KEY3, '/tmp/unknown.txt')
    except botocore.exceptions.ClientError as e:
        print("An error has occured.")
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
            return statement("An error has occured. Please check the Alexa configuration.")
        else:
            raise

    file=open("/tmp/request.txt","r")
    request=file.read()

    file2=open("/tmp/number.txt","r")
    requestnumber=file2.read()

    file3=open("/tmp/unknown.txt","r")
    unknownrequest=file3.read()

    if request == None or request == "" or request == "?":
        return question("Please make a request first.")

    if number == None:
        number = code

    if unknownrequest == "coderequest":
        code=int(number)
        number=None
    elif unknownrequest == "numberrequest":
        write_upload_textfile("number",number)
        number=int(number)
        code=None
    elif unknownrequest == "userrequest":
        code=None
        number=None
        write_upload_textfile("user",user)

    if number == None:
        if requestnumber == None:
            write_upload_textfile("unknown","numberrequest")
            return question("Please specify a stack or template. This is in the form of a number, such as stack two.").reprompt("Please specify a number.")
        else:
            number=requestnumber

    if request == "StatusRequest":
        response=stack_status(number)
        return statement(str(response))

    if request == "TemplateCost":
        if user == None:
            write_upload_textfile("unknown","userrequest")
            return question("Which user are you?")
        else:
            return statement(template_cost(number,user))

    if request == "LaunchInstance":
        level = 0
    elif request == "DeleteInstance":
        level = 1
    else:
        level = 2

    if code == None:
        if user == None:
            write_upload_textfile("unknown","userrequest")
            return question("Which user are you?")
        else:
            write_upload_textfile("user",user)
            requestcheck=security_request(user,level)
            if requestcheck == False:
                return question("The user is not recognised, or does not have the required permissions, please suggest a different user.").reprompt("Please suggest a different user.")

            write_upload_textfile("unknown","coderequest")
            return question("You have been sent a code to your mobile device. Please state that code.").reprompt("Please state the code sent to your mobile device.")

    if request == "LaunchInstance":
        securitycheck=security_check(int(code))
        if securitycheck == True:
            response=stackformation(number)
            return statement(str(response))
        else:
            return question("Incorrect code, please try again.").reprompt("Please state the code sent to your device.")
    elif request == "DeleteInstance":
        securitycheck=security_check(int(code))
        if securitycheck == True:
            response=stackdeletion(number)
            return statement(str(response))
        else:
            return question("Incorrect code, please try again.").reprompt("Please state the code sent to your device.")
    else:
        return statement("An error has occured. Please check the Alexa configuration.")

##Function used to launch a requested stack from a template in the S3 bucket.
def stackformation(number):
    downloadattempt = download_file("availabletemplates","availabletemplates")
    if downloadattempt == True:
        return statement("An error has occured. Please check the Alexa configuration.")

    file=open("/tmp/availabletemplates.txt","r")
    liststring=file.read()
    liststring2=ast.literal_eval(liststring)
    if int(number)>len(liststring2) or number == None:
        speech_output = "The number you specified is invalid."
        return speech_output
    try:
        response = client.create_stack(
            StackName='Cloud-Former-'+str(number),
            TemplateURL='https://s3-'+userbucketregion+'.amazonaws.com/'+userbucketname+'/'+str(liststring2[int(number)-1]),
            TimeoutInMinutes=userrollbacktime,
            OnFailure='ROLLBACK',
            ClientRequestToken='tokenrequest'+str(number)
        )
        speech_output = "Stack "+number+" has been launched."
        print ("Success.")
    except Exception as e:
        print('Stack formation failed.')
        speech_output = "There has been a problem. The instance was not launched successfully."
    return speech_output

##Function used to delete a requested stack from a template in the S3 bucket.
def stackdeletion(number):
    if number == None:
        speech_output = "The number you specified is invalid."
        return speech_output

    ##Update the following to add/remove options when listing available stacks on AWS:
    response = client.list_stacks(
        StackStatusFilter=[
            'CREATE_IN_PROGRESS','CREATE_FAILED','CREATE_COMPLETE','ROLLBACK_IN_PROGRESS','ROLLBACK_FAILED','ROLLBACK_COMPLETE','DELETE_IN_PROGRESS','DELETE_FAILED','UPDATE_IN_PROGRESS','UPDATE_COMPLETE_CLEANUP_IN_PROGRESS','UPDATE_COMPLETE','UPDATE_ROLLBACK_IN_PROGRESS','UPDATE_ROLLBACK_FAILED','UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS','UPDATE_ROLLBACK_COMPLETE','REVIEW_IN_PROGRESS'
        ]
    )
    numberofstacks=len(response['StackSummaries'])

    found=False
    for i in range(numberofstacks):
        Stackname=response['StackSummaries'][i-1]['StackName']
        if Stackname == 'Cloud-Former-'+str(number):
            found=True

    if found == False:
        speech_output = "The number you specified is invalid."
        return speech_output

    try:
        response = client.delete_stack(
            StackName='Cloud-Former-'+str(number),
            ClientRequestToken='tokenrequest0'+str(number)
        )
        speech_output = "Stack "+number+" has been deleted."
    except Exception as e:
        print('Stack deletion failed.')
        speech_output = "There has been a problem. The instance was not deleted successfully."
    return speech_output

##Function to request a code from the user, using contact details from contacts.csv in the S3 bucket.
def security_request(user,level):
    #return True #enable for debugging - warning: this disables all security!
    KEY = 'contacts.csv'
    try:
        s3.Bucket(BUCKET_NAME).download_file(KEY, '/tmp/contacts.csv')
    except botocore.exceptions.ClientError as e:
        print("An error has occured.")
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
            return statement("An error has occured. Please check the Alexa configuration.")
        else:
            raise

    authentication=False
    found=False
    with open('/tmp/contacts.csv') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            compare1=str(user)
            compare2=str(row[0])
            if str.lower(compare1)==str.lower(compare2):
                contactnumber=row[1]
                authentication=row[2]
                if int(authentication)==-1:
                    found=False
                    break
                elif int(authentication) >= int(level):
                    found=True
                    break
                else:
                    found=False
                    break


    if found == False:
        print("Error: User not found or not authenticated.")
        return False

    currenttime=time.time()
    tfacode=str(random_with_N_digits(usercodelength))
    write_upload_textfile("securitycode",tfacode+" "+str(currenttime))
    sns.publish(PhoneNumber = str(contactnumber), Message=str(tfacode) )
    return True

##Checks code supplied by the user with stored code in S3 bucket.
def security_check(code):
    #return True #enable for debugging - warning: this disables all security!
    print("Checking...")

    downloadattempt = download_file("securitycode","securitycode")
    if downloadattempt == True:
        return statement("An error has occured. Please check the Alexa configuration.")

    file=open("/tmp/securitycode.txt","r")
    text=file.read()
    words = text.split(" ")
    tfacode=words[0]
    currenttime=words[1]

    if time.time() > float(currenttime)+usertimeout:
        return False

    if int(tfacode)==int(code):
        security=True
    else:
        security=False

    if security == True:
        return True
    else:
        return False

##Lists available templates which can be launched.
@ask.intent("RequestInstance")
def list_stacks():
    BUCKET_NAME = s3.Bucket(userbucketname)
    list1=[]
    list2=[]
    i=0
    for file in BUCKET_NAME.objects.all():
        filename=file.key
        words = filename.split(".")
        title=words[0]
        extension=words[1]
        list3=""
        if extension == "json":
            i+=1
            response = client.get_template_summary(
                TemplateURL='https://s3-'+userbucketregion+'.amazonaws.com/'+userbucketname+'/'+str(file.key)
            )
            for j in range(len(response['ResourceTypes'])):
                resource=response['ResourceTypes'][j-1]
                list3=list3+resource.replace("::", " ")+", "
            list1.append(str(i)+'. '+title.replace("_", " ")+". This launches "+list3.replace("AWS", "")+". ")
            list2.append(file.key)

    write_upload_textfile("availabletemplates",str(list2))

    speech_output = '. '.join(list1)

    return question(speech_output)

##Lists specific stack resources, if already launched in AWS CloudFormation.
##This requires specifying the number of the given stack.
@ask.intent("StackStatus")
def stack_status_initial(number):
    write_upload_textfile("request","StatusRequest")

    if number == None or number == "?":
        write_upload_textfile("unknown","numberrequest")
        return question("Please specify a number with your request for stack status.")
    speech_output=stack_status(number)
    return statement(speech_output)

##This function is used with the above intent to fetch the resources of launched stacks in AWS.
def stack_status(number):
    try:
        response = client.describe_stack_resources(
            StackName='Cloud-Former-'+str(number),
        )
        speech_output="Name. "+response['StackResources'][0]['StackName'].replace("-", " ")+" . Resource. "+response['StackResources'][0]['ResourceType'].replace("::", " ")+" . Status. "+response['StackResources'][0]['ResourceStatus'].replace("_", " ")
    except Exception as e:
        speech_output="That stack either does not exist, or has been deleted."
        return speech_output
    return speech_output

##Gives a summary of all launched stacks in AWS CloudFormation.
@ask.intent("StackStatusAll")
def stack_status_all():
    try:
        response = client.list_stacks(
            StackStatusFilter=[
                'CREATE_IN_PROGRESS','CREATE_FAILED','CREATE_COMPLETE','ROLLBACK_IN_PROGRESS','ROLLBACK_FAILED','ROLLBACK_COMPLETE','DELETE_IN_PROGRESS','DELETE_FAILED','UPDATE_IN_PROGRESS','UPDATE_COMPLETE_CLEANUP_IN_PROGRESS','UPDATE_COMPLETE','UPDATE_ROLLBACK_IN_PROGRESS','UPDATE_ROLLBACK_FAILED','UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS','UPDATE_ROLLBACK_COMPLETE','REVIEW_IN_PROGRESS'
            ]
        )
        #'DELETE_COMPLETE' not included
        numberofstacks=len(response['StackSummaries'])
        speech_output=""
        for i in range(numberofstacks):
            speech_output=speech_output+"Name. "+response['StackSummaries'][i-1]['StackName'].replace("-", " ")+" . Status. "+response['StackSummaries'][i-1]['StackStatus'].replace("_", " ")+". "
    except Exception as e:
        speech_output="An error has occured. Please check the Alexa configuration."
    return question(speech_output)

#Gives an estimated monthly cost of a template, which is sent to the user's phone.
@ask.intent("TemplateCost") #in-development
def template_cost_initial(number, user):
    downloadattempt = download_file("availabletemplates","availabletemplates")
    if downloadattempt == True:
        return statement("An error has occured. Please check the Alexa configuration.")

    file=open("/tmp/availabletemplates.txt","r")
    availabletemplates=file.read()
    if availabletemplates == None or availabletemplates == "":
        return question("Please request which templates are available before proceeding. This is to prevent launching the incorrect stack.")

    write_upload_textfile("request","TemplateCost")

    if number == None or number == "?":
        write_upload_textfile("unknown","numberrequest")
        return question("Please specify which template you would like the cost for. This is in the form of a number, such as template two.").reprompt("Please specify a template.")
    else:
        write_upload_textfile("number",number)

    if user == None:
        write_upload_textfile("unknown","userrequest")
        return question("Which user are you?")
    else:
        return statement(template_cost(number,user))

def template_cost(number, user):
    downloadattempt = download_file("availabletemplates","availabletemplates")
    if downloadattempt == True:
        return statement("An error has occured. Please check the Alexa configuration.")

    file=open("/tmp/availabletemplates.txt","r")
    liststring=file.read()
    liststring2=ast.literal_eval(liststring)
    if int(number)>len(liststring2) or number == None:
        speech_output = "The number you specified is invalid."
        return speech_output

    KEY = 'contacts.csv'
    try:
        s3.Bucket(BUCKET_NAME).download_file(KEY, '/tmp/contacts.csv')
    except botocore.exceptions.ClientError as e:
        print("An error has occured.")
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
            return statement("An error has occured. Please check the Alexa configuration.")
        else:
            raise

    found=False
    with open('/tmp/contacts.csv') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            compare1=str(user)
            compare2=str(row[0])
            if str.lower(compare1)==str.lower(compare2):
                contactnumber=row[1]
                found=True
                break

    if found == False:
        print("Error: User not found.")
        return "User not found."

    try:
        response = client.estimate_template_cost(
        TemplateURL='https://s3-'+userbucketregion+'.amazonaws.com/'+userbucketname+'/'+str(liststring2[int(number)-1])
        )
        sns_output=str(response['Url'])
        sns.publish(PhoneNumber = str(contactnumber), Message=sns_output )
        speech_output="The cost URL has been sent to your mobile device."
    except Exception as e:
        print('Cost request failed.')
        speech_output = "There has been a problem. The message was not sent successfully."
    return speech_output

#Function used to upload a textfile to the user specified S3 bucket.
def write_upload_textfile(filename,data):
    open("/tmp/"+str(filename)+".txt","w").close()
    file=open("/tmp/"+str(filename)+".txt","w")
    file.write(str(data))
    file.close()
    s3write = boto3.client('s3')
    with open("/tmp/"+str(filename)+".txt", 'rb') as data:
        s3write.upload_fileobj(data, userbucketname, str(filename)+'.txt')

#Function used to download a textfile from the user specified S3 bucket.
def download_file(filename,key):
    KEY = key+'.txt'
    try:
        s3.Bucket(BUCKET_NAME).download_file(KEY, "/tmp/"+str(filename)+".txt")
    except botocore.exceptions.ClientError as e:
        print("An error has occured.")
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
            return True
        else:
            raise

###
