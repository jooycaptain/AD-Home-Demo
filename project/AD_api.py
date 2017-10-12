from flask import Flask, render_template, session, url_for, redirect, flash, request, jsonify
import requests
import os
import json
import urllib2
import MySQLdb
from MySQLdb import escape_string as thwart
from dbconnect import connection
import gc
from project import app
from project import urlHome
import numpy as np

from flask_mail import Mail, Message
mail = Mail(app)

from flask.ext.login import LoginManager
from flask.ext.login import login_user , logout_user , current_user , login_required
from .decorators import require_apikey


from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

import SFcase
from SFcase import issueBitoStr

stat = {'0':'New',
        '1':'Surveyed',
        '1.5': 'Pending',
        '2': 'Approved',
        '3': 'Change design*',
        '4': 'Redesign*',
        '5': 'Draft',
        '6': 'Need',
        '7': 'Need',
        '8': 'Bad'}

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

@app.route("/prebmc/", methods=["GET"])
@require_apikey
@crossdomain(origin='*')
def prebmc_display():
    try:
        c,conn = connection()
        x = c.execute("SELECT * FROM cases")
        CASE_DICT=[]
        for row in c:
            if float(row[3]) > 1.5:
                try:
                    int(row[14])
                    issueList = issueBitoStr(row[14])
                    issueStr = np.array(issueList.split('; ')).tolist()
                    CASE_DICT.append({'Case#': row[0], 'PreBMC': issueStr, 'Status': stat[row[3]]})
                except:
                    CASE_DICT.append({'Case#': row[0], 'PreBMC': None, 'Status': stat[row[3]]})
        return json.dumps(CASE_DICT)


    except Exception as e:
        return str(e) + ' Bad request!'

ADDesigner = {'Lennon':'Lennon Wu',
              'Alessandro':'Alessandro Marra',
              'Joey':'Joey Jiao',
              'Tina':'Tina Gong',
              'Yao':'Yao Wang',
              'Katerina':'Katerina Liakos',
              'Stephanie':'Stephanie Ma',
              'Victor':'Victor Borisov',
              'Rebecca':'Rebecca Handa',
              'Silun':'Silun Zhang',
              'Michael':'Michael Tarzian',
              'Justin':'Justin Gottlieb',
              'Ren':'Ren Yu',
              'Meredith':'Meredith Johansen',
              'Lukas':'Lukas Fuchshofen'}

designIssue = ['Missing Meter Location',
               'Detached Garage',
               'Obstruction Removal Needed',
               '3 Layers of Shingles',
               'Shingles/Roof to be Fixed',
               'Tree Removal Needed',
               'Two Systems Proposed',
               'Other','Sealed Rafters',
               'Missing Sales Pictures',
               'Missing Utility Number',
               'Missing Electricity Consumption',
               'Energy Audit',
               'Rusted Meter',
               'Breaker Issue']

@app.route("/master_info/<sfdc>", methods=["GET", "POST"])
@require_apikey
def master_info(sfdc):
    try:
        c,conn = connection()
        x = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                    [thwart(sfdc)])
        if int(x) == 0:
            return "No such case in the system."
        row = c.fetchone()
        info = str(row[8])
        amp = ''
        rsi = ''
        rsp = ''
        au = ''
        if info.find('AMP:') != -1:
            amp = info[info.find('AMP:')+4:info.find(';',info.find('AMP:'))]
        if info.find('RSI:') != -1:
            rsi = info[info.find('RSI:')+4:info.find(';',info.find('RSI:'))]
        if info.find('RSP:') != -1:
            rsp = info[info.find('RSP:')+4:info.find(';',info.find('RSP:'))]
        if info.find('AUS:') != -1:
            au = info[info.find('AUS:')+4:info.find(';',info.find('AUS:'))]
        designer = ADDesigner[str(row[1])]
        issueBi = row[14]
        UTT = ''
        ck = ['0','0','0','0']
        if info.find('UTT:') != -1:
            UTT = info[info.find('UTT:')+4:info.find(';',info.find('UTT:'))]
            UTT = UTT.replace("-","")
        if rsp.find('eal') <> -1:
            ck[0] = '1'
        if rsp == '' or rsi == '' or amp == '':
            ck[1] = '1'
        if UTT == 'Missing':
            ck[2] = '1'
        if au == '':
            ck[3] = '1'
        try:
            issuesFromBi = issueBitoStr(row[14][:8]+ck[0]+ck[1]+ck[2]+ck[3]+row[14][12:])
        except:
            issuesFromBi = ''        

        info = {'SF###': sfdc,
                'AMP': str(amp),
                'RSI': str(rsi),
                'RSP': str(rsp),
                'AUS': str(au),
                'NOT': str(row[7]),
                'DES': designer,
                'STS': issuesFromBi}   
        return jsonify(info)
    except Exception as e:
        return str(e) + ' Bad request!'

        
@app.route("/shading/", methods=["GET"])
@require_apikey
@crossdomain(origin='*')
def shading_list():
    try:
        c,conn = connection()
        data = c.execute("SELECT * FROM cases ORDER BY status, aptDate, PRB")
        CASE_DICT=[]
        for row in c:
            if row[3] == '1':
                if row[14] == None or row[14] == 'None':
                    CASE_DICT.append({'Case#': row[0], 'Designer': str(row[1]), 'Shading': str(row[14])})        
        return json.dumps(CASE_DICT)
    except Exception as e:
        return str(e) + ' Bad request!'

