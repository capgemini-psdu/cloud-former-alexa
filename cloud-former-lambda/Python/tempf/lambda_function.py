##
#Alexa Python (2.7) Lambda Skill
#Author: Jordan Lindsey
#Email: jordan.lindsey@capgemini.com
#Version: 3.1
#Date: 13/07/2017
#Changelog: Added basic conversations.
#Features: Can give current date/time. Creation of AWS stack. Deletion of AWS stack. COnversations. SMS Verification.
#In-Production: Requesting template information. Advanced Conversations.
##

##Begin function

from __future__ import print_function

import json
import time
import boto3
import botocore.exceptions
from flask_ask import Ask, statement, question, session, convert_errors
from flask import Flask, render_template
from random import randint
import botocore

print('Loading function')

app = Flask(__name__)
ask = Ask(app, '/')

@ask.intent('AMAZON.StopIntent')
def stop():
    return statement("")

@ask.intent('AMAZON.CancelIntent')
def cancel():
    return statement("")

@ask.session_ended
def session_ended():
    return "{}", 200

@ask.intent("GetStatus")
def get_system_status():
    speech_output = "This Alexa skill is functioning normally."
    return statement(speech_output)

@ask.intent("GetDateIntent")
def get_current_date():
    speech_output = (time.strftime("%d/%m"))
    return statement(speech_output)

@ask.intent("GetTimeIntent")
def get_current_time():
    speech_output = (time.strftime("%H:%M"))
    return statement(speech_output)

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

@ask.intent("LaunchInstance")
def launch_instance(number,code):
    s3 = boto3.client('s3')
    open("/tmp/request.txt","w").close()
    file=open("/tmp/request.txt","w")
    file.write("LaunchInstance")
    file.close()
    with open('/tmp/request.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'request.txt')

    if number == None or number == "?":
        return question("Please specify which stack you would like to launch. This is in the form of a number, such as stack seven.").reprompt("Please specify which stack you would like to launch.")
    else:
        pass

    open("/tmp/number.txt","w").close()
    file=open("/tmp/number.txt","w")
    file.write(number)
    file.close()
    with open('/tmp/number.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'number.txt')

    if code == None:
        security_request()
        return question("You have been sent a code to your mobile device. Please state that code.").reprompt("Please state the code sent to your mobile device.")
    else:
        pass

    securitycheck=security_check(int(code))
    if securitycheck == True:
        response=stackformation(int(number))
        return statement(str(response))
    else:
        return statement("Incorrect code.")

@ask.intent("TerminateInstance")
def delete_instance(number,code):
    s3 = boto3.client('s3')
    open("/tmp/request.txt","w").close()
    file=open("/tmp/request.txt","w")
    file.write("DeleteInstance")
    file.close()
    with open('/tmp/request.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'request.txt')

    if number == None  or number == "?":
        return question("Please specify which stack you would like to delete. This is in the form of a number, such as stack seven.").reprompt("Please specify which stack you would like to delete.")
    else:
        pass

    open("/tmp/number.txt","w").close()
    file=open("/tmp/number.txt","w")
    file.write(number)
    file.close()
    with open('/tmp/number.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'number.txt')

    if code == None:
        security_request()
        return question("You have been sent a code to your mobile device. Please state that code.").reprompt("Please state the code sent to your mobile device.")
    else:
        pass

    securitycheck=security_check(int(code))
    if securitycheck == True:
        response=stackdeletion(int(number))
        return statement(str(response))
    else:
        return statement("Incorrect code.")

@ask.intent("UnknownRequest")
def unknown_request(number,code):
    s3 = boto3.resource('s3')
    BUCKET_NAME = 'jlindsey-bucket-eu-west-1'
    KEY = 'request.txt'
    try:
        s3.Bucket(BUCKET_NAME).download_file(KEY, '/tmp/request.txt')
    except botocore.exceptions.ClientError as e:
        print("An error has occured.")
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
            return statement("An error has occured. Please check the Alexa configuration.")
        else:
            raise
    file=open("/tmp/request.txt","r")
    request=file.read()

    BUCKET_NAME = 'jlindsey-bucket-eu-west-1'
    KEY2 = 'number.txt'
    try:
        s3.Bucket(BUCKET_NAME).download_file(KEY2, '/tmp/number.txt')
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
            return statement("An error has occured. Please check the Alexa configuration.")
        else:
            raise
    file2=open("/tmp/request.txt","r")
    requestnumber=file2.read()

    if code == None:
        security_request()
        return question("You have been sent a code to your mobile device. Please state that code.").reprompt("Please state the code sent to your mobile device.")
    else:
        pass

    if number == None:
        if requestnumber == None:
            return question("Please specify which stack you would like to delete. This is in the form of a number, such as stack seven.").reprompt("Please specify which stack you would like to delete.")
        else:
            # open("/tmp/number.txt","w").close() #clears textfile
            # file=open("/tmp/number.txt","w")
            # file.write(number)
            # file.close()
            # with open('/tmp/number.txt', 'rb') as data:
            #     s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'number.txt')
            number=requestnumber
    else:
        pass

    if request == "LaunchInstance":
        securitycheck=security_check(int(code))
        if securitycheck == True:
            response=stackformation(number)
            return statement(str(response))
        else:
            return statement("Incorrect code.")
    elif request == "DeleteInstance":
        securitycheck=security_check(int(code))
        if securitycheck == True:
            response=stackdeletion(number)
            return statement(str(response))
        else:
            return statement("Incorrect code.")
    else:
        return statement("An error has occured. Please check the Alexa configuration.")

def stackformation(number):
    client = boto3.client('cloudformation')
    try:
        response = client.create_stack(
            StackName='Cloud-Former',
            TemplateURL='https://s3-eu-west-1.amazonaws.com/jlindsey-bucket-eu-west-1/basic_ec2_instance.json',
            TimeoutInMinutes=2,
            OnFailure='ROLLBACK',
            ClientRequestToken='tokenrequest1'
        )
        speech_output = "Number test launched."#.format(number)
        print ("Success.")
    except Exception as e:
        print('Stack formation failed.')
        speech_output = "There has been a problem. The instance was not launched successfully."
    return speech_output

def stackdeletion(number):
    client = boto3.client('cloudformation')
    try:
        response = client.delete_stack(
            StackName='Cloud-Former',
            ClientRequestToken='tokenrequest2'
        )
        speech_output = "Number test deleted."
    except Exception as e:
        print('Stack deletion failed.')
        speech_output = "There has been a problem. The instance was not deleted successfully."
    return speech_output

def security_request():
    sns = boto3.client('sns')
    tfacode=str(random_with_N_digits(4))
    open("/tmp/securitycode.txt","w").close()
    file=open("/tmp/securitycode.txt","w")
    file.write(tfacode)
    file.close()
    s3 = boto3.client('s3')
    with open('/tmp/securitycode.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'securitycode.txt')
    number = "+13078000356" #https://smsreceivefree.com/info/13078000356/ for debugging
    sns.publish(PhoneNumber = number, Message=str(tfacode) )
    return question("A security code has been sent to your phone. Please state your intent, followed by that code.").reprompt("Please state your intent, followed by that code.")

def security_check(code):
    print("Checking...")
    s3 = boto3.resource('s3')
    BUCKET_NAME = 'jlindsey-bucket-eu-west-1'
    KEY = 'securitycode.txt'
    try:
        s3.Bucket(BUCKET_NAME).download_file(KEY, '/tmp/securitycode.txt')
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise

    file=open("/tmp/securitycode.txt","r")
    tfacode=file.read()

    if int(tfacode)==int(code):
        security=True
    else:
        security=False

    if security == True:
        return True
    else:
        return False

@ask.intent("RequestInstance")
def request_list():
    speech_output = "Function not yet completed."
    return statement(speech_output)

###
