##
#Alexa Python (2.7) Lambda Skill
#Author: Jordan Lindsey
#Email: jordan.lindsey@capgemini.com
#Version: 3.4
#Date: 18/07/2017
#Changelog: Added basic conversations. Added 2FA timeout. Multi-user verification. Requesting available stacks.
#Features: Can give current date/time. Creation of AWS stack. Deletion of AWS stack. Conversations. SMS Verification. Dynamic Stack Formation.
#In-Production: Listing current status of deployed stacks.
##

##Begin function

from __future__ import print_function

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

app = Flask(__name__)
ask = Ask(app, '/')

@ask.launch
def launched():
    return question('Welcome to Cloud Former')

@ask.intent('AMAZON.StopIntent')
def stop():
    return statement("")

@ask.intent('AMAZON.CancelIntent')
def cancel():
    return statement("")

@ask.session_ended
def session_ended():
    return "{}", 200

@ask.intent("ResetSkill")
def reset_skill():
    s3 = boto3.client('s3')
    open("/tmp/blank.txt","w").close()
    with open('/tmp/blank.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'availabletemplates.txt')
    with open('/tmp/blank.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'number.txt')
    with open('/tmp/blank.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'request.txt')
    with open('/tmp/blank.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'securitycode.txt')
    with open('/tmp/blank.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'unknown.txt')
    with open('/tmp/blank.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'user.txt')
    speech_output = "Skill reset."
    return statement(speech_output)

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
def launch_instance(number,code,user):
    s3 = boto3.client('s3')
    open("/tmp/request.txt","w").close()
    file=open("/tmp/request.txt","w")
    file.write("LaunchInstance")
    file.close()
    with open('/tmp/request.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'request.txt')

    if number == None or number == "?":
        open("/tmp/unknown.txt","w").close()
        file=open("/tmp/unknown.txt","w")
        file.write("numberrequest")
        file.close()
        with open('/tmp/unknown.txt', 'rb') as data:
            s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'unknown.txt')
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
        if user == None:
            open("/tmp/unknown.txt","w").close()
            file=open("/tmp/unknown.txt","w")
            file.write("userrequest")
            file.close()
            with open('/tmp/unknown.txt', 'rb') as data:
                s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'unknown.txt')
            return question("Which user are you?")
        else:
            requestcheck=security_request(user)
            if requestcheck == False:
                return question("User not recognised, please suggest a different user.").reprompt("Please suggest a different user.")
            else:
                pass
            open("/tmp/unknown.txt","w").close()
            file=open("/tmp/unknown.txt","w")
            file.write("coderequest")
            file.close()
            with open('/tmp/unknown.txt', 'rb') as data:
                s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'unknown.txt')
            return question("You have been sent a code to your mobile device. Please state that code.").reprompt("Please state the code sent to your mobile device.")
    else:
        pass

    securitycheck=security_check(int(code))
    if securitycheck == True:
        response=stackformation(int(number))
        return statement(str(response))
    else:
        return question("Incorrect code.")

@ask.intent("TerminateInstance")
def delete_instance(number,code,user):
    s3 = boto3.client('s3')
    open("/tmp/request.txt","w").close()
    file=open("/tmp/request.txt","w")
    file.write("DeleteInstance")
    file.close()
    with open('/tmp/request.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'request.txt')

    if number == None  or number == "?":
        open("/tmp/unknown.txt","w").close()
        file=open("/tmp/unknown.txt","w")
        file.write("numberrequest")
        file.close()
        with open('/tmp/unknown.txt', 'rb') as data:
            s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'unknown.txt')
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
        if user == None:
            open("/tmp/unknown.txt","w").close()
            file=open("/tmp/unknown.txt","w")
            file.write("userrequest")
            file.close()
            with open('/tmp/unknown.txt', 'rb') as data:
                s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'unknown.txt')
            return question("Which user are you?")
        else:
            open("/tmp/user.txt","w").close()
            file=open("/tmp/user.txt","w")
            file.write(user)
            file.close()
            with open('/tmp/user.txt', 'rb') as data:
                s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'user.txt')
            requestcheck=security_request(user)
            if requestcheck == False:
                return question("User not recognised, please suggest a different user.").reprompt("Please suggest a different user.")
            else:
                pass
            open("/tmp/unknown.txt","w").close()
            file=open("/tmp/unknown.txt","w")
            file.write("coderequest")
            file.close()
            with open('/tmp/unknown.txt', 'rb') as data:
                s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'unknown.txt')
            return question("You have been sent a code to your mobile device. Please state that code.").reprompt("Please state the code sent to your mobile device.")
    else:
        pass

    securitycheck=security_check(int(code))
    if securitycheck == True:
        response=stackdeletion(int(number))
        return statement(str(response))
    else:
        return question("Incorrect code.")

@ask.intent("UnknownRequest")
def unknown_request(number,code,user):
    if number == None and code == None and user == None:
        return question("I'm sorry, I did not understand your request or statement. Please try again.")

    s3 = boto3.resource('s3')
    BUCKET_NAME = 'jlindsey-bucket-eu-west-1'
    KEY = 'request.txt'
    KEY2 = 'number.txt'
    KEY3 = 'unknown.txt'
    KEY4 = 'availabletemplates.txt'
    try:
        s3.Bucket(BUCKET_NAME).download_file(KEY, '/tmp/request.txt')
        s3.Bucket(BUCKET_NAME).download_file(KEY2, '/tmp/number.txt')
        s3.Bucket(BUCKET_NAME).download_file(KEY3, '/tmp/unknown.txt')
        s3.Bucket(BUCKET_NAME).download_file(KEY4, '/tmp/availabletemplates.txt')
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

    file4=open("/tmp/availabletemplates.txt","r")
    availabletemplates=file4.read()

    if availabletemplates == None or availabletemplates == "":
        return question("Please request which templates are available before proceeding. This is to prevent modifying the incorrect stack.")

    if number == None:
        number = code
    else:
        pass

    s3 = boto3.client('s3')
    if unknownrequest == "coderequest":
        code=int(number)
        number=None
    elif unknownrequest == "numberrequest":
        file=open("/tmp/number.txt","w")
        file.write(number)
        file.close()
        with open('/tmp/number.txt', 'rb') as data:
            s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'number.txt')
        number=int(number)
        code=None
    elif unknownrequest == "userrequest":
        code=None
        number=None
        open("/tmp/user.txt","w").close()
        file=open("/tmp/user.txt","w")
        file.write(user)
        file.close()
        with open('/tmp/user.txt', 'rb') as data:
            s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'user.txt')
    else:
        pass

    if number == None:
        if requestnumber == None:
            open("/tmp/unknown.txt","w").close()
            file=open("/tmp/unknown.txt","w")
            file.write("numberrequest")
            file.close()
            with open('/tmp/unknown.txt', 'rb') as data:
                s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'unknown.txt')
            return question("Please specify which stack you would like to delete. This is in the form of a number, such as stack seven.").reprompt("Please specify which stack you would like to delete.")
        else:
            number=requestnumber
    else:
        pass

    if code == None:
        if user == None:
            open("/tmp/unknown.txt","w").close()
            file=open("/tmp/unknown.txt","w")
            file.write("userrequest")
            file.close()
            with open('/tmp/unknown.txt', 'rb') as data:
                s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'unknown.txt')
            return question("Which user are you?")
        else:
            open("/tmp/user.txt","w").close()
            file=open("/tmp/user.txt","w")
            file.write(user)
            file.close()
            with open('/tmp/user.txt', 'rb') as data:
                s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'user.txt')
            requestcheck=security_request(user)
            if requestcheck == False:
                return question("User not recognised, please suggest a different user.").reprompt("Please suggest a different user.")
            else:
                pass
            open("/tmp/unknown.txt","w").close()
            file=open("/tmp/unknown.txt","w")
            file.write("coderequest")
            file.close()
            with open('/tmp/unknown.txt', 'rb') as data:
                s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'unknown.txt')
            return question("You have been sent a code to your mobile device. Please state that code.").reprompt("Please state the code sent to your mobile device.")
    else:
        pass

    if request == "LaunchInstance":
        securitycheck=security_check(int(code))
        if securitycheck == True:
            response=stackformation(number)
            return statement(str(response))
        else:
            return question("Incorrect code.")
    elif request == "DeleteInstance":
        securitycheck=security_check(int(code))
        if securitycheck == True:
            response=stackdeletion(number)
            return statement(str(response))
        else:
            return question("Incorrect code.")
    else:
        return statement("An error has occured. Please check the Alexa configuration.")

def stackformation(number):
    client = boto3.client('cloudformation')
    s3 = boto3.resource('s3')
    BUCKET_NAME = 'jlindsey-bucket-eu-west-1'
    KEY = 'availabletemplates.txt'
    try:
        s3.Bucket(BUCKET_NAME).download_file(KEY, '/tmp/availabletemplates.txt')
    except botocore.exceptions.ClientError as e:
        print("An error has occured.")
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
            return statement("An error has occured. Please check the Alexa configuration.")
        else:
            raise

    file=open("/tmp/availabletemplates.txt","r")
    liststring=file.read()
    liststring2=ast.literal_eval(liststring)
    if int(number)>len(liststring2) or number == None:
        speech_output = "The number you specified is invalid."
        return speech_output
    try:
        response = client.create_stack(
            StackName='Cloud-Former-'+str(number),
            TemplateURL='https://s3-eu-west-1.amazonaws.com/jlindsey-bucket-eu-west-1/'+str(liststring2[int(number)-1]),
            TimeoutInMinutes=5,
            OnFailure='ROLLBACK',
            ClientRequestToken='tokenrequest'+str(number)
        )
        speech_output = "Stack "+number+" has been launched."
        print ("Success.")
    except Exception as e:
        print('Stack formation failed.')
        speech_output = "There has been a problem. The instance was not launched successfully."
    return speech_output

def stackdeletion(number):
    client = boto3.client('cloudformation')
    s3 = boto3.resource('s3')
    BUCKET_NAME = 'jlindsey-bucket-eu-west-1'
    KEY = 'availabletemplates.txt'
    try:
        s3.Bucket(BUCKET_NAME).download_file(KEY, '/tmp/availabletemplates.txt')
    except botocore.exceptions.ClientError as e:
        print("An error has occured.")
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
            return statement("An error has occured. Please check the Alexa configuration.")
        else:
            raise

    file=open("/tmp/availabletemplates.txt","r")
    liststring=file.read()
    liststring2=ast.literal_eval(liststring)
    if int(number)>len(liststring2) or number == None:
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
        raise e
    return speech_output

def security_request(user):
    #return True #enable for debugging - warning: this disables all security!
    s3 = boto3.resource('s3')
    BUCKET_NAME = 'jlindsey-bucket-eu-west-1'
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
            print(user)
            print(row[0])
            compare1=str(user)
            compare2=str(row[0])
            if str.lower(compare1)==str.lower(compare2):
                contactnumber=row[1]
                print(contactnumber)
                found=True
                break

    if found == False:
        print("Error: User not found.")
        return False

    sns = boto3.client('sns')
    currenttime=time.time()
    tfacode=str(random_with_N_digits(4))
    open("/tmp/securitycode.txt","w").close()
    file=open("/tmp/securitycode.txt","w")
    file.write(tfacode+" "+str(currenttime))
    file.close()
    s3 = boto3.client('s3')
    with open('/tmp/securitycode.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'securitycode.txt')
    sns.publish(PhoneNumber = str(contactnumber), Message=str(tfacode) )
    return True

def security_check(code):
    #return True #enable for debugging - warning: this disables all security!
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
    text=file.read()
    words = text.split(" ")
    tfacode=words[0]
    currenttime=words[1]

    if time.time() > float(currenttime)+90:
        return False
    else:
        pass

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

@ask.intent("RequestInstance")
def request_list():
    speech_output = "Function not yet completed."
    return statement(speech_output)

@ask.intent("RequestInstance")
def list_stacks():
    s3 = boto3.resource('s3')
    BUCKET_NAME = s3.Bucket('jlindsey-bucket-eu-west-1')
    list1=[]
    list2=[]
    i=0
    for file in BUCKET_NAME.objects.all():
        filename=file.key
        words = filename.split(".")
        title=words[0]
        extension=words[1]
        if extension == "json":
            i+=1
            list1.append(str(i)+'. '+title.replace("_", " "))
            list2.append(file.key)

    s3 = boto3.client('s3')
    open("/tmp/availabletemplates.txt","w").close()
    file=open("/tmp/availabletemplates.txt","w")
    file.write(str(list2))
    file.close()
    with open('/tmp/availabletemplates.txt', 'rb') as data:
        s3.upload_fileobj(data, 'jlindsey-bucket-eu-west-1', 'availabletemplates.txt')

    speech_output = '. '.join(list1)

    #print(ast.literal_eval(str(list2)))
    return statement(speech_output)

#@ask.intent("StackStatus") #in-development
#def stack_status(name):

#@ask.intent("TemplateSummary") #in-development
#def template_summary(name):

###
