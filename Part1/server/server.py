#%% Libraries


# Importing the necessary libraries 
import socket
import json
import os
import random
import threading
import subprocess


#%% Variables


# Setting the host and the control connection port
HOST = '127.0.0.1'
PORT = 20021

# Setting the usernames and passwords and their corresponding permissions
Users = {
            "Melika": {"password" : "123", "root_access" : 0},
            "Melina": {"password" : "456", "root_access" : 0}
        }

# Storing the connected ids
connected_clients = []
 

#%% Functions
  

# Returning the permission based on the username and its corresponding connection id
def root_accessing(conn):
    
    root_access = 0     
    for i in range(len(connected_clients)):
        if (connected_clients[i]["conn"] == conn):
            username = connected_clients[i]["username"]
            break
        
    if username in Users:
        root_access = Users[username]["root_access"]
        
    return root_access
        

# Authenticating based on the username and password provided 
# Updating the connection ids and usernames
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


# Indicating the exit command
def qt(): 
    status = "0"
    description = "0"
    return status, description


# Returning the appropriate status code, description, and port number if required based on the number of files 
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
    

# Returning the appropriate status code, description, and port number if required based on the existance of the file provided 
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


# Returning the appropriate status code, description, and port number if required based on the permission of the connection id 
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

        
# Returning the appropriate status code, description, and port number if required based on the existance of the file provided and the permission of the connection id 
# Removing the file if required
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


# Returning the appropriate status code, description, and port number if required based on the permission of the connection id  
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


# Handling the command primarily
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


# Listing the files in the directory of the server 
# Sending the result to the client
def lsdata(dataconn):

    result = subprocess.run("ls -l", capture_output=True, text=True, shell=True).stdout
    dataconn.sendall(result.encode()) 
   
    Status = "226"
    Description = "Directory send OK"
    
    return Status, Description


# Printing the properties of the transferring file
# Sending the content of the file provided to the client
def getdata(FileName, dataconn):
    
    print(FileName + " " + str(os.path.getsize(FileName)) + "b is being transfered.")

    with open(FileName, 'rb') as file:
        dataconn.sendall(file.read())
        file.close()

    Status = "226"
    Description = "Transfer complete"
    
    return Status, Description


# Receiving the content of the file provided from the client and creating the file in the server directory
def putdata(FileName, dataconn):
    
    FileName = open(os.path.join('.', FileName), 'wb')
    FileInfo = dataconn.recv(1048576)
    
    FileName.write(FileInfo)
    FileName.close()  

    Status = "226"
    Description = "Transfer complete"
    
    return Status, Description


# Doing the "put" function for each file 
def mputdata(data_json, dataconn, conn):

    for i in range(len(data_json)-1):
        
        FileName = list(data_json.values())[i+1]
        Status, Description = putdata(FileName, dataconn)
        
        server_json = json.dumps({"FileName" : FileName,
                                  "StatusCode" : Status,
                                  "Description" : Description
                                 })
        conn.sendall(server_json.encode())
    

# Handling the commands required data connection 
def dataControl(data_json, dataconn):
    
    command = data_json["Cmd"]
    
    if (command == "LIST"):
        Status, Description = lsdata(dataconn)
    
    elif (command == "GET"):
        Status, Description = getdata(data_json["FileName"], dataconn)
    
    elif (command == "PUT"):
        Status, Description = putdata(data_json["FileName"], dataconn)
    
    return Status, Description
        

# Creating the JSON 
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
        
        # Receiving the content from the client
        data = conn.recv(1024).decode()
        # Loading the JSON 
        data_json = json.loads(data)
        
        # Handling the content 
        status, description, port_number = control(data_json, conn)  
        # Creating the response JSON
        server_json = server_string(status, description, port_number)
        # Sending the response to the client
        conn.sendall(server_json.encode())
        
        # Some exception processings for "quit" command
        if (status == "0" and description == "0"):
            break
        
        # Handling commands required data connection
        if (port_number != "0"):
            
            # Creating the data connection
            dataSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            dataSocket.bind((HOST,int(port_number)))
            dataSocket.listen()
            dataconn, dataaddr = dataSocket.accept()
            
            if (data_json["Cmd"] != "MPUT"):
                
                # Handling the commands secondly
                Status, Description = dataControl(data_json, dataconn)
                # Closing the data connection
                dataSocket.close()
                
                # Creating the response and Sending it to the client
                server_json = server_string(Status, Description, "0")
                conn.sendall(server_json.encode())
            
            else:
                # Handling the "mput" command
                mputdata(data_json, dataconn, conn)
                dataSocket.close()
    
    # Closing the control connection
    conn.close()


def main():
    
    # Creating a socket object 
    # Specifying that the socket will use the IPv4 address family and a TCP connection
    serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    # Binding the socket to the specified host and port
    serverSocket.bind((HOST,PORT))
    # Starting to listen for incoming connections until a client connects
    serverSocket.listen()

    while True:
        
        # Returning a new socket object that represents the connection with the client and the address of the client that connected
        conn,addr = serverSocket.accept()
        # Updating the "connected_clients" list
        connected_clients.append({"conn" : conn, "username" : "NONE"}) 
        
        # Creating the thread object with appropriate target and inputs
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        # Starting the task
        thread.start()
    
    
if __name__ == "__main__":
    main()

