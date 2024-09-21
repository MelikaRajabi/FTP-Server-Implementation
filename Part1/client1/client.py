#%% Libraries


# Importing the necessary libraries 
import socket 
import json
import os


#%% Variables


# Setting the host and the control connection port
HOST = '127.0.0.1'
PORT = 20021


#%% Functions


# Receiving the "ls" result from the server and printing it
def lsdata(dataSocket):
    
    result = dataSocket.recv(1048576).decode()
    print(result)


# Receiving the file provided from the server and creating it in the client directory
def getdata(FileName, dataSocket):
    
    FileName = open(os.path.join('.', FileName), 'wb')
    FileInfo = dataSocket.recv(1048576)
    
    FileName.write(FileInfo)
    FileName.close()  
    

# Printing the properties of the transferring file 
# Sending the file to the server
def putdata(FileName, dataSocket):
    
    print(FileName + " " + str(os.path.getsize(FileName)) + "b is being transfered.")
    
    with open(FileName, 'rb') as file:
        dataSocket.sendall(file.read())
        file.close()
        

# Doing the "put" function for each file 
# Receiving the server's response
# Printing the server's response for each file
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
        

# Handling the commands required data connection
def datacontrol(data_json, dataSocket):
    
    command = json.loads(data_json)["Cmd"]
    
    if (command == "LIST"):
        lsdata(dataSocket)
    
    elif (command == "GET"):
        getdata(json.loads(data_json)["FileName"], dataSocket)
        
    elif (command == "PUT"):
        putdata(json.loads(data_json)["FileName"], dataSocket)


# Creating the JSON to send to the server
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
    
    # Creating a socket object 
    # Specifying that the socket will use the IPv4 address family and a TCP connection
    clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    # Connecting to the mentioned host and port
    clientSocket.connect((HOST,PORT))

    while True:
        
        # Getting and processing the user command to create the appropriate JSON
        command = input()
        commands = command.split()
        data_json = client_string(commands)
        # Sending the JSON to the server
        clientSocket.sendall(data_json.encode())
        
        # Receiving the server response and processing it
        data = clientSocket.recv(1024).decode()
        client_json = json.loads(data)
        
        status = client_json["StatusCode"]
        description = client_json["Description"]
        port_number = "0"
        if "DataPort" in client_json:
            port_number = client_json["DataPort"]
        
        # Some exception processings for "quit" command
        if (status == "0" and description == "0"):
            break
        
        # Printing the response
        print(status + " " + description)
        
        # Handling the commands required data connection
        if (port_number != "0"):
            
            # Connecting to the data connection created by the server
            dataSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            dataSocket.connect((HOST,int(port_number)))
            
            if (commands[0] != "mput"):
                # Handling the command
                datacontrol(data_json, dataSocket)
                # Closing the data connection
                dataSocket.close()
                
                # Receiving and processing the server response
                data = clientSocket.recv(1024).decode()
                data_json = json.loads(data)
                status = data_json["StatusCode"]
                description = data_json["Description"] 
                # Printing the response
                print(status + " " + description)
                
            else:
                # Handling the "mput" command
                mputdata(data_json, dataSocket, clientSocket)
                dataSocket.close()
    
    # Closing the control connection
    clientSocket.close()


if __name__ == "__main__":
    main()
    
