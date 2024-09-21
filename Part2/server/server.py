#%% Libraries

import socket
import json
import os
import random
import threading
import subprocess

#%% Variables

HOST = '127.0.0.1'
PORT = 20021

Users = {
            "Melika": {"password" : "123", "root_access" : 0},
            "Melina": {"password" : "456", "root_access" : 0}
        }

connected_clients = []

#%% Functions
  
def root_accessing(conn):
    
    root_access = 0     
    for i in range(len(connected_clients)):
        if (connected_clients[i]["conn"] == conn):
            username = connected_clients[i]["username"]
            break
        
    if username in Users:
        root_access = Users[username]["root_access"]
        
    return root_access
        
def authenticate(username, password, conn):
    
    if (username in Users and Users[username]["password"] == password):
        Users[username]["root_access"] = 1
        status = "230"
        description = "Successfully logged in. Proceed"
    else:
        status = "430"
        description = "Failure in granting root accessibility"
        
    for i in range(len(connected_clients)):
        if (connected_clients[i]["conn"] == conn):
            connected_clients[i]["username"] = username
            break
        
    return status, description

def qt(): 
    status = "0"
    description = "0"
    return status, description
    
def ls(): 
    
    n = len(os.listdir())
        
    if (n == 0):
        status = "210"
        description = "Empty"
        port_number = "0"
    
    else:
        status = "150"
        description = "PORT command successful"
        port_number = str(random.randrange(40000, 50000))
    
    return status, description, port_number
      
def get(FileName): 
    
    found = 0
    with os.scandir() as items:
        for item in items:
            if item.name == FileName:
                found = 1
                break
                
    if (found == 1):
        status = "150"
        description = "OK to send data"
        port_number = str(random.randrange(40000, 50000))
    else:
        status = "550"
        description = "File doesn't exist"
        port_number = "0"
                
    return status, description, port_number

def put(conn): 
    
    root_access = root_accessing(conn)
        
    if (root_access == 1):
        status = "150"
        description = "OK to send data"
        port_number = str(random.randrange(40000, 50000))
    else:
        status = "434"
        description = "The client doesn’t have the root access. File transfer aborted."
        port_number = "0"
        
    return status, description, port_number
 
def delete(FileName, conn): 
    
    root_access = root_accessing(conn)
    
    found = 0
    with os.scandir() as items:
        for item in items:
            if item.name == FileName:
                found = 1
                break
    
    if (root_access == 0):
        status = "434"
        description = "The client doesn’t have the root access."
    elif (found == 0):
        status = "550"
        description = "File doesn't exist"
    else:
        os.remove(FileName)
        status = "200"
        description = "Successfully deleted"
        
    return status, description

def mput(conn):
    
    root_access = root_accessing(conn)
    
    if (root_access == 1):
        status = "150"
        description = "OK to send data"
        port_number = str(random.randrange(40000, 50000))
    else:
        status = "434"
        description = "The client doesn’t have the root access."
        port_number = "0"
        
    return status, description, port_number

def control(data_json, conn):
    
    command = data_json["Cmd"]
    port_number = "0"
    
    if (command == "AUTH"):
        status, description = authenticate(data_json["User"], data_json["Password"], conn)
        
    elif (command == "QUIT"):
        status, description = qt()
        
    elif (command == "LIST"):
        status, description, port_number = ls()
        
    elif (command == "GET"):
        status, description, port_number = get(data_json["FileName"])
        
    elif (command == "PUT"):
        status, description, port_number = put(conn)
        
    elif (command == "DELE"):
        status, description = delete(data_json["FileName"], conn)

    elif (command == "MPUT"):
        status, description, port_number = mput(conn)
        
    return status, description, port_number

def lsdata(dataconn):

    result = subprocess.run("ls -l", capture_output=True, text=True, shell=True).stdout
    dataconn.sendall(result.encode()) 
   
    Status = "226"
    Description = "Directory send OK"
    
    return Status, Description

def getdata(FileName, dataconn):
    
    print(FileName + " " + str(os.path.getsize(FileName)) + "b is being transfered.")

    with open(FileName, 'rb') as file:
        dataconn.sendall(file.read())
        file.close()

    Status = "226"
    Description = "Transfer complete"
    
    return Status, Description

def putdata(FileName, dataconn):
    
    FileName = open(os.path.join('.', FileName), 'wb')
    FileInfo = dataconn.recv(1048576)
    
    FileName.write(FileInfo)
    FileName.close()  

    Status = "226"
    Description = "Transfer complete"
    
    return Status, Description

def mputdata(data_json, dataconn, conn):

    for i in range(len(data_json)-1):
        
        FileName = list(data_json.values())[i+1]
        Status, Description = putdata(FileName, dataconn)
        
        server_json = json.dumps({"FileName" : FileName,
                                  "StatusCode" : Status,
                                  "Description" : Description
                                 })
        conn.sendall(server_json.encode())

def dataControl(data_json, dataconn):
    
    command = data_json["Cmd"]
    
    if (command == "LIST"):
        Status, Description = lsdata(dataconn)
    
    elif (command == "GET"):
        Status, Description = getdata(data_json["FileName"], dataconn)
    
    elif (command == "PUT"):
        Status, Description = putdata(data_json["FileName"], dataconn)
    
    return Status, Description

def server_string(status, description, port_number):
    
    if (port_number == "0"):
        data_json = json.dumps({"StatusCode" : status,
                                "Description" : description
                               })
    else:
        data_json = json.dumps({"StatusCode" : status,
                                "Description" : description,
                                "DataPort" : port_number
                               })
        
    return data_json

#%% Main

def handle_client(conn, addr):
    
    while True:
        
        data = conn.recv(1024).decode()
        data_json = json.loads(data)
        
        status, description, port_number = control(data_json, conn)  
        server_json = server_string(status, description, port_number)
        conn.sendall(server_json.encode())
        
        if (status == "0" and description == "0"):
            break
        
        if (port_number != "0"):
            
            dataSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            dataSocket.bind((HOST,int(port_number)))
            dataSocket.listen()
            dataconn, dataaddr = dataSocket.accept()
            
            if (data_json["Cmd"] != "MPUT"):
                
                Status, Description = dataControl(data_json, dataconn)
                dataSocket.close()
                
                server_json = server_string(Status, Description, "0")
                conn.sendall(server_json.encode())
            
            else:
                mputdata(data_json, dataconn, conn)
                dataSocket.close()

    conn.close()

def main():

    serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    serverSocket.bind((HOST,PORT))
    serverSocket.listen()

    while True:
        
        conn,addr = serverSocket.accept()
        connected_clients.append({"conn" : conn, "username" : "NONE"}) 

        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
    
if __name__ == "__main__":
    main()

