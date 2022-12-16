
import numpy as np
import socketserver
import socket
import threading

import socket
import selectors
import random
import cv2
from threading import Thread, enumerate
import base64
import time
import os

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
                length = self.recvall(self.request,64)
                #print(length)
                length = length.decode('utf-8')
                stringData = self.recvall(self.request,int(length))
                data = np.frombuffer(base64.b64decode(stringData), np.uint8)
                frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
                directory = "/home/cilab/Save_Bee_Image"
                cur_time = str(time.time())
                img_name = cur_time
                save_file_name = os.path.join(directory, img_name+".jpg")
                cv2.imwrite(save_file_name, frame)
        except Exception as e:
            print(e)
            print("???")
            pass
    #socket에서 수신한 버퍼를 반환하는 함수
    def recvall(self,sock, count):
        # 바이트 문자열
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
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
