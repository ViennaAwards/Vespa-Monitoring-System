from decimal import DivisionByZero
from flask import Flask,render_template,request,session,app,redirect,url_for,flash
import json
import pymysql
import time
import socket
import threading
from flask_paginate import Pagination, get_page_parameter
from flask import jsonify,Markup
from datetime import date, timedelta,datetime
import socket
from threading import Thread, enumerate

app = Flask(__name__)
file_test = []
test = []
app.secret_key= b'aaa!111/'
value = ''
Start = ''
End = ''
old_value = ''
old_Start = ''
old_End = ''
@app.route('/',methods=['GET','POST'])
def main_page():
    return render_template('MainPage_Text_Version.html')

'''@app.route('/submit_test',methods=['GET','POST'])
def submit_test():
    global value
    global Start
    global End
    if request.method == 'POST':
        value = request.form['FPS']
        value = str(value)

        Start = request.form['Start']
        Start = str(Start)

        End = request.form['End']
        End = str(End)
    return render_template('input_send_test.html')'''

@app.route('/monitoring',methods=['GET','POST'])
def monitoring():
    IP = request.args.get('ip')
    return render_template('MainPage_Text_Version.html',IP=IP)

@app.route('/archieve',methods=['GET','POST'])
def archieve():
    IP = request.args.get('ip')
    port = request.args.get('port')
    db = pymysql.connect(host='localhost',port=3306,user='root',passwd='NorthTransilVania',db='VESMO')
    cur = db.cursor()
    ip_list=[]
    species_list=[]
    time_list=[]
    result_list=[]
    try:
        page = request.args.get(get_page_parameter(),type=int,default=1)
        limit=15
        offset = page*limit - limit
        cur.execute("SELECT idx,species,time,IP,client_id FROM detect_information_text_version WHERE IP="+"'"+IP+"'"+"and client_id="+"'"+port+"'")
        res = cur.fetchall()
        length = len(res)
        cur.execute("SELECT IP,species,time FROM detect_information_text_version WHERE IP="+"'"+IP+"'"+"and client_id="+"'"+port+"'"+" ORDER By idx DESC LIMIT %s OFFSET %s",(limit,offset))
        data_list=cur.fetchall()
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE IP="+"'"+IP+"'"+"and client_id="+"'"+port+"'")
        total=cur.fetchall()
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE IP="+"'"+IP+"'"+"and client_id="+"'"+port+"'"+"and species like"+'"'+"black%"+'"')
        black=cur.fetchall()
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE IP="+"'"+IP+"'"+"and client_id="+"'"+port+"'"+"and species like"+'"'+"simil%"+'"')
        simil=cur.fetchall()
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE IP="+"'"+IP+"'"+"and client_id="+"'"+port+"'"+"and species like"+'"'+"crabro%"+'"')
        crabro=cur.fetchall()
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE IP="+"'"+IP+"'"+"and client_id="+"'"+port+"'"+"and species like"+'"'+"ggoma%"+'"')
        ggoma=cur.fetchall()
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE IP="+"'"+IP+"'"+"and client_id="+"'"+port+"'"+"and species like"+'"'+"jangsu%"+'"')
        jangsu=cur.fetchall()
        db.commit()
        pagination = Pagination (page=page,per_page=limit,total=length)
        int(total[0][0])
    finally:
        db.close()
    return render_template('details.html',IP=IP,pagination=pagination,result_list=data_list,total_num=list(total)[0],black_num=list(black)[0],simil_num=list(simil)[0],crabro_num=list(crabro)[0],ggoma_num=list(ggoma)[0],jangsu_num=list(jangsu)[0],total_ratio=100.0,black_ratio=round((int(black[0][0])/int(total[0][0]))*100,2),simil_ratio=round((int(simil[0][0])/int(total[0][0]))*100,2),crabro_ratio=round((int(crabro[0][0])/int(total[0][0]))*100,2),ggoma_ratio=round((int(ggoma[0][0])/int(total[0][0]))*100,2),jangsu_ratio=round((int(jangsu[0][0])/int(total[0][0]))*100,2))

@app.route('/loaddata_IP', methods=['POST'])
def loaddata_IP():
    post_data_list = []
    Address_list = []
    db = pymysql.connect(host='localhost',port=3306,user='root',passwd='NorthTransilVania',db='VESMO')
    cur = db.cursor()
    try:
        cur.execute("select IP from detect_information_text_version group by IP having count(IP)>0")
        IP_list=cur.fetchall()
        db.commit()
        IP_list = list(IP_list)
        for i in range (len(IP_list)):
            cur.execute("SELECT idx,species,time,IP,client_id from detect_information_text_version where IP='"+IP_list[i][0]+"'ORDER BY idx DESC limit 1;")
            data = cur.fetchall()
            data_list = list(data[0])
            cur.execute("SELECT IP FROM detect_information_text_version WHERE IP='" + IP_list[i][0]+"'")
            Address=cur.fetchall()
            Address = list(Address[0])
            Address_list.append(Address)
            db.commit()
            post_data_list.append(data_list)
        post_data_list.insert(0,Address_list)
        post_data_list.insert(0,len(IP_list))
        db.commit()
        post_data_list.append(socket.gethostbyname(socket.gethostname()))
        #print(post_data_list)
        data= tuple(post_data_list)

        jsondata=json.dumps(data)
        
        return jsondata
    finally:
        db.close()

@app.route('/IPlist', methods=['POST'])
def IPlist():
    db = pymysql.connect(host='localhost',port=3306,user='root',passwd='NorthTransilVania',db='VESMO')
    cur = db.cursor()
    try:
        cur.execute("select IP from detect_information_text_version group by IP having COUNT(IP)>0")
        data_list=cur.fetchall()
        data = list(data_list)
        data.insert(0,len(data))
        data_list = tuple(data)
        db.commit()
        jsondata=json.dumps(data_list)
        return jsondata
    finally:
        db.close()

@app.route('/loaddata',methods=['POST'])
def loaddata():
    db = pymysql.connect(host='localhost',port=3306,user='root',passwd='NorthTransilVania',db='VESMO')
    cur = db.cursor()
    load_data_list = []
    try:
        data = request.get_json()
        IP = data.get("IP")
        
        cur.execute("SELECT IP FROM detect_information_text_version WHERE IP=" + IP)
        Address_list=cur.fetchall()
        Address_list = list(Address_list[0])
        db.commit()
        
        cur.execute("select client_id from detect_information_text_version WHERE IP ="+IP+"group by client_id having client_id>0")
        port_list = cur.fetchall()
        port_list = list(port_list)
        port_count = len(port_list)
        db.commit()
        for i in range(port_count):
            cur.execute("SELECT idx,species,time,IP,client_id from detect_information_text_version where IP="+IP+"and client_id="+"'"+port_list[i][0]+"'"+"ORDER BY idx DESC limit 1;")
            data_list = cur.fetchall()
            load_data_list.append(list(data_list[0]))
        data = load_data_list
        data.insert(0,port_count)
        data.insert(1,Address_list[0])
        data_list = tuple(data)
        jsondata=json.dumps(data_list)
        return jsondata
    finally:
        db.close()
    
@app.route('/loaddata2',methods=['POST'])
def loaddata2():
    db = pymysql.connect(host='localhost',port=3306,user='root',passwd='NorthTransilVania',db='VESMO')
    cur = db.cursor()
    load_data_list = []
    try:
        data = request.get_json()
        #print(data)
        IP = data.get("IP")
        print(IP)
        cur.execute("SELECT IP FROM detect_information_text_version WHERE IP=" + IP)
        Address_list=cur.fetchall()
        Address_list = list(Address_list[0])
        db.commit()
        cur.execute("select client_id from detect_information_text_version WHERE IP ="+IP+"group by client_id having client_id>0")
        port_list = cur.fetchall()
        port_list = list(port_list)
        port_count = len(port_list)
        db.commit()
        for i in range(port_count):
            cur.execute("SELECT idx,species,time,IP,client_id from detect_information_text_version where IP="+IP+"and client_id="+"'"+port_list[i][0]+"'"+"ORDER BY idx DESC limit 1;")
            data_list = cur.fetchall()
            load_data_list.append(list(data_list[0]))
        data = load_data_list
        data.insert(0,port_count)
        data.insert(1,Address_list[0])
        data_list = tuple(data)
        jsondata=json.dumps(data_list)
        return jsondata
    finally:
        db.close()

@app.route('/change_species', methods=['POST'])
def change_species():
    date_detection=[]
    species = request.form['Species']
    if len(species)<=0:
        species = "apis"
    db = pymysql.connect(host='localhost',port=3306,user='root',passwd='NorthTransilVania',db='VESMO')
    cur = db.cursor()
    try:
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
        date = str(year)+'_'+str(month)+'_'+str(day)
        #print(date)
        #print(species)
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE species="+"'"+species+"'"+" AND "+ "time like"+"'"+date+"%'")
        today_num=cur.fetchall()

        date = str(year)+'_'+str(month)+'_'+str(day-1)
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE species="+"'"+species+"'"+" AND "+ "time like"+"'"+date+"%'")
        Day1_Ago_num=cur.fetchall()

        date = str(year)+'_'+str(month)+'_'+str(day-2)
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE species="+"'"+species+"'"+" AND "+ "time like"+"'"+date+"%'")
        Day2_Ago_num=cur.fetchall()

        date = str(year)+'_'+str(month)+'_'+str(day-3)
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE species="+"'"+species+"'"+" AND "+ "time like"+"'"+date+"%'")
        Day3_Ago_num=cur.fetchall()

        date = str(year)+'_'+str(month)+'_'+str(day-4)
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE species="+"'"+species+"'"+" AND "+ "time like"+"'"+date+"%'")
        Day4_Ago_num=cur.fetchall()
        
        date_detection.append(int(today_num[0][0]))
        date_detection.append(int(Day1_Ago_num[0][0]))
        date_detection.append(int(Day2_Ago_num[0][0]))
        date_detection.append(int(Day3_Ago_num[0][0]))
        date_detection.append(int(Day4_Ago_num[0][0]))

        data= tuple(date_detection)

        jsondata=json.dumps(data)
        
        return jsondata
    finally:
        db.close()
 
@app.route('/chart', methods=['GET','POST'])
def chart():
    date_detection=[]
    species_detection=[]
    db = pymysql.connect(host='localhost',port=3306,user='root',passwd='NorthTransilVania',db='VESMO')
    cur = db.cursor()
    try:
        black_num=0
        simil_num=0
        crabro_num=0
        ggoma_num=0
        jangsu_num=0
        now = datetime.now()
        yesterday = datetime.today() - timedelta(1)
        Day2_Ago = datetime.today() - timedelta(2)
        Day3_Ago = datetime.today() - timedelta(3)
        Day4_Ago = datetime.today() - timedelta(4)
        date = now.strftime('%Y-%m-%d')
        query = "SELECT COUNT(idx) FROM detect_information_text_version WHERE time like"+"'"+date+"%'"
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE time like"+"'"+date+"%'")
        today_num=cur.fetchall()

        date = yesterday.strftime('%Y-%m-%d')
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE time like"+"'"+date+"%'")
        Day1_Ago_num=cur.fetchall()

        date = Day2_Ago.strftime('%Y-%m-%d')
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE time like"+"'"+date+"%'")
        Day2_Ago_num=cur.fetchall()

        date = Day3_Ago.strftime('%Y-%m-%d')
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE time like"+"'"+date+"%'")
        Day3_Ago_num=cur.fetchall()

        date = Day4_Ago.strftime('%Y-%m-%d')
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE time like"+"'"+date+"%'")
        Day4_Ago_num=cur.fetchall()
        
        cur.execute("select IP from detect_information_text_version group by IP having COUNT(IP)>0")
        IP_list=cur.fetchall()
        print(IP_list)

        current_time = now.strftime('%Y-%m-%d-%h-%m-%s')
        last_time = Day4_Ago.strftime('%Y-%m-%d-%h-%m-%s')
        cur.execute("SELECT species FROM detect_information_text_version Where time<="+"'"+current_time+"'"+"and time>="+"'"+last_time+"'")
        species=cur.fetchall()
        for species in list(species):
            for species in list(species):
                black_num = black_num+species.count('black')
                simil_num = simil_num+species.count('simil')
                crabro_num = crabro_num+species.count('crabro')
                ggoma_num = ggoma_num+species.count('ggoma')
                jangsu_num = jangsu_num+species.count('jangsu')
        '''cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE species="+'"'+"black"+'"')
        black=cur.fetchall()
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE species="+'"'+"simil"+'"')
        simil=cur.fetchall()
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE species="+'"'+"crabro"+'"')
        crabro=cur.fetchall()
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE species="+'"'+"ggoma"+'"')
        ggoma=cur.fetchall()
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE species="+'"'+"jangsu"+'"')
        jangsu=cur.fetchall()'''

        db.commit()
        IP_list = list(IP_list)

        species_detection.append(black_num)
        species_detection.append(simil_num)
        species_detection.append(crabro_num)
        species_detection.append(ggoma_num)
        species_detection.append(jangsu_num)

        date_detection.append(int(today_num[0][0]))
        date_detection.append(int(Day1_Ago_num[0][0]))
        date_detection.append(int(Day2_Ago_num[0][0]))
        date_detection.append(int(Day3_Ago_num[0][0]))
        date_detection.append(int(Day4_Ago_num[0][0]))
    finally:
        db.close()
    return render_template('chart.html',Today=list(today_num[0]),Day1_Ago=list(Day1_Ago_num[0]),Day2_Ago=list(Day2_Ago_num[0]),Day3_Ago=list(Day3_Ago_num[0]),Day4_Ago=list(Day4_Ago_num[0]),date_detection_num=date_detection,IP_list=IP_list[0],species_detection=species_detection)

@app.route('/location_name', methods=['POST'])
def location_name():
    date_detection=[]
    species_detection=[]
    db = pymysql.connect(host='localhost',port=3306,user='root',passwd='NorthTransilVania',db='VESMO')
    cur = db.cursor()
    data = request.get_json()
    try:
        black_num=0
        simil_num=0
        crabro_num=0
        ggoma_num=0
        jangsu_num=0
        now = datetime.now()
        yesterday = datetime.today() - timedelta(1)
        Day2_Ago = datetime.today() - timedelta(2)
        Day3_Ago = datetime.today() - timedelta(3)
        Day4_Ago = datetime.today() - timedelta(4)
        date = now.strftime('%Y-%m-%d')
        sql = "SELECT COUNT(idx) FROM detect_information_text_version WHERE location= "+"'"+data['location_name']+"' and "+"time like"+"'"+date+"%'"
        print(sql)
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE location= "+"'"+data['location_name']+"' and "+"time like"+"'"+date+"%'")
        today_num=cur.fetchall()

        date = yesterday.strftime('%Y-%m-%d')
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE location= "+"'"+data['location_name']+"' and "+"time like"+"'"+date+"%'")
        Day1_Ago_num=cur.fetchall()

        date = Day2_Ago.strftime('%Y-%m-%d')
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE location= "+"'"+data['location_name']+"' and "+"time like"+"'"+date+"%'")
        Day2_Ago_num=cur.fetchall()

        date = Day3_Ago.strftime('%Y-%m-%d')
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE location= "+"'"+data['location_name']+"' and "+"time like"+"'"+date+"%'")
        Day3_Ago_num=cur.fetchall()

        date = Day4_Ago.strftime('%Y-%m-%d')
        cur.execute("SELECT COUNT(idx) FROM detect_information_text_version WHERE location= "+"'"+data['location_name']+"' and "+"time like"+"'"+date+"%'")
        Day4_Ago_num=cur.fetchall()

        current_time = now.strftime('%Y-%m-%d-%h-%m-%s')
        last_time = Day4_Ago.strftime('%Y-%m-%d-%h-%m-%s')
        cur.execute("SELECT species FROM detect_information_text_version Where time<="+"'"+current_time+"'"+"and time>="+"'"+last_time+"'")
        species=cur.fetchall()
        for species in list(species):
            for species in list(species):
                black_num = black_num+species.count('black')
                simil_num = simil_num+species.count('simil')
                crabro_num = crabro_num+species.count('crabro')
                ggoma_num = ggoma_num+species.count('ggoma')
                jangsu_num = jangsu_num+species.count('jangsu')
        
        species_detection.append(black_num)
        species_detection.append(simil_num)
        species_detection.append(crabro_num)
        species_detection.append(ggoma_num)
        species_detection.append(jangsu_num)
        species_data = tuple(species_detection)
        date_detection.append(int(today_num[0][0]))
        date_detection.append(int(Day1_Ago_num[0][0]))
        date_detection.append(int(Day2_Ago_num[0][0]))
        date_detection.append(int(Day3_Ago_num[0][0]))
        date_detection.append(int(Day4_Ago_num[0][0]))
        data= tuple(date_detection)
        data = data+species_data
        print(data)
        jsondata=json.dumps(data)
        return jsondata
    finally:
        db.close()

'''def run():
    app.run(host='0.0.0.0',port=12000,threaded=True)'''

'''def Send_Client():
    global value
    global old_value
    global Start
    global End
    global old_Start
    global old_End
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('220.69.240.221', 9000))    # ip주소, 포트번호 지정
    server_socket.listen(0)                          # 클라이언트의 연결요청을 기다리는 상태

    client_socket, addr = server_socket.accept()     # 연결 요청을 수락함. 그러면 아이피주소, 포트등 데이터를 return
    while True:
        if old_value!=value or old_Start!=Start or old_End!=End:

            value = "Speed:"+value
            Time = "Start:"+Start+"/"+"End:"+End

            print(value)
            print(Time)
            

            client_socket.sendall(value.encode(encoding='utf-8'))
            client_socket.sendall(Time.encode(encoding='utf-8'))
            #client_socket.sendall(End.encode(encoding='utf-8'))
            old_value = value
            old_Start = Start
            old_End = End'''

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=12000,threaded=True)
    #Thread(target=delete_table,args=()).start()
    #Thread(target=run,args=()).start()
    #Thread(target=Send_Client,args=()).start()
