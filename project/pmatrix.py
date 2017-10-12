#import pandas as pd
import requests
from flask import Flask, render_template, session, url_for, redirect, flash, request, jsonify
import MySQLdb
from MySQLdb import escape_string as thwart
from dbconnect import connection
from project import app
from project import urlHome
import gc
import random
import time
from datetime import date,timedelta, datetime
import os
import numpy as np
import math
from pyexcel_xlsx import save_data
from collections import OrderedDict
from simple_salesforce import Salesforce
import random

from flask_mail import Mail, Message
mail = Mail(app)

from flask.ext.login import LoginManager
from flask.ext.login import login_user , logout_user , current_user , login_required
from .decorators import require_apikey
from .decorators import async



#status = 'new' OR 'done'
@app.route('/ssp_matrix', methods=["POST"])
def ssp_matrix():
  try:
    casenum = request.form['casenum']
    c,conn = connection()
    time = datetime.now()
    time = time.strftime('%Y-%m-%d %H:%M:%S')
    status = request.form['status']
    designer = request.form['designer']
    if status == 'new':
        c.execute("INSERT INTO sspm (caseid, timein) VALUES (%s, %s)",
                  [thwart(casenum), thwart(time)])
    elif status == 'done':
        c.execute("UPDATE sspm SET timedone = (%s) WHERE caseid = (%s)",
                        [thwart(time),thwart(casenum)])
        c.execute("UPDATE sspm SET designer = (%s) WHERE caseid = (%s)",
                        [thwart(designer),thwart(casenum)])

    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return 'Ok'
  except Exception as e:
        subject = 'SSP Matrix - problem'
        msg = Message(subject , sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
        msg.body = str(e)
        mail.send(msg)
        return str(e)

@app.route('/close_matrix', methods=["POST"])
def close_matrix():
  try:
    casenum = request.form['casenum']
    reviewer = request.form['reviewer']
    closer = request.form['closer']
    c,conn = connection()
    time = datetime.now()
    time = time.strftime('%Y-%m-%d %H:%M:%S')
    
    c.execute("UPDATE closm SET timedone = (%s) WHERE caseid = (%s) order by timein DESC limit 1",
                            [thwart(time), thwart(casenum)])
    c.execute("UPDATE closm SET closer = (%s) WHERE caseid = (%s) order by timein DESC limit 1",
                            [thwart(closer), thwart(casenum)])
    c.execute("UPDATE closm SET reviewer = (%s) WHERE caseid = (%s) order by timein DESC limit 1",
                            [thwart(reviewer), thwart(casenum)])
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return 'Ok'
  except Exception as e:
        subject = 'SSP Matrix - problem'
        msg = Message(subject , sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
        msg.body = str(e)
        mail.send(msg)
        return str(e)
        
@app.route('/shading_matrix/<sfdc>', methods=["GET","POST"])
def shading_matrix(sfdc):
  try:
    c,conn = connection()
    time = datetime.now()
    time = time.strftime('%Y-%m-%d %H:%M:%S')
    
    if request.method == "GET":
        c.execute("INSERT INTO sham (caseid, timein) VALUES (%s, %s)",
                  [thwart(sfdc), thwart(time)])
    
    else:
        designer = request.form['designer']
        c.execute("UPDATE sham SET timedone = (%s) WHERE caseid = (%s)",
                    [thwart(time),thwart(sfdc)])
        c.execute("UPDATE sham SET designer = (%s) WHERE caseid = (%s)",
                        [thwart(designer),thwart(sfdc)])
        c.execute("UPDATE cases SET shading = (%s) WHERE caseid = (%s)",
                    [thwart(designer),thwart(sfdc)])
        
        
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return redirect(urlHome+'case/#Surveyed')
  except Exception as e:
        subject = 'Shading Matrix - problem'
        msg = Message(subject + str(sfdc), sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
        msg.body = str(e)
        mail.send(msg)
        return str(e)

#data = { 'status':'new', 'designer':'Joey' } # new pick 
#data = { 'status':'fail'} #bad tsrf   
#data = { 'status':'reject'} #reject   
#data = { 'status':'submit'} #submit
#data = {'status':'change', 'designer': 'Marra'} #p1-p2   
#data = {'status': 'new'} #bad tsrf save/ finalize     
@app.route('/design_matrix/<sfdc>', methods=["POST"])
def design_matrix(sfdc):
  try:
    c,conn = connection()
    time = datetime.now()
    time = time.strftime('%Y-%m-%d %H:%M:%S')
    status = request.form['status']
    if status == 'new':
        data = c.execute("SELECT * FROM desigm WHERE caseid = (%s) ORDER BY version DESC LIMIT 1",
                          [thwart(sfdc)])
        row = c.fetchone()
        if int(data) == 0:
            data = c.execute("SELECT * FROM cases WHERE caseid = (%s)",
                          [thwart(sfdc)])
            row = c.fetchone()
            if row[1] != None:
                designer = row[1]
                c.execute("INSERT INTO desigm (caseid, timein, designer, version) VALUES (%s, %s, %s, '101')",
                        [thwart(sfdc), thwart(time), thwart(designer)])
            else:
                designer = request.form['designer']
                c.execute("INSERT INTO desigm (caseid, timein, designer, version) VALUES (%s, %s, %s, '1')",
                        [thwart(sfdc), thwart(time), thwart(designer)])
        elif row[4] < 0:
            designer = row[1]
            c.execute("INSERT INTO desigm (caseid, timein, designer, version) VALUES (%s, %s, %s, '1')",
                        [thwart(sfdc), thwart(time), thwart(designer)])
        else:
            version = row[4]
            version = str((int(version/100) + 1) * 100 + 1)
            try: 
                designer = request.form['designer']
            except:
                designer = row[1]
            c.execute("INSERT INTO desigm (caseid, timein, designer, version) VALUES (%s, %s, %s, %s)",
                        [thwart(sfdc), thwart(time), thwart(designer), thwart(version)])
    
    elif status == 'reject':
        data = c.execute("DELETE FROM desigm WHERE caseid = (%s) ORDER BY version DESC LIMIT 1",
                              [thwart(sfdc)])
        data = c.execute("SELECT * FROM desigm WHERE caseid = (%s) ORDER BY version DESC LIMIT 1",
                              [thwart(sfdc)])
        row = c.fetchone()
        designer = row[1]
        version = row[4]
        version = str(version + 1)            
        c.execute("INSERT INTO desigm (caseid, timein, designer, version) VALUES (%s, %s, %s, %s)",
                  [thwart(sfdc), thwart(time), thwart(designer), thwart(version)])
    
    elif status == 'fail':
        data = c.execute("SELECT * FROM desigm WHERE caseid = (%s) ORDER BY version DESC LIMIT 1",
                              [thwart(sfdc)])
        row = c.fetchone()
        c.execute("UPDATE desigm SET timedone = (%s) WHERE caseid = (%s) ORDER BY version DESC LIMIT 1",
                    [thwart(time),thwart(sfdc)])
        c.execute("UPDATE desigm SET version = -1000 WHERE caseid = (%s) ORDER BY version DESC LIMIT 1",
                    [thwart(sfdc)])

                  
    elif status == 'submit':
        c.execute("UPDATE desigm SET timedone = (%s) WHERE caseid = (%s) ORDER BY version DESC LIMIT 1",
                        [thwart(time),thwart(sfdc)])
                        
    elif status == 'change':
        designer = request.form['designer']

        c.execute("UPDATE desigm SET timein = (%s) WHERE caseid = (%s) ORDER BY version DESC LIMIT 1",
                    [thwart(time),thwart(sfdc)])
        c.execute("UPDATE desigm SET designer = (%s) WHERE caseid = (%s) ORDER BY version DESC LIMIT 1",
                    [thwart(designer),thwart(sfdc)])
            
        
    conn.commit()
    c.close()
    conn.close()
    gc.collect()
    return 'OK'
  except Exception as e:
        subject = 'Design Matrix - problem'
        msg = Message(subject + str(sfdc), sender='robotmarriao@gmail.com', recipients=['joey.jiao@levelsolar.com'])
        msg.body = str(e)
        mail.send(msg)
        return str(e)
        


empColor = {'Joey':'#93152d',
            'Alessandro':'#1aadce',
            'Yao':'#e7709e',
            'Tina':'#09e485',
            'Stephanie':'#c21265',
            'Victor':'#2f7ed8',
            'Silun':'#9d60a8',#492970
            'Rebecca':'#f59759',
            'Lukas':'#492970',#77a1e5
            'Ren':'#49b9af',#77a1e5
            'Michael':'#0d233a',
            'Justin':'#666666',
            'Naima':'#fa774f',
            'Meredith':'#c9faff',
            'AD':'#000000',
            'Katerina':'#c21265',
            'None':'#000000'}


@app.route('/prepareCSV/')
@login_required
def prepareCSV():
    try:
        data = OrderedDict() # from collections import OrderedDict
        sfdc = []
        c,conn = connection()
        c.execute("select caseid from cases")
        for row in c:
            sfdc.append((str(row[0])))
        boxIdList=[["Opportunity Id","box_arraydesign__c","box_install__c","box_permit__c","box_sales__c"]]
        boxNoList=[["Opportunity Id","SFDC"]]
        sf = Salesforce(username='integration@levelsolar.com', password='HrNt7DrqaEfZmBqJRan9dKFzmQFp', security_token='yWlJG8lAKCq1pTBkbBMSVcKg')

        response = sf.query_all("select id,Account_Number__c FROM Opportunity WHERE Account_Number__c in " + str(sfdc).replace("u'","'").replace('[','(').replace(']',')').replace(' ',''))
        for item in response['records']:
            try:
                url = urlHome + 'boxid/'+str(item['Account_Number__c']) + '?api_key=Jo3y1SAW3S0M3'
                response_dict = requests.get(url).json()
                boxIdList.append([str(item['Id']),response_dict['AD_id'],response_dict['IN_id'],response_dict['PT_id'],response_dict['SALE_id']])
            except:
                boxNoList.append([str(item['Id']),str(item['Account_Number__c'])])

            
        data.update({"BoxId": boxIdList})
        data.update({"Error": boxNoList})
        
        save_data("/var/www/ADHome/project/static/AD Matrix.xlsx", data)
        return redirect(urlHome + 'static/AD Matrix.xlsx')
    except Exception as e:
        return str(e)

@app.route('/exldownload/')
@login_required
def exldownload():
    try:
        data = OrderedDict() # from collections import OrderedDict
        timeStart = '2016-05-07'
        c,conn = connection()
        x = c.execute("SELECT * FROM sspm WHERE timein > '" + timeStart + "'")
        sspList=[["Case#","Designer","Time In","Time Done"]]
        for row in c:
            if row[3] != None:
                sspList.append([str(row[0]),str(row[1]),str(row[2]),str(row[3])])
        data.update({"SSP": sspList})
        x = c.execute("SELECT * FROM sham WHERE timein > '" + timeStart + "'")
        shmList=[["Case#","Designer","Time In","Time Done"]]
        for row in c:
            if row[3] != None:
                shmList.append([str(row[0]),str(row[1]),str(row[2]),str(row[3])])
        data.update({"Shading": shmList})
        x = c.execute("SELECT * FROM desigm WHERE version = 1 AND timein > '" + timeStart + "'")
        designList=[["Version# starts at 1. Finalize or change request will come as 101, 201 etc. Everytime it gets rejected then plus 1."],["Case#","Designer","Time In","Time Done","Version#"]]
        for row in c:
            if row[3] != None:
                designList.append([str(row[0]),str(row[1]),str(row[2]),str(row[3]),str(row[4])])
        data.update({"Design": designList})
        x = c.execute("SELECT * FROM desigm WHERE version % 100 = 1 AND version != 1 AND timein > '" + timeStart + "'")
        finalList=[["Version# starts at 1. Finalize or change request will come as 101, 201 etc Everytime it gets rejected then plus 1.."],["Case#","Designer","Time In","Time Done","Version#"]]
        for row in c:
            if row[3] != None:
                finalList.append([str(row[0]),str(row[1]),str(row[2]),str(row[3]),str(row[4])])
        data.update({"Finale - Change": finalList})
        x = c.execute("SELECT * FROM desigm WHERE version % 100 != 1 AND version != -1000 AND timein > '" + timeStart + "'")
        rejectList=[["Version# starts at 1. Finalize or change request will come as 101, 201 etc. Everytime it gets rejected then plus 1."],["Case#","Designer","Time In","Time Done","Version#"]]
        for row in c:
            if row[3] != None:
                rejectList.append([str(row[0]),str(row[1]),str(row[2]),str(row[3]),str(row[4])])
        data.update({"Rejection": rejectList})
        x = c.execute("SELECT * FROM revim WHERE reviewer != 'Rejection' and timein > '" + timeStart + "'")
        reviewList=[["Case#","Designer","Time In","Time Done"]]
        for row in c:
            if row[3] != None:
                reviewList.append([str(row[0]),str(row[1]),str(row[2]),str(row[3])])
        data.update({"Review": reviewList})
        save_data("/var/www/ADHome/project/static/AD Matrix.xlsx", data)
        return redirect(urlHome + 'static/AD Matrix.xlsx')
    except Exception as e:
        return str(e)

def fluctuation(new, old):
    try:
        fluc = int((float(new) - float(old))/float(old)*100)
    except:
        fluc = 999
    if fluc > 0:
        return "<span style='color:#00FF00'> +"+str(fluc)+"% </span>"
    elif fluc < 0:
        return "<span style='color:#FF0000'> "+str(fluc)+"% </span>"
    else:
        return "<span> +"+str(fluc)+"% </span>"

currentDesigners = {'Yao':'Yao Wang',
                    'Tina':'Tina Gong',
                    'Victor':'Victor Borisov',
                    'Silun':'Silun Zhang',
                    'Ren':'Ren Yu',#77a1e5
                    'Michael':'Michael Tarzian',
                    'Justin':'Justin Gottlieb',
                    'Naima':'Naima Dejoie',
                    'Rebecca':'Rebecca Handa',
                    'Meredith':'Meredith Johansen',
                    'Katerina':'Katerina Liakos',
                    'Martin':'Martin Forero'}


@app.route('/performanceDaily/')
@require_apikey
def performanceDaily():
    try:
        today = str(datetime.today())[:10]
        subject = 'AD Championship ' + today[5:]
        msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['adteam@levelsolar.com','halvard.lange@levelsolar.com','arraydesign@levelsolar.com','kevin.johnson@levelsolar.com'])
        # msg = Message(subject, sender=('AD - Please Reply To All','adrobot@levelsolar.com'), recipients=['joey.jiao@levelsolar.com'])

        c,conn = connection()
        data = c.execute("select caseid, status, aptDate, info from cases where status = '1' and (aptDate != 'On Hold')")
        backlog = 0
        realBacklog = 0
        nycBacklog = 0
        for row in c:
            info = str(row[3])
            au = 0
            if info.find('AUS:') != -1:
                au = info[info.find('AUS:')+4:info.find(';',info.find('AUS:'))]
            if len(au) > 0 and row[2] != 'g2g-now':
                realBacklog +=1
            if row[2] == 'g2g-now':
                nycBacklog +=1
            backlog +=1

        total = [0,0,0,0,0,0]
        totalWeek = [0,0,0,0,0,0]
        totalMonth = [0,0,0,0,0,0]
        x = c.execute("SELECT designer, count(*) as Total, (count(*) / (SELECT count(*) FROM sspm WHERE timedone > '" + today + "')) * 100 AS 'Percentage' FROM sspm WHERE timedone > '" + today + "' GROUP BY designer ORDER BY Total DESC")
        sspList=[]
        for row in c:
            if str(row[0]) <> 'None':
                total[0] = total[0] + row[1]
                sspList.append([str(row[0]),str(row[1])])

        x = c.execute("SELECT designer, count(*) as Total, (count(*) / (SELECT count(*) FROM sham WHERE timedone > '" + today + "')) * 100 AS 'Percentage' FROM sham WHERE timedone > '" + today + "' GROUP BY designer ORDER BY Total DESC")
        shadingList=[]
        for row in c:
            if str(row[0]) <> 'None':
                total[1] = total[1] + row[1]
                shadingList.append([str(row[0]),str(row[1])])

        x = c.execute("SELECT designer, count(*) as Total, (count(*) / (SELECT count(*) FROM desigm WHERE version = 1 AND timedone > '" + today + "')) * 100 AS 'Percentage' FROM desigm WHERE version = 1 AND timedone > '" + today + "' GROUP BY designer ORDER BY Total DESC")
        designList=[]
        for row in c:
            if str(row[0]) <> 'None':
                total[2] = total[2] + row[1]
                designList.append([str(row[0]),str(row[1])])

        x = c.execute("SELECT designer, count(*) as Total, (count(*) / (SELECT count(*) FROM desigm WHERE version % 100 = 1 AND version != 1 AND timedone > '" + today + "')) * 100 AS 'Percentage' FROM desigm WHERE version % 100 = 1 AND version != 1 AND timedone > '" + today + "' GROUP BY designer ORDER BY Total DESC")
        finalList=[]
        for row in c:
            if str(row[0]) <> 'None':
                total[3] = total[3] + row[1]
                finalList.append([str(row[0]),str(row[1])])

        x = c.execute("SELECT closer, count(*) as Total, (count(*) / (SELECT count(*) FROM closm WHERE timedone > '" + today + "')) * 100 AS 'Percentage' FROM closm WHERE timedone > '" + today + "' GROUP BY closer ORDER BY Total DESC")
        closer = []
        for row in c:
            if str(row[0]) <> 'None':
                total[4] = total[4] + row[1]
                closer.append([str(row[0]),str(row[1])])


        x = c.execute("SELECT reviewer, count(*) as Total, (count(*) / (SELECT count(*) FROM revim WHERE reviewer != 'Rejection' and timedone > '" + today + "')) * 100 AS 'Percentage' FROM revim WHERE reviewer != 'Rejection' and timedone > '" + today + "' GROUP BY reviewer ORDER BY Total DESC")
        reviewer = []
        for row in c:
            if str(row[0]) <> 'None':
                total[5] = total[5] + row[1]
                reviewer.append([str(row[0]),str(row[1])])

        wholeLastWeek = []
        dayNumber = str(4 - datetime.today().weekday())

        x = c.execute("SELECT designer, count(*) as Total FROM sspm WHERE timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())-1 DAY GROUP BY designer ORDER BY Total DESC")
        sspWeekList=[]
        for row in c:
            if str(row[0]) <> 'None':
                totalWeek[0] = totalWeek[0] + row[1]
                sspWeekList.append([str(row[0]),str(row[1])])

        x = c.execute("SELECT designer, count(*) as Total FROM sham WHERE timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())-1 DAY GROUP BY designer ORDER BY Total DESC")
        shadingWeekList=[]
        for row in c:
            if str(row[0]) <> 'None':
                totalWeek[1] = totalWeek[1] + row[1]
                shadingWeekList.append([str(row[0]),str(row[1])])
        

        x = c.execute("SELECT designer, count(*) as Total FROM desigm WHERE version = 1 AND timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())-1 DAY GROUP BY designer ORDER BY Total DESC")
        designWeekList=[]
        for row in c:
            if str(row[0]) <> 'None':
                totalWeek[2] = totalWeek[2] + row[1]
                designWeekList.append([str(row[0]),str(row[1])])

        x = c.execute("SELECT designer, count(*) as Total FROM desigm WHERE version % 100 = 1 AND version != 1 AND timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())-1 DAY GROUP BY designer ORDER BY Total DESC")
        finalWeekList=[]
        for row in c:
            if str(row[0]) <> 'None':
                totalWeek[3] = totalWeek[3] + row[1]
                finalWeekList.append([str(row[0]),str(row[1])])

        x = c.execute("SELECT closer, count(*) as Total FROM closm WHERE timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())-1 DAY GROUP BY closer ORDER BY Total DESC")
        closerWeek = []
        for row in c:
            if str(row[0]) <> 'None':
                totalWeek[4] = totalWeek[4] + row[1]
                closerWeek.append([str(row[0]),str(row[1])])

        x = c.execute("SELECT reviewer, count(*) as Total FROM revim WHERE reviewer != 'Rejection' and timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())-1 DAY GROUP BY reviewer ORDER BY Total DESC")
        reviewerWeek = []
        for row in c:
            if str(row[0]) <> 'None':
                totalWeek[5] = totalWeek[5] + row[1]
                reviewerWeek.append([str(row[0]),str(row[1])])

        ############################################################################
        x = c.execute("SELECT designer, count(*) as Total FROM sspm WHERE YEAR(timedone) = YEAR(CURRENT_DATE()) AND MONTH(timedone) = MONTH(CURRENT_DATE()) GROUP BY designer ORDER BY Total DESC")
        sspMonthList=[]
        for row in c:
            if str(row[0]) <> 'None':
                totalMonth[0] = totalMonth[0] + row[1]
                sspMonthList.append([str(row[0]),str(row[1])])

        x = c.execute("SELECT designer, count(*) as Total FROM sham WHERE YEAR(timedone) = YEAR(CURRENT_DATE()) AND MONTH(timedone) = MONTH(CURRENT_DATE()) GROUP BY designer ORDER BY Total DESC")
        shadingMonthList=[]
        for row in c:
            if str(row[0]) <> 'None':
                totalMonth[1] = totalMonth[1] + row[1]
                shadingMonthList.append([str(row[0]),str(row[1])])
        

        x = c.execute("SELECT designer, count(*) as Total FROM desigm WHERE version = 1 AND YEAR(timedone) = YEAR(CURRENT_DATE()) AND MONTH(timedone) = MONTH(CURRENT_DATE()) GROUP BY designer ORDER BY Total DESC")
        designMonthList=[]
        for row in c:
            if str(row[0]) <> 'None':
                totalMonth[2] = totalMonth[2] + row[1]
                designMonthList.append([str(row[0]),str(row[1])])

        x = c.execute("SELECT designer, count(*) as Total FROM desigm WHERE version % 100 = 1 AND version != 1 AND YEAR(timedone) = YEAR(CURRENT_DATE()) AND MONTH(timedone) = MONTH(CURRENT_DATE()) GROUP BY designer ORDER BY Total DESC")
        finalMonthList=[]
        for row in c:
            if str(row[0]) <> 'None':
                totalMonth[3] = totalMonth[3] + row[1]
                finalMonthList.append([str(row[0]),str(row[1])])

        x = c.execute("SELECT closer, count(*) as Total FROM closm WHERE YEAR(timedone) = YEAR(CURRENT_DATE()) AND MONTH(timedone) = MONTH(CURRENT_DATE()) GROUP BY closer ORDER BY Total DESC")
        closerMonth = []
        for row in c:
            if str(row[0]) <> 'None':
                totalMonth[4] = totalMonth[4] + row[1]
                closerMonth.append([str(row[0]),str(row[1])])

        x = c.execute("SELECT reviewer, count(*) as Total FROM revim WHERE reviewer != 'Rejection' and YEAR(timedone) = YEAR(CURRENT_DATE()) AND MONTH(timedone) = MONTH(CURRENT_DATE()) GROUP BY reviewer ORDER BY Total DESC")
        reviewerMonth = []
        for row in c:
            if str(row[0]) <> 'None':
                totalMonth[5] = totalMonth[5] + row[1]
                reviewerMonth.append([str(row[0]),str(row[1])])

        # ##########################################################################

        x = c.execute("SELECT count(*) FROM sspm WHERE timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6 DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())+" + dayNumber + " DAY")
        row = c.fetchone()
        wholeLastWeek.append(row[0])
        x = c.execute("SELECT count(*) FROM sham WHERE designer <> 'None' AND timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6 DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())+" + dayNumber + " DAY")
        row = c.fetchone()
        wholeLastWeek.append(row[0])
        x = c.execute("SELECT count(*) FROM desigm WHERE timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6 DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())+" + dayNumber + " DAY AND version = '1'")
        row = c.fetchone()
        wholeLastWeek.append(row[0])
        x = c.execute("SELECT count(*) FROM desigm WHERE timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6 DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())+" + dayNumber + " DAY AND version % 100 = 1 AND version != 1")
        row = c.fetchone()
        wholeLastWeek.append(row[0])
        x = c.execute("SELECT count(*) FROM closm WHERE timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6 DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())+" + dayNumber + " DAY")
        row = c.fetchone()
        wholeLastWeek.append(row[0])
        x = c.execute("SELECT count(*) FROM revim WHERE reviewer != 'Rejection' and timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6 DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())+" + dayNumber + " DAY")
        row = c.fetchone()
        wholeLastWeek.append(row[0])

        wholeThisWeek = []
        x = c.execute("SELECT count(*) FROM sspm WHERE timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())-1 DAY")
        row = c.fetchone()
        wholeThisWeek.append(row[0])
        x = c.execute("SELECT count(*) FROM sham WHERE designer <> 'None' AND timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())-1 DAY")
        row = c.fetchone()
        wholeThisWeek.append(row[0])
        x = c.execute("SELECT count(*) FROM desigm WHERE timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())-1 DAY AND version = '1'")
        row = c.fetchone()
        wholeThisWeek.append(row[0])
        x = c.execute("SELECT count(*) FROM desigm WHERE timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())-1 DAY AND version % 100 = 1 AND version != 1")
        row = c.fetchone()
        wholeThisWeek.append(row[0])
        x = c.execute("SELECT count(*) FROM closm WHERE timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())-1 DAY")
        row = c.fetchone()
        wholeThisWeek.append(row[0])
        x = c.execute("SELECT count(*) FROM revim WHERE reviewer != 'Rejection' and timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())-1 DAY")
        row = c.fetchone()
        wholeThisWeek.append(row[0])

        designerMatrixDay = {# 'Tina Gong':['-']*6,
                              # 'Victor Borisov':['-']*6,
                              # 'Silun Zhang':['-']*6,
                              'Naima Dejoie':['-']*6,
                              # 'Ren Yu':['-']*6,#77a1e5
                              'Michael Tarzian':['-']*6,
                              'Katerina Liakos':['-']*6,
                              # 'Rebecca Handa':['-']*6,
                              'Justin Gottlieb':['-']*6,
                              'Meredith Johansen':['-']*6,
                              'Total':total}
        designerMatrixWeek = {# 'Tina Gong':['-']*6,
                              # 'Victor Borisov':['-']*6,
                              # 'Silun Zhang':['-']*6,
                              'Naima Dejoie':['-']*6,
                              # 'Ren Yu':['-']*6,#77a1e5
                              # 'Rebecca Handa':['-']*6,
                              'Michael Tarzian':['-']*6,
                              'Katerina Liakos':['-']*6,
                              'Justin Gottlieb':['-']*6,
                              'Meredith Johansen':['-']*6,
                              'Total':totalWeek}
        designerMatrixMonth = {# 'Tina Gong':['-']*6,
                              # 'Victor Borisov':['-']*6,
                              # 'Silun Zhang':['-']*6,
                              'Naima Dejoie':['-']*6,
                              # 'Ren Yu':['-']*6,#77a1e5
                              # 'Rebecca Handa':['-']*6,
                              'Michael Tarzian':['-']*6,
                              'Katerina Liakos':['-']*6,
                              'Justin Gottlieb':['-']*6,
                              'Meredith Johansen':['-']*6,
                              'Total':totalMonth}
        for item in sspList:
            try:
                designerMatrixDay[currentDesigners[item[0]]][0] = item[1]
            except:
                try:
                    designerMatrixDay[item[0]][0] = item[1]
                except:
                    pass
        for item in shadingList:
            try:
                designerMatrixDay[currentDesigners[item[0]]][1] = item[1]
            except:
                try:
                    designerMatrixDay[item[0]][1] = item[1]
                except:
                    pass
        for item in designList:
            try:
                designerMatrixDay[currentDesigners[item[0]]][2] = item[1]
            except:
                try:
                    designerMatrixDay[item[0]][2] = item[1]
                except:
                    pass
        for item in finalList:
            try:
                designerMatrixDay[currentDesigners[item[0]]][3] = item[1]
            except:
                try:
                    designerMatrixDay[item[0]][3] = item[1]
                except:
                    pass
        for item in closer:
            try:
                designerMatrixDay[currentDesigners[item[0]]][4] = item[1]
            except:
                try:
                    designerMatrixDay[item[0]][4] = item[1]
                except:
                    pass
        for item in reviewer:
            try:
                designerMatrixDay[currentDesigners[item[0]]][5] = item[1]
            except:
                try:
                    designerMatrixDay[item[0]][5] = item[1]
                except:
                    pass
        ##############Week
        for item in sspWeekList:
            try:
                designerMatrixWeek[currentDesigners[item[0]]][0] = item[1]
            except:
                try:
                    designerMatrixWeek[item[0]][0] = item[1]
                except:
                    pass
        for item in shadingWeekList:
            try:
                designerMatrixWeek[currentDesigners[item[0]]][1] = item[1]
            except:
                try:
                    designerMatrixWeek[item[0]][1] = item[1]
                except:
                    pass
        for item in designWeekList:
            try:
                designerMatrixWeek[currentDesigners[item[0]]][2] = item[1]
            except:
                try:
                    designerMatrixWeek[item[0]][2] = item[1]
                except:
                    pass
        for item in finalWeekList:
            try:
                designerMatrixWeek[currentDesigners[item[0]]][3] = item[1]
            except:
                try:
                    designerMatrixWeek[item[0]][3] = item[1]
                except:
                    pass
        for item in closerWeek:
            try:
                designerMatrixWeek[currentDesigners[item[0]]][4] = item[1]
            except:
                try:
                    designerMatrixWeek[item[0]][4] = item[1]
                except:
                    pass
        for item in reviewerWeek:
            try:
                designerMatrixWeek[currentDesigners[item[0]]][5] = item[1]
            except:
                try:
                    designerMatrixWeek[item[0]][5] = item[1]
                except:
                    pass
        #########################Month
        for item in sspMonthList:
            try:
                designerMatrixMonth[currentDesigners[item[0]]][0] = item[1]
            except:
                try:
                    designerMatrixMonth[item[0]][0] = item[1]
                except:
                    pass
        for item in shadingMonthList:
            try:
                designerMatrixMonth[currentDesigners[item[0]]][1] = item[1]
            except:
                try:
                    designerMatrixMonth[item[0]][1] = item[1]
                except:
                    pass
        for item in designMonthList:
            try:
                designerMatrixMonth[currentDesigners[item[0]]][2] = item[1]
            except:
                try:
                    designerMatrixMonth[item[0]][2] = item[1]
                except:
                    pass
        for item in finalMonthList:
            try:
                designerMatrixMonth[currentDesigners[item[0]]][3] = item[1]
            except:
                try:
                    designerMatrixMonth[item[0]][3] = item[1]
                except:
                    pass
        for item in closerMonth:
            try:
                designerMatrixMonth[currentDesigners[item[0]]][4] = item[1]
            except:
                try:
                    designerMatrixMonth[item[0]][4] = item[1]
                except:
                    pass
        for item in reviewerMonth:
            try:
                designerMatrixMonth[currentDesigners[item[0]]][5] = item[1]
            except:
                try:
                    designerMatrixMonth[item[0]][5] = item[1]
                except:
                    pass



        msg.html = '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><style type="text/css" media="screen">table {border-collapse:collapse;width: 100%;}th, td {text-align:left;padding: 8px;}tr:nth-child(even){background-color: #f2f2f2}</style></head><body><table style="width:800px;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:20%;text-align:left">Backlog</th><th style="text-decoration:underline;width:26%;text-align:left">With Consumption</th><th style="text-decoration:underline;width:26%;text-align:left">Need Consumption</th><th style="text-decoration:underline;width:26%;text-align:left">G2G Finalization</th></tr>'
        msg.html = msg.html + '<tr><td>#</td><td>' + str(realBacklog) + '</td><td>' + str(backlog - nycBacklog - realBacklog) + '</td><td>' + str(nycBacklog) + '</td></tr></table>'

        msg.html = msg.html + '<table style="width:800px;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:20%;text-align:left">Category</th><th style="text-decoration:underline;width:20%;text-align:left">Today</th><th style="text-decoration:underline;width:20%;text-align:left">This Week</th><th style="text-decoration:underline;width:20%;text-align:left">Last Week</th><th style="text-decoration:underline;width:20%;text-align:left">This Month</th></tr>'

        msg.html = msg.html + '<tr><td># of SSP</td><td>' + str(total[0]) + '</td><td>' + str(wholeThisWeek[0]) + '</td><td>' + str(wholeLastWeek[0]) + '</td><td>' + str(designerMatrixMonth['Total'][0]) + '</td></tr>'
        msg.html = msg.html + '<tr><td># of Shading</td><td>' + str(total[1]) + '</td><td>' + str(wholeThisWeek[1]) + '</td><td>' + str(wholeLastWeek[1]) + '</td><td>' + str(designerMatrixMonth['Total'][1]) + '</td></tr>'
        msg.html = msg.html + '<tr><td># of Design</td><td>' + str(total[2]) + '</td><td>' + str(wholeThisWeek[2]) + '</td><td>' + str(wholeLastWeek[2]) + '</td><td>' + str(designerMatrixMonth['Total'][2]) + '</td></tr>'
        msg.html = msg.html + '<tr><td># of Desgn Change</td><td>' + str(total[3]) + '</td><td>' + str(wholeThisWeek[3]) + '</td><td>' + str(wholeLastWeek[3]) + '</td><td>' + str(designerMatrixMonth['Total'][3]) + '</td></tr>'
        msg.html = msg.html + '<tr><td># of Desgn Closed</td><td>' + str(total[4]) + '</td><td>' + str(wholeThisWeek[4]) + '</td><td>' + str(wholeLastWeek[4]) + '</td><td>' + str(designerMatrixMonth['Total'][4]) + '</td></tr>'
        msg.html = msg.html + '<tr><td># of Desgn Reviewed</td><td>' + str(total[5]) + '</td><td>' + str(wholeThisWeek[5]) + '</td><td>' + str(wholeLastWeek[5]) + '</td><td>' + str(designerMatrixMonth['Total'][5]) + '</td></tr>'

        msg.html = msg.html + "</table><p style=text-decoration:underline;text-align:left'><strong>Today's Metrics:</strong></p>"

        msg.html = msg.html + '<table style="width:1200px;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:12.5%;text-align:left">Array Designer</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of SSP</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Shading</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Design</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Design Change</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Design Closed</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Design Reviewed</th></tr>'
        for item in designerMatrixDay:
            if str(item) <> 'Total':
                msg.html = msg.html + '<tr><td>'+str(item)+'</td><td>' + str(designerMatrixDay[item][0]) + '</td><td>' + str(designerMatrixDay[item][1]) + '</td><td>' + str(designerMatrixDay[item][2]) + '</td><td>' + str(designerMatrixDay[item][3]) + '</td><td>' + str(designerMatrixDay[item][4]) + '</td><td>' + str(designerMatrixDay[item][5]) + '</td></tr>'
                # msg.html = msg.html + '<tr><td>'+str(item)'</td></tr>'
                # return str(item)
        msg.html = msg.html + '<tr><td>Total</td><td>' + str(designerMatrixDay['Total'][0]) + '</td><td>' + str(designerMatrixDay['Total'][1]) + '</td><td>' + str(designerMatrixDay['Total'][2]) + '</td><td>' + str(designerMatrixDay['Total'][3]) + '</td><td>' + str(designerMatrixDay['Total'][4]) + '</td><td>' + str(designerMatrixDay['Total'][5]) + '</td></tr>'
        msg.html = msg.html + "</table><p style=text-decoration:underline;text-align:left'><strong>This Week's Metrics:</strong></p>"

        msg.html = msg.html + '<table style="width:1200px;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:12.5%;text-align:left">Array Designer</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of SSP</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Shading</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Design</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Design Change</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Design Closed</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Design Reviewed</th></tr>'
        for item in designerMatrixWeek:
            if str(item) <> 'Total':
                msg.html = msg.html + '<tr><td>'+str(item)+'</td><td>' + str(designerMatrixWeek[item][0]) + '</td><td>' + str(designerMatrixWeek[item][1]) + '</td><td>' + str(designerMatrixWeek[item][2]) + '</td><td>' + str(designerMatrixWeek[item][3]) + '</td><td>' + str(designerMatrixWeek[item][4]) + '</td><td>' + str(designerMatrixWeek[item][5]) + '</td></tr>'
                # msg.html = msg.html + '<tr><td>'+str(item)'</td></tr>'
                # return str(item)
        msg.html = msg.html + '<tr><td>Total</td><td>' + str(designerMatrixWeek['Total'][0]) + '</td><td>' + str(designerMatrixWeek['Total'][1]) + '</td><td>' + str(designerMatrixWeek['Total'][2]) + '</td><td>' + str(designerMatrixWeek['Total'][3]) + '</td><td>' + str(designerMatrixWeek['Total'][4]) + '</td><td>' + str(designerMatrixWeek['Total'][5]) + '</td></tr>'

        msg.html = msg.html + "</table><p style=text-decoration:underline;text-align:left'><strong>This Month's Metrics:</strong></p>"

        msg.html = msg.html + '<table style="width:1200px;border:1px solid black;margin-bottom:20px;padding-top:7px;padding-bottom:7px"><tr><th style="text-decoration:underline;width:12.5%;text-align:left">Array Designer</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of SSP</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Shading</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Design</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Design Change</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Design Closed</th><th style="text-decoration:underline;width:12.5%;text-align:left"># of Design Reviewed</th></tr>'
        for item in designerMatrixMonth:
            if str(item) <> 'Total':
                msg.html = msg.html + '<tr><td>'+str(item)+'</td><td>' + str(designerMatrixMonth[item][0]) + '</td><td>' + str(designerMatrixMonth[item][1]) + '</td><td>' + str(designerMatrixMonth[item][2]) + '</td><td>' + str(designerMatrixMonth[item][3]) + '</td><td>' + str(designerMatrixMonth[item][4]) + '</td><td>' + str(designerMatrixMonth[item][5]) + '</td></tr>'
                # msg.html = msg.html + '<tr><td>'+str(item)'</td></tr>'
                # return str(item)
        msg.html = msg.html + '<tr><td>Total</td><td>' + str(designerMatrixMonth['Total'][0]) + '</td><td>' + str(designerMatrixMonth['Total'][1]) + '</td><td>' + str(designerMatrixMonth['Total'][2]) + '</td><td>' + str(designerMatrixMonth['Total'][3]) + '</td><td>' + str(designerMatrixMonth['Total'][4]) + '</td><td>' + str(designerMatrixMonth['Total'][5]) + '</td></tr>'

        msg.html = msg.html + '</table><h4>--------------------------------------------------</h4><p>Thank you!</p></body></html>'
        mail.send(msg)
        return 'good'
    except Exception as e:
        return str(e)

@app.route('/matrixclean/')
@login_required
def matrixclean():
    try:
        timeStart = '2016-10-06'
        c,conn = connection()
        data = c.execute("SELECT * FROM sspm WHERE timein > '" + timeStart + "'")
        sspm = c.fetchall()
        sspList=[]
        for item in sspm:
            if item[3] == None:
                x = c.execute("SELECT status FROM cases WHERE caseid = "+str(item[0]))
                row = c.fetchone()
                if int(x) == 0 or row[0] != '0':
                    sspList.append(item[0])
        data = c.execute("SELECT * FROM sham WHERE timein > '" + timeStart + "'")
        sham = c.fetchall()
        shaList=[]
        for item in sham:
            if item[3] == None:
                x = c.execute("SELECT status FROM cases WHERE caseid = "+str(item[0]))
                row = c.fetchone()
                if int(x) == 0 or float(row[0]) > 1:
                    shaList.append(item[0])
        data = c.execute("SELECT * FROM desigm WHERE timein > '" + timeStart + "'")
        desigm = c.fetchall()
        desList=[]
        for item in desigm:
            if item[3] == None:
                x = c.execute("SELECT status FROM cases WHERE caseid = "+str(item[0]))
                row = c.fetchone()
                if int(x) == 0 or float(row[0]) <> 1:
                    desList.append([item[0],item[4]])
        return str(sspList).replace('L','')
        return str(shaList).replace('L','')
        return str(desList).replace('L','')

        for item in sspList:
            x = c.execute("DELETE FROM sspm WHERE caseid = "+str(item))
        for item in shaList:
            x = c.execute("DELETE FROM sham WHERE caseid = "+str(item))
        for item in desList:
            x = c.execute("DELETE FROM desigm WHERE caseid = "+str(item[0])+" AND version = "+str(item[1]))

        conn.commit()
        c.close()
        conn.close()
        gc.collect()
        return 'Done'
    except Exception as e:
        return str(e)
        
@app.route('/matrix/')
@login_required
def matrix():
    try:
        c,conn = connection()
        #SSP Completed time distribution
        data = c.execute("select DATEDIFF(curdate() - INTERVAL DAYOFWEEK(curdate())+6 DAY,min(timein))/7 from sspm")
        row = c.fetchone()
        sspWeek = int(math.ceil(row[0])) + 1
        personalAvg = {'Joey':np.zeros((5,sspWeek)),
                       'Alessandro':np.zeros((5,sspWeek)),
                       # 'Lennon':np.zeros((5,sspWeek)),
                       'Yao':np.zeros((5,sspWeek)),
                       'Tina':np.zeros((5,sspWeek)),
                       'Stephanie':np.zeros((5,sspWeek)),
                       'Victor':np.zeros((5,sspWeek)),
                       'Silun':np.zeros((5,sspWeek)),
                       'Katerina':np.zeros((5,sspWeek)),
                       'Rebecca':np.zeros((5,sspWeek)),
                       'Lukas':np.zeros((5,sspWeek)),
                       'Michael':np.zeros((5,sspWeek)),
                       'Justin':np.zeros((5,sspWeek)),
                       'Naima':np.zeros((5,sspWeek)),
                       'Ren':np.zeros((5,sspWeek)),
                       'Meredith':np.zeros((5,sspWeek)),
                       'AD':np.zeros((5,sspWeek)),
                       'None':np.zeros((5,sspWeek))}
        personalShare = {'Joey':np.zeros((5,sspWeek)),
                       'Alessandro':np.zeros((5,sspWeek)),
                       # 'Lennon':np.zeros((5,sspWeek)),
                       'Yao':np.zeros((5,sspWeek)),
                       'Tina':np.zeros((5,sspWeek)),
                       'Stephanie':np.zeros((5,sspWeek)),
                       'Victor':np.zeros((5,sspWeek)),
                       'Silun':np.zeros((5,sspWeek)),
                       'Katerina':np.zeros((5,sspWeek)),
                       'Rebecca':np.zeros((5,sspWeek)),
                       'Lukas':np.zeros((5,sspWeek)),
                       'Michael':np.zeros((5,sspWeek)),
                       'Justin':np.zeros((5,sspWeek)),
                       'Naima':np.zeros((5,sspWeek)),
                       'Ren':np.zeros((5,sspWeek)),
                       'Meredith':np.zeros((5,sspWeek)),
                       'AD':np.zeros((5,sspWeek)),
                       'None':np.zeros((5,sspWeek))}
        personalScore = {'Joey':np.zeros((5,sspWeek)),
                       'Alessandro':np.zeros((5,sspWeek)),
                       # 'Lennon':np.zeros((5,sspWeek)),
                       'Yao':np.zeros((5,sspWeek)),
                       'Tina':np.zeros((5,sspWeek)),
                       'Stephanie':np.zeros((5,sspWeek)),
                       'Victor':np.zeros((5,sspWeek)),
                       'Silun':np.zeros((5,sspWeek)),
                       'Katerina':np.zeros((5,sspWeek)),
                       'Rebecca':np.zeros((5,sspWeek)),
                       'Lukas':np.zeros((5,sspWeek)),
                       'Michael':np.zeros((5,sspWeek)),
                       'Justin':np.zeros((5,sspWeek)),
                       'Naima':np.zeros((5,sspWeek)),
                       'Ren':np.zeros((5,sspWeek)),
                       'Meredith':np.zeros((5,sspWeek)),
                       'AD':np.zeros((5,sspWeek)),
                       'None':np.zeros((5,sspWeek))}
        personalCount = {'Joey':np.zeros((4,sspWeek)),
                       'Alessandro':np.zeros((4,sspWeek)),
                       # 'Lennon':np.zeros((4,sspWeek)),
                       'Yao':np.zeros((4,sspWeek)),
                       'Tina':np.zeros((4,sspWeek)),
                       'Stephanie':np.zeros((4,sspWeek)),
                       'Victor':np.zeros((4,sspWeek)),
                       'Silun':np.zeros((4,sspWeek)),
                       'Katerina':np.zeros((4,sspWeek)),
                       'Rebecca':np.zeros((4,sspWeek)),
                       'Lukas':np.zeros((4,sspWeek)),
                       'Michael':np.zeros((4,sspWeek)),
                       'Justin':np.zeros((4,sspWeek)),
                       'Naima':np.zeros((4,sspWeek)),
                       'Ren':np.zeros((4,sspWeek)),
                       'Meredith':np.zeros((4,sspWeek)),
                       'AD':np.zeros((4,sspWeek)),
                       'None':np.zeros((4,sspWeek))}
        historyAvg = []
        
        series = [[]]
        historyAvg.append({'SSP':[]})
        for i in range(0,sspWeek):
            ssp_DICT = {}
            hist = {}
            name = ''
            series.append([])
            data = c.execute("SELECT * from sspm WHERE designer <> '8' and timein >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timein < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY ORDER BY designer")
            dataAvg = []
            for row in c:
                if row[3] != None:
                    if name != row[1]:
                        name = row[1]
                        ssp_DICT[name] = []
                    if int(str(row[2])[11:13]) < 17:
                        T_diff = int((row[3] - row[2]).total_seconds() / 60)
                        T_diff = T_diff 
                        ssp_DICT[name].append(T_diff)
                        dataAvg.append(T_diff)
            if len(dataAvg) > 0:
                historyAvg[0]['SSP'].append(float(sum(dataAvg))/float(len(dataAvg)))
            else:
                historyAvg[0]['SSP'].append(0)
            for j in ssp_DICT:
                if len(ssp_DICT[j]) > 0:
                    personalAvg[j][0][i] = float(sum(ssp_DICT[j]))/float(len(ssp_DICT[j]))
                hist[j] = np.histogram(ssp_DICT[j], bins=[0, 15, 30, 60, 100, 150])[0].tolist()
            for j in hist:
                if max(hist[j]) != 0:
                    series[i+1].append({'name': j, 'color':empColor[j],'data': hist[j]})
        series[0] = series[1]

        #SSP Share
        series2 = [[]]
        for i in range(0,sspWeek):
            ssp_DICT = []
            series2.append([])
            data = c.execute("SELECT designer, count(*) as Total, (count(*) / (SELECT count(*) FROM sspm WHERE designer <> '8' and timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY)) * 100 AS 'Percentage' FROM sspm WHERE designer <> '8' and timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY GROUP BY designer ORDER BY designer DESC")
            for row in c:
                # return str(row)
                if str(row[0]) <> 'None':
                    personalCount[row[0]][0][i] = int(row[1])
                    personalShare[row[0]][0][i] = float(row[2])
                    ssp_DICT.append({'name': str(row[0]) + ' x' + str(row[1]),'y': float(row[2]),'color': empColor[str(row[0])]})
            series2[i+1].append({'name': 'Share', 'data': ssp_DICT})
        series2[0] = series2[1]

        #Shading Complete
        series3 = [[]]
        historyAvg.append({'Shading':[]})
        for i in range(0,sspWeek):
            shatime_DICT = {}
            hist = {}
            name = ''
            series3.append([])
            dataAvg = []
            data = c.execute("SELECT * from sham WHERE designer <> '8' and timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY ORDER BY designer")
            for row in c:
                if row[3] != None:
                    if name != row[1]:
                        name = row[1]
                        shatime_DICT[name] = []
                    T_diff = int((row[3] - row[2]).total_seconds() / 60)
                    T_diff = T_diff 
                    shatime_DICT[name].append(T_diff)
                    dataAvg.append(T_diff)
            if len(dataAvg) > 0:
                historyAvg[1]['Shading'].append(float(sum(dataAvg))/float(len(dataAvg)))
            else:
                historyAvg[1]['Shading'].append(0)
            for j in shatime_DICT:
                if len(shatime_DICT[j]) > 0:
                    personalAvg[j][1][i] = float(sum(shatime_DICT[j]))/float(len(shatime_DICT[j]))
                hist[j] = np.histogram(shatime_DICT[j], bins=[0, 30, 180, 480, 2880, 100000])[0].tolist()
            for j in hist:
                if max(hist[j]) != 0:
                    series3[i+1].append({'name': j, 'color':empColor[j],'data': hist[j]})
        series3[0] = series3[1]

        #Shading Share
        series4 = [[]]
        for i in range(0,sspWeek):
            shatime_DICT = []
            series4.append([])
            data = c.execute("SELECT designer, count(*) as Total, (count(*) / (SELECT count(*) FROM sham WHERE designer <> '8' and timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY)) * 100 AS 'Percentage' FROM sham WHERE designer <> '8' and timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY GROUP BY designer ORDER BY designer DESC")
            for row in c:
                if str(row[0]) <> 'None':
                    personalCount[row[0]][1][i] = int(row[1])
                    personalShare[row[0]][1][i] = float(row[2])
                    shatime_DICT.append({'name': str(row[0]) + ' x' + str(row[1]),'y': float(row[2]),'color': empColor[str(row[0])]})
            series4[i+1].append({'name': 'Share', 'data': shatime_DICT})
        series4[0] = series4[1]

        #1st design complete time
        series5 = [[]]
        historyAvg.append({'Design':[]})
        for i in range(0,sspWeek):
            design_DICT = {}
            hist = {}
            name = ''
            series5.append([])
            dataAvg = []
            data = c.execute("SELECT * from desigm WHERE designer <> '8' and version = 1 AND timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY ORDER BY designer")
            for row in c:
                if row[3] != None:
                    if name != row[1]:
                        name = row[1]
                        design_DICT[name] = []
                    T_diff = int((row[3] - row[2]).total_seconds() / 60) 
                    T_diff = T_diff 
                    design_DICT[name].append(T_diff)
                    dataAvg.append(T_diff)
            if len(dataAvg) > 0:
                historyAvg[2]['Design'].append(float(sum(dataAvg))/float(len(dataAvg)))
            else:
                historyAvg[2]['Design'].append(0)
            for j in design_DICT:
                if len(design_DICT[j]) > 0:
                    personalAvg[j][2][i] = float(sum(design_DICT[j]))/float(len(design_DICT[j]))
                hist[j] = np.histogram(design_DICT[j], bins=[0, 30, 60, 120, 180, 480, 50000])[0].tolist()
            for j in hist:
                if max(hist[j]) != 0:
                    series5[i+1].append({'name': j, 'color':empColor[j],'data': hist[j]})
        series5[0] = series5[1]

        #1st design share
        series6 = [[]]
        for i in range(0,sspWeek):
            des1_DICT = []
            series6.append([])
            data = c.execute("SELECT designer, count(*) as Total, (count(*) / (SELECT count(*) FROM desigm WHERE designer <> '8' and version = 1 AND timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY)) * 100 AS 'Percentage' FROM desigm WHERE designer <> '8' and version = 1 AND timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY GROUP BY designer ORDER BY designer DESC")
            for row in c:
                if str(row[0]) <> 'None':
                    personalCount[row[0]][2][i] = int(row[1])
                    personalShare[row[0]][2][i] = float(row[2])
                    des1_DICT.append({'name': str(row[0]) + ' x' + str(row[1]),'y': float(row[2]),'color': empColor[str(row[0])]})
            series6[i+1].append({'name': 'Share', 'data': des1_DICT})
        series6[0] = series6[1]

        #finalize complete time
        series7 = [[]]
        historyAvg.append({'Finalize/ Change':[]})
        for i in range(0,sspWeek):
            design_DICT = {}
            hist = {}
            name = ''
            series7.append([])
            dataAvg = []
            data = c.execute("SELECT * FROM desigm WHERE designer <> '8' and version % 100 = 1 AND version != 1 AND timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY ORDER BY designer")
            for row in c:
                if row[3] != None:
                    if name != row[1]:
                        name = row[1]
                        design_DICT[name] = []
                    T_diff = int((row[3] - row[2]).total_seconds() / 60)
                    T_diff = T_diff 
                    design_DICT[name].append(T_diff)
                    dataAvg.append(T_diff)
            if len(dataAvg) > 0:
                historyAvg[3]['Finalize/ Change'].append(float(sum(dataAvg))/float(len(dataAvg)))
            else:
                historyAvg[3]['Finalize/ Change'].append(0)
            for j in design_DICT:
                if len(design_DICT[j]) > 0:
                    personalAvg[j][3][i] = float(sum(design_DICT[j]))/float(len(design_DICT[j]))
                hist[j] = np.histogram(design_DICT[j], bins=[0, 30, 60, 120, 180, 480, 500000])[0].tolist()
            for j in hist:
                if max(hist[j]) != 0:
                    series7[i+1].append({'name': j, 'color':empColor[j],'data': hist[j]})
        series7[0] = series7[1]

        #finalize share
        series8 = [[]]
        for i in range(0,sspWeek):
            des2_DICT = []
            series8.append([])
            data = c.execute("SELECT designer, count(*) as Total, (count(*) / (SELECT count(*) FROM desigm WHERE designer <> '8' and version % 100 = 1 AND version != 1 AND timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY)) * 100 AS 'Percentage' FROM desigm WHERE designer <> '8' and version % 100 = 1 AND version != 1 AND timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY GROUP BY designer ORDER BY designer DESC")
            for row in c:
                if str(row[0]) <> 'None':
                    personalCount[row[0]][3][i] = int(row[1])
                    personalShare[row[0]][3][i] = float(row[2])
                    des2_DICT.append({'name': str(row[0]) + ' x' + str(row[1]),'y': float(row[2]),'color': empColor[str(row[0])]})
            series8[i+1].append({'name': 'Share', 'data': des2_DICT})
        series8[0] = series8[1]

        #rejection rate
        series9 = [[]]
        for i in range(0,sspWeek):
            reject_DICT = []
            series9.append([])
            data = c.execute("SELECT designer, count(*) as Total, (count(*) / (SELECT count(*) FROM desigm WHERE designer <> '8' and version % 100 != 1 AND version != -1000 AND timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY)) * 100 AS 'Percentage' FROM desigm WHERE designer <> '8' and version % 100 != 1 AND version != -1000 AND timedone >= curdate() - INTERVAL DAYOFWEEK(curdate())+6+7*"+str(i-1)+" DAY AND timedone < curdate() - INTERVAL DAYOFWEEK(curdate())-1+7*"+str(i-1)+" DAY GROUP BY designer ORDER BY designer DESC")
            for row in c:
                if str(row[0]) <> 'None':
                    personalShare[row[0]][4][i] = float(row[2])
                    reject_DICT.append({'name': str(row[0]) + ' x' + str(row[1]),'y': float(row[2]),'color': empColor[str(row[0])]})
            series9[i+1].append({'name': 'Share', 'data': reject_DICT})
        series9[0] = series9[1]

        #personal score
        for i in range(0,sspWeek):
            for item in personalAvg:
                if personalAvg[item][0][i] <> 0:
                    personalScore[item][4][i] = math.exp((personalAvg[item][0][i]-15)*math.log(0.5)/(historyAvg[0]['SSP'][i]-15))*50 + personalShare[item][0][i] * .5
                    personalScore[item][0][i] = 100 - personalShare[item][4][i]
                if personalAvg[item][1][i] <> 0:
                    personalScore[item][1][i] = math.exp((personalAvg[item][1][i]-60)*math.log(0.5)/(historyAvg[1]['Shading'][i]-60))*50  + personalShare[item][1][i] * .5
                    personalScore[item][0][i] = 100 - personalShare[item][4][i]
                if personalAvg[item][2][i] <> 0:
                    personalScore[item][2][i] = math.exp((personalAvg[item][2][i]-60)*math.log(0.5)/(historyAvg[2]['Design'][i]-60))*50  + personalShare[item][2][i] * .5
                    personalScore[item][0][i] = 100 - personalShare[item][4][i]
                if personalAvg[item][3][i] <> 0:
                    personalScore[item][3][i] = math.exp((personalAvg[item][3][i]-60)*math.log(0.5)/(historyAvg[3]['Finalize/ Change'][i]-60))*50  + personalShare[item][3][i] * .5
                    personalScore[item][0][i] = 100 - personalShare[item][4][i]
                
        series10 = [[]]
        for i in range(0,sspWeek):
            series10.append([])
            for item in personalScore:
                dataScore = [int(personalScore[item][0][i]),int(personalScore[item][1][i]),int(personalScore[item][2][i]),int(personalScore[item][3][i]),int(personalScore[item][4][i])]
                if max(dataScore) != 0:
                    series10[i+1].append({'name':item, 'data': dataScore,'pointPlacement':'on','color': empColor[item]})

        series10[0] = series10[1]

        series11 = [[],[],[],[]]
        for i in range(0,4):
            for item in personalCount:
                if max(personalCount[item][i][0:8]) != 0:
                    series11[i].append({'name':item,'data':personalCount[item][i][0:8][::-1].tolist(),'color': empColor[item]})
        conn.commit()
        c.close()
        conn.close()
        gc.collect()

        # today = datetime.date.today()
        # idx = (today.weekday() + 1) % 7
        # sun = today - datetime.timedelta(7+idx)
        # xs = [(today - datetime.timedelta(7*i+idx)).strftime("%m/%d") for i in range (0,8)]
        return render_template('plottest.html', series=series, series2=series2, series3=series3, series4=series4, series5=series5, series6=series6, series7=series7, series8=series8, series9=series9, series10=series10, series11=series11, historyAvg=historyAvg, urlHome=urlHome)
    except Exception as e:
        return str(e)
        
