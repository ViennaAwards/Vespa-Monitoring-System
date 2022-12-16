import socket
import pymysql
from datetime import date, timedelta,datetime

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('220.69.240.221', 9000))    # ip주소, 포트번호 지정
server_socket.listen(0)                          # 클라이언트의 연결요청을 기다리는 상태
db = pymysql.connect(host='localhost',port=3306,user='root',passwd='NorthTransilVania',db='VESMO')
cur = db.cursor()

client_socket, addr = server_socket.accept()     # 연결 요청을 수락함. 그러면 아이피주소, 포트등 데이터를 return
#client_socket.sendall("1".encode("utf-8"))
while True:
    data = client_socket.recv(65535)                 # 클라이언트로 부터 데이터를 받음. 출력되는 버퍼 사이즈. (만약 2할 경우, 2개의 데이터만 전송됨)
    data = data.decode()
    print("받은 데이터:", data)             # 받은 데이터를 해석함.
    if(len(data)>0):
        cur.execute("INSERT INTO detect_information_text_version(IP,species,time,client_id) values(%s,%s,%s,%s)",(str(addr[0]),data,str(datetime.now()),"test"))
        db.commit()