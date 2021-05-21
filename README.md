# SafePasta KitchenGuard

## Description
This repository contains the SafePasta KitchenGuard project. <br>

## Prerequisites 
The files in /src are meant to run on a RaspberryPi 4. The files in the /NodeJS contain the server files and are meant to run on another computer. We tested it on machines running Windows 10
and Ubuntu 20.4. The PC with the server and the RaspberryPi must both be connected to the same local network. <br>

It is assumed that the tutorials have been followed so that the RaspeberryPi is configured with an MQTT broker, Z2M Python 3 etc. It is also assumed that the a potential users have the physical devices used in these tutorials.


## Installation Guide PC

Before following this guide make sure that, mosquitto, MySQL and NodeJS are installed on your PC. It is important that mosquitto is installed as a service that runs in the background. Also if mosqitto is installed as version 2.0 or higher it block connection from unauthenticated devices. The easy way is to install an older version, which can be found with this link https://mosquitto.org/files/binary/. However, this may also be changed in the mosquitto configuration file. 

Extract the /NodeJS folder from this github repository. 

Open a terminal window and navigate to the extracted /NodeJS folder, and run npm install:

```console
>cd .../NodeJS
>npm install
```
This should install all required node modules, however, this may not always be the case. If a node modeule is missing this will be shown in the terminal when we try to start the server later. <br>

Now we want to setup the database. In this guide we will do it via the terminal. Make sure that you've added MySQL to your system PATH and open a new terminal window. Enter the following commands:

```console
>mysql -u root -p
```

Put your password to login as root user.

Now when you are logged into MySQL insert following commands one by one:

```sql
mysql> CREATE DATABASE kitchenguard;
mysql> USE kitchenguard;
mysql> CREATE TABLE kitchenguard(  
        start text,  
        stop text,  
        frq text,  
        time_total text
);
```

Now the database should be up and running. 

Now you want to open the SPWebServer.js file with an IDE. In line 27 you want to change the password to the password you use for the root user. 

```javascript
/*
! get connection to our DB
*/
function getConnection(){
  return mysql.createConnection({
    multipleStatements: true,
    host: 'localhost',
    port: '3306',
    user: 'root',
    password: 'CHANGE_PASSWORD_HERE',
    database: 'kitchenguard'
  });
}
```

Now it is time to start the server. Navigate to the /NodeJS folder and type in the following commands:

```console
>cd .../NodeJS
>npm i nodemon -g
>npm i mqtt
>npm i ejs
>nodemon SPWebServer.js
```

This will install a few required packages, and run the server. You should be able to connect to it in the browser with the url: 

```console
127.0.0.1:3000
```

## Installation Guide RaspberryPi

To download project, open a console and run:

```console
example@pi:~$ git clone https://github.com/MaltheT/KitchenGuard.git
```
The number of physical devices may vary, but the friendly names should be LED1, LED2, ... LEDn and PIR1, PIR2, ... PIRn. The power sensor should be named NEO. In the file /opt/zigbee/data/configuration.yaml there are fields for friendly names of known zigbee devices. Change these names with any text editor. Example of how this could be done: 

```console
example@pi:~$ cd /opt/zigbee/data
example@pi:~$ sudo nano configuration.yaml
```
The local IPv4 address for the host running server should be known. To do this go the machine running the server. On Windows one can learn this address by opening a console and running 
```console
C:\Users\ServerMachine>ipconfig
```
This command outputs a lot of text. We are looking for the line specifying IPv4 address.

If server is running on Linux machine do following in a console:
```console
example@pi:~$ hostname -I
```

Line 18 of SPControllerStateMachine.py must use this address.If the address is xxx.xxx.xxx.xxx change this file to look like this:   
```python
def __init__(self):
        self.client = SPmqttClient("xxx.xxx.xxx.xxx", 1883)
        ...
```

The last thing to do is installing the transitions and DateTime libraries
```console
example@pi:~$ pip3 install transitions 
```

The RaspberryPi should now be configured to run the SafePasta KitchenGuard system. To run it open a terminal and issue:

```console
example@pi:~$ cd /opt/zigbee && npm start
```
In another terminal window run: 
```console
example@pi:~$ cd KitchenGuard/src
example@pi:~$ python3 SPMain.py
```
