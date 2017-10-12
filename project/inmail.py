#parse inbound email - inmail.py

from flask import Flask, request, url_for
import simplejson
from project import app
from project import urlHome
import requests
import json
from datetime import datetime
from datetime import date,timedelta
import pandas as pd
import csv
import os
from pandastable import weeklystatus
import MySQLdb
from MySQLdb import escape_string as thwart
from dbconnect import connection
import gc
from box import sync, unsync

from flask_mail import Mail, Message
mail = Mail(app)

@app.route("/incoming", methods=["GET","POST"])
def email():
    try:
        if request.method == "POST":
            envelope = simplejson.loads(request.form.get('envelope'))
            to_address = envelope['to'][0]
            from_address = envelope['from']
            text = request.form.get('text')
            html = request.form.get('html')
            subject = str(request.form.get('subject'))
            num_attachments = int(request.form.get('attachments', 0))
            attachments = []
            if num_attachments <> -1:
                for num in range(1, (num_attachments + 1)):
                    attachment = request.files.get(('attachment%d' % num))
                    attachments.append(attachment.read())
            if subject.find('A New Design Case Has Been Created') <> -1:
                url = 'http://adhome.levelsolar.com/emailNewDesign?api_key=Jo3y1SAW3S0M3'
                payload = {'emailBody' : text, 'emailSubject' : subject}
                response = requests.post(url, data=payload)

            elif subject.find(' - Pre BMC Issue Resolved') <> -1:
                url = 'http://adhome.levelsolar.com/emailIssueResolved?api_key=Jo3y1SAW3S0M3'
                payload = {'emailBody' : text, 'emailSubject' : subject}
                response = requests.post(url, data=payload)

            elif subject.find(' - Design Change Requested!')<> -1:
                url = 'http://adhome.levelsolar.com/emailChangeRequest?api_key=Jo3y1SAW3S0M3'
                payload = {'emailBody' : text, 'emailSubject' : subject}
                response = requests.post(url, data=payload)

            elif subject.find(' - CAD Outcome') <> -1:
                url = 'http://adhome.levelsolar.com/emailCADOutcome?api_key=Jo3y1SAW3S0M3'
                payload = {'emailBody' : text, 'emailSubject' : subject}
                response = requests.post(url, data=payload)

            else:
                msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
                msg.body = str(text)
                mail.send(msg)
            return "OK"
        else: # request.method == "GET"
            return "incoming"
    except Exception as e:
        msg = Message('Inbound email', sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])
        msg.body = str(e) +text
        mail.send(msg)
        return str(e)