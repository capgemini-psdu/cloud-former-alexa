##
#Alexa Python (2.7) Lambda Skill
#Author: Jordan Lindsey
#Email: jordan.lindsey@capgemini.com
#Version: 3.0
#Date: 10/07/2017
#Changelog: Updated to work with ask_flask
#Features: Can give current date/time. Creation of AWS stack. Deletion of AWS stack.
#In-Production: SMS verification. Requesting template information. Conversations.
#Completed: Migration from boto to boto3. Migration from us-east to eu-west. Deletion of AWS stack. Error handling.
##

##Begin function

from __future__ import print_function

import json
import time
import boto3
import botocore.exceptions
from flask_ask import Ask, statement, question, session
from flask import Flask, render_template

print('Loading function')

app = Flask(__name__)
ask = Ask(app, '/')

def security_request():
    sns = boto3.client('sns')
    number = "+44inputnumberhere" 
    #sns.publish(PhoneNumber = number, Message='example text message' )
    return True

@ask.intent('AMAZON.StopIntent')
def stop():
    return statement("Goodbye")


@ask.intent('AMAZON.CancelIntent')
def cancel():
    return statement("Goodbye")


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

@ask.intent("LaunchInstance")
def launch_instance():
    client = boto3.client('cloudformation')
    try:
        response = client.create_stack(
            StackName='Cloud-Former',
            TemplateURL='https://s3-eu-west-1.amazonaws.com/jlindsey-bucket-eu-west-1/basic_ec2_instance.json',
            TimeoutInMinutes=2,
            OnFailure='ROLLBACK',
            ClientRequestToken='tokenrequest1'
        )
        speech_output = "Success."
    except Exception as e:
        print('Stack formation failed.')
        speech_output = "There has been a problem. The instance was not launched successfully."
    return statement(speech_output)

@ask.intent("TerminateInstance")
def launch_instance():
    client = boto3.client('cloudformation')
    try:
        response = client.delete_stack(
            StackName='Cloud-Former',
            ClientRequestToken='tokenrequest2'
        )
        speech_output = "Success."
    except Exception as e:
        print('Stack deletion failed.')
        speech_output = "There has been a problem. The instance was not deleted successfully."
    return statement(speech_output)

@ask.intent("RequestInstance")
def launch_instance():
    speech_output = "TBC"
    return statement(speech_output)
