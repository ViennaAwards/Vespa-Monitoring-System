import numpy as np
import socketserver
import socket
import threading
import re
import socket
import selectors
import random
import cv2
from threading import Thread, enumerate
import base64
import time
import os
import pymysql
from datetime import date, timedelta,datetime
from collections import deque

db = pymysql.connect(host='localhost',port=3306,user='root',passwd='NorthTransilVania',db='VESMO')
cur = db.cursor()
info_queue = deque()

def insert_data():
    while True:
        if(len(info_queue)>0):
            #print(info_queue)
            info = info_queue.popleft()
            print(info)
            cur.execute("INSERT INTO detect_information_text_version(IP,species,time,client_id) values(%s,%s,%s,%s)",(info[0],info[1],info[2],info[3].replace("\x00","")))
            db.commit()

class Cserver():

    def __init__(self):
        self.users={}
    
    def add(self,username,conn,addr):
        lock.acquire()
        self.users[username]=(conn,addr)
        lock.release()
        self.sendMessageToAll('[%s] Enter'%username)
        print('사용자수:[%d]'%len(self.users))

        return username

    def remove(self,username):
        lock.acquire()
        del self.users[username]
        lock.release()
        print(len(self.users))

    def messagehandle(self,username,msg):
        if msg.strip() == '\quit':
            self.remove(username)
            return -1
        else:
            self.sendall(msg)

    def sendMessageToAll(self,msg):
        for conn,addr in self.users.values():
            conn.send(msg.encode())

class TcpHandle(socketserver.BaseRequestHandler):
    user = Cserver()
    def handle(self):
        print("Connect")
        try:
            while True:
                data = self.recvall(self.request,65535)                 # 클라이언트로 부터 데이터를 받음. 출력되는 버퍼 사이즈. (만약 2할 경우, 2개의 데이터만 전송됨)
                data = data.decode()
                if(len(data)>0):
                    #print(data)
                    info_queue.append([str(self.client_address[0]),data.split("/")[0],str(datetime.now()),data.split("/")[1].replace("\n","")])
                    #print("받은 데이터:", data.split("/")[0], "받은 ID:", data.split("/")[1].replace("\n",""),"IP:",self.client_address[0])             # 받은 데이터를 해석함.
                    #cur.execute("INSERT INTO detect_information_text_version(IP,species,time,client_id) values(%s,%s,%s,%s)",(str(self.client_address[0]),data.split("/")[0],str(datetime.now()),data.split("/")[1].replace("\n","")))
                    #db.commit()
                #self.socket.listen(1)
        except Exception as e:
            print(e)
            print("???")
            pass

    def recvall(self,sock, count):
        # 바이트 문자열
        buf = b''
        buf = sock.recv(count)
        return buf

class MultiServer(socketserver.ThreadingMixIn,socketserver.TCPServer):
    pass
     
def runServer():
    try:
        global server
        server=MultiServer(('220.69.240.221',9000),TcpHandle)
        server.serve_forever()
    except KeyboardInterrupt:
        print('Exit')
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    print("Start")
    Thread(target=runServer,args=()).start()
    Thread(target=insert_data,args=()).start()