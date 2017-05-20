import logging
import json
import sys
import socket, re, os, sys, inspect
from flask import Flask, render_template, redirect, url_for
from flask import request as request_flask
from flask import session as session_flask
from flask_ask import Ask, request, session, question, statement, dialog
import datetime
import copy, random
import paho.mqtt.client as paho


external_tokens={}

#broker = 'broker.hivemq.com'
#broker = '127.0.0.1'
broker = '13.126.2.187'
account_no = "4444777755551369"
customer_id = "33336369"
user_topic = "/text/" + customer_id + "/messages/user"
alexa_topic = "/text/" + customer_id + "/messages/alexa"
result_topic = "/text/" + customer_id + "/messages/result"

questions = [["Who's your favourite actor?","Angelina Jolie"],
             ["What's your favourite sport?", 'basketball'],
             ["What's your favourite animal?","lion"],
             ["What's your favourite color?","black"]]

payee_details = {
                'sam' : '4444777755551370',
                'nick' : '4444777755551371',
                'john' : '4444777755551372',
                }
vpa_details = {
                'sam' : 'sam@icicibank',
                'nick' : 'nick@icicibank',
                'john' : 'john@icicibank',
                }

vas = {
    'wallet' : '', 
    'prepaid' : 'caller tune', 
    'postpaid' : '',
    'dth' : 'free HD trial pack',
}


app = Flask(__name__)
ask = Ask(app, "/")
app.secret_key = "test_secret_key"
logging.getLogger('flask_ask').setLevel(logging.DEBUG)

def on_connect(client, userdata, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.


def on_publish(client, userdata, mid):
    print("published : "+str(mid))

client = paho.Client(clean_session=True)
client.on_publish = on_publish
client.on_connect = on_connect

class Payload:
    slots = ""
    intent = ""
    text = ""
    customer_id = ""
    alexaData = ""
    def __init__(self, customer_id):
        self.customer_id = customer_id
    def setSlots(self,slots):
        self.slots = slots
    def setIntent(self,intent):
        self.intent = intent
    def setText(self,text):
        self.text = text
    def setAlexaData(self,alexaData):
        self.alexaData = alexaData


@ask.launch
def launch():
    speech_text = render_template('welcome')
    return question(speech_text).reprompt(speech_text).simple_card('GringottsResponse', speech_text)

@ask.intent('CheckBalanceIntent',
            mapping={'product_slot':'PRODUCT_SLOT'})
def getAccountBalance(product_slot):
    mqttPayload = Payload(customer_id)
    mqttPayload.setIntent('CheckBalanceIntent')
    client.publish(user_topic, json.dumps(mqttPayload.__dict__), qos=0)
    valid_products = ['wallet', 'prepaid']
    if product_slot is not None:
        if product_slot in valid_products:
            speech_text = render_template('balance_response', balance=685, product_slot=product_slot)
            mqttPayload.setText(speech_text)
        else:
            speech_text = render_template('invalid_product')
            mqttPayload.setText(speech_text)
        client.publish(alexa_topic, json.dumps(mqttPayload.__dict__), qos=0)
        return statement(speech_text).simple_card('AirCareResponse', speech_text)
    else:
        return dialog().dialog_directive()


@ask.intent('ActiveVASIntent',
            mapping={'product_slot':'PRODUCT_SLOT'})
def getAccountBalance(product_slot):
    mqttPayload = Payload(customer_id)
    mqttPayload.setIntent('ActiveVASIntent')
    client.publish(user_topic, json.dumps(mqttPayload.__dict__), qos=0)
    valid_products = ['wallet', 'prepaid', 'postpaid', 'dth']
    
    if product_slot is not None:
        product_slot = product_slot.lower()
        if product_slot in valid_products:
            if vas[product_slot]!='':
                speech_text = render_template('vas_response', content=vas[product_slot], product_slot=product_slot)
                mqttPayload.setText(speech_text)
            else :
                speech_text = render_template('vas_no_response', product_slot=product_slot)
                mqttPayload.setText(speech_text)
        else:
            speech_text = render_template('invalid_product')
            mqttPayload.setText(speech_text)
        client.publish(alexa_topic, json.dumps(mqttPayload.__dict__), qos=0)
        return statement(speech_text).simple_card('AirCareResponse', speech_text)
    else:
        return dialog().dialog_directive()


@ask.intent('VASActionIntent',
            mapping={'product_slot':'PRODUCT_SLOT', 'vas_action_slot' : 'VAS_ACTION_SLOT', 'vas_slot' : 'VAS_SLOT'})
def getAccountBalance(product_slot, vas_action_slot, vas_slot):
    mqttPayload = Payload(customer_id)
    mqttPayload.setIntent('ActiveVASIntent')
    client.publish(user_topic, json.dumps(mqttPayload.__dict__), qos=0)
    valid_products = ['wallet', 'prepaid', 'postpaid', 'dth']
    
    if product_slot is not None:
        product_slot = product_slot.lower()
        if product_slot in valid_products:
            if vas_action_slot == 'activate':
                vas[product_slot] = vas_slot
                speech_text = render_template('vas_activate', vas_slot=vas_slot, product_slot=product_slot)
                mqttPayload.setText(speech_text)
            elif vas_action_slot == 'deactivate':
                vas[product_slot] = ''
                speech_text = render_template('vas_deactivate', vas_slot=vas_slot, product_slot=product_slot)
                mqttPayload.setText(speech_text)
        else:
            speech_text = render_template('invalid_product')
            mqttPayload.setText(speech_text)
        client.publish(alexa_topic, json.dumps(mqttPayload.__dict__), qos=0)
        return statement(speech_text).simple_card('AirCareResponse', speech_text)
    else:
        return dialog().dialog_directive()





@ask.session_ended
def session_ended():
    return "", 200


@ask.intent('AMAZON.HelpIntent')
def help():
    help_text = render_template('help')
    help_reprompt = render_template('help_reprompt')
    return question(help_text).reprompt(help_reprompt)


@ask.intent('AMAZON.StopIntent')
def stop():
    bye_text = render_template('bye')
    return statement(bye_text)


@ask.intent('AMAZON.CancelIntent')
def cancel():
    bye_text = render_template('bye')
    return statement(bye_text)



if __name__ == '__main__':
    #print rest.getAccountSummary(token, 33336369, account_no)
    #print rest.listPayee(token, 33336369)
    #print rest.createVPA(token, account_no, "soumyadeep@icicibank")
    try:
        client.connect(broker, 1883, 60)
        client.loop_start()
        print user_topic
        print alexa_topic
    except (KeyboardInterrupt, SystemExit):
        client.loop_stop()
        client.disconnect()

    app.run(threaded=True,debug=True)
