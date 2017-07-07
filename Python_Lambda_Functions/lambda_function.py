##
#Alexa Python (2.7) Lambda Skill
#Author: Jordan Lindsey
#Email: jordan.lindsey@capgemini.com
#Version: 2.3
#Date: 06/07/2017
#Features: Can give current date/time. Creation of AWS stack. Deletion of AWS stack.
#In-Production: Error handling.
#Completed: Migration from boto to boto3. Migration from us-east to eu-west. Deletion of AWS stack.
#Removed: Experimental weather API feature.
##

##Begin function

from __future__ import print_function

import json
import time
import boto3
import botocore.exceptions

print('Loading function')

def lambda_handler(event, context):
    if (event["session"]["application"]["applicationId"] !=
            "amzn1.ask.skill.13642b2c-127b-48a8-8ba7-3ee8222e45f8"):
        raise ValueError("Invalid Application ID")
    
    if event["session"]["new"]:
        on_session_started({"requestId": event["request"]["requestId"]}, event["session"])

    if event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    elif event["request"]["type"] == "IntentRequest":
        return on_intent(event["request"], event["session"])
    elif event["request"]["type"] == "SessionEndedRequest":
        return on_session_ended(event["request"], event["session"])
        
def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]

    if intent_name == "GetStatus":
        return get_system_status()
    elif intent_name == "GetDateIntent":
        return get_current_date()
    elif intent_name == "GetTimeIntent":
        return get_current_time()
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    elif intent_name == "LaunchInstance":
        return launch_instance()
    elif intent_name == "TerminateInstance":
        return terminate_instance()
    else:
        raise ValueError("Invalid intent")
        
################################################HELPERS
        
def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])
        
def on_session_ended(session_ended_request, session):
    print("Ending session.")
    
def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }
    
################################################ENDHELPERS
    
def handle_session_end_request():
    card_title = "Thank you"
    speech_output = "Thank you for using the cloud formation skill.  Goodbye!"
    should_end_session = True
    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))
    
def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Alexa cloud formation skill. " \
                    "You can ask me to create an instance, or " \
                    "to terminate it."
    reprompt_text = "Please ask me to create an instance, or " \
                    "to destroy it."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
def get_system_status():
    session_attributes = {}
    card_title = "System Status"
    reprompt_text = ""
    should_end_session = False

    speech_output = "This system is running normally."

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
def get_current_date():
    session_attributes = {}
    card_title = "Date"
    reprompt_text = ""
    should_end_session = False
    
    speech_output = (time.strftime("%d/%m"))
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
def get_current_time():
    session_attributes = {}
    card_title = "Time"
    reprompt_text = ""
    should_end_session = False
    
    speech_output = (time.strftime("%H:%M"))
    
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
def launch_instance():
    session_attributes = {}
    card_title = "EC2 Instance Launch"
    reprompt_text = ""
    should_end_session = False
    
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
    ##Currently adding error handling:
    #except botocore.exceptions.something as e:
    #    if e.message.startswith('something to identify the message')
    #        print('errormessage')
    #        return something
    #    elif e.message.something else:
    #        ...
    #    else:
    #        ...
    except Exception as e:
        print('Stack formation failed.')
        speech_output = "There has been a problem. The instance was not launched successfully."
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def terminate_instance():
    session_attributes = {}
    card_title = "EC2 Instance Termination"
    reprompt_text = ""
    should_end_session = False
    
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
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

##End function
