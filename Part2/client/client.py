#%% Libraries

import socket 
import json
import os

#%% Variables

HOST = '127.0.0.1'
PORT = 20021

#%% Functions

def lsdata(dataSocket):
    
    result = dataSocket.recv(1048576).decode()
    print(result)

def getdata(FileName, dataSocket):
    
    FileName = open(os.path.join('.', FileName), 'wb')
    FileInfo = dataSocket.recv(1048576)
    
    FileName.write(FileInfo)
    FileName.close()  
    
def putdata(FileName, dataSocket):
    
    print(FileName + " " + str(os.path.getsize(FileName)) + "b is being transfered.")
    
    with open(FileName, 'rb') as file:
        dataSocket.sendall(file.read())
        file.close()
             
def mputdata(data_json, dataSocket, clientSocket):

    data_json = json.loads(data_json)
    for i in range(len(data_json)-1):
        
        FileName = list(data_json.values())[i+1]
        putdata(FileName, dataSocket)
        
        clientdata = clientSocket.recv(1024).decode()
        client_json = json.loads(clientdata)
        
        filename = client_json["FileName"] 
        status = client_json["StatusCode"]
        description = client_json["Description"]        
        print(filename + " " + status + " " + description)
                   
def datacontrol(data_json, dataSocket):
    
    command = json.loads(data_json)["Cmd"]
    
    if (command == "LIST"):
        lsdata(dataSocket)
    
    elif (command == "GET"):
        getdata(json.loads(data_json)["FileName"], dataSocket)
        
    elif (command == "PUT"):
        putdata(json.loads(data_json)["FileName"], dataSocket)

def client_string(commands):
    
    if (commands[0] == "ath"):
        data_json = json.dumps({"Cmd" : "AUTH",
                                "User" : commands[1],
                                "Password" : commands[2]
                                })
        
    elif (commands[0] == "quit"):
        data_json = json.dumps({"Cmd" : "QUIT"})
        
    elif (commands[0] == "ls"):
        data_json = json.dumps({"Cmd" : "LIST"})
        
    elif (commands[0] == "get"):
        data_json = json.dumps({"Cmd" : "GET",
                                "FileName" : commands[1]
                                })
        
    elif (commands[0] == "put"):
        data_json = json.dumps({"Cmd" : "PUT",
                                "FileName" : commands[1]
                                })
        
    elif (commands[0] == "delete"):
        data_json = json.dumps({"Cmd" : "DELE",
                                "FileName" : commands[1]
                                })
        
    elif (commands[0] == "mput"):
        
        output = {"Cmd" : "MPUT"}
        for i in range(len(commands)-1):
            key = "FileName_" + str(i+1)
            if (i == 0):
                output[key] = commands[i+1]
            else:
                output[key] = commands[i+1][1:]
        
        data_json = json.dumps(output) 

    return data_json

#%% Main

def main():
    
    clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    clientSocket.connect((HOST,PORT))

    while True:
    
        command = input()
        commands = command.split()
        data_json = client_string(commands)
        clientSocket.sendall(data_json.encode())
        
        data = clientSocket.recv(1024).decode()
        client_json = json.loads(data)
        
        status = client_json["StatusCode"]
        description = client_json["Description"]
        port_number = "0"
        if "DataPort" in client_json:
            port_number = client_json["DataPort"]
        
        if (status == "0" and description == "0"):
            break
        
        print(status + " " + description)
        
        if (port_number != "0"):
            
            dataSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            dataSocket.connect((HOST,int(port_number)))
            
            if (commands[0] != "mput"):
                datacontrol(data_json, dataSocket)
                dataSocket.close()
                
                data = clientSocket.recv(1024).decode()
                data_json = json.loads(data)
                status = data_json["StatusCode"]
                description = data_json["Description"]        
                print(status + " " + description)
                
            else:
                mputdata(data_json, dataSocket, clientSocket)
                dataSocket.close()
                
    clientSocket.close()

if __name__ == "__main__":
    main()
    
