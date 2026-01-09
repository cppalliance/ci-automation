
## Connectivity

- [Windows Instructions](#connect-from-windows)
- [Ubuntu Instructions](#connect-from-ubuntu)

## Connect from Windows

VNC on Windows

Check if chocolatey is already installed. 

```
gcm choco
```

If not, install:  

```
Invoke-WebRequest https://chocolatey.org/install.ps1 -UseBasicParsing | Invoke-Expression
```

Close and re-open the terminal window.

Check if SSH is already installed. 

```
gcm ssh
```

If not, install:  

```
choco install -y openssh
```

If you don't yet have an SSH key: 

```
cd $HOME/.ssh
ssh-keygen
(and follow the prompts, usually pressing 'Enter') 
dir
```

Take note of the SSH key name, to use in the next step.  

Send the .pub ssh key to the administrator to install on the remote workstation.  
You will also need to be provided the remote user's vncpassword and standard password.  

Connect to the remote workstation:

```
ssh -i _my_ssh_key_ -L 5901:localhost:5901 ubuntu@cursor.cpp.al
```

In addition to opening an SSH connection, this creates a tunnel on port 5901.  

VNC OPTION 1: RealVNC

Install RealVNC. Go to https://www.realvnc.com/en/connect/download/viewer/  
Select Windows msi installer.  
Download.  
Install.  
Launch.  

It will ask you to log in to realvnc. This is not necessary, click to proceed, and then on the second or third step, cancel the process.  

Create a new connection.  

Address: 127.0.0.1:5901  
Name: cursor.cpp.al  
Connect.  

VNC OPTION 2: TigerVNC

```
choco install -y tigervnc
tigervnc
```

The executable will be installed at `C:\Program Files (x86)\TigerVNC\vncviewer.exe`. Switch to that folder, run vncviewer.exe and connect to 127.0.0.1:5901. 

## Connect from Ubuntu

VNC on Ubuntu

```
apt-get update
apt-get install remmina
```

If you don't yet have an SSH key: 

```
cd $HOME/.ssh
ssh-keygen
(and follow the prompts, usually pressing 'Enter') 
dir
```

Take note of the SSH key name, to use in the next step.  

Send the .pub ssh key to the administrator to install on the remote workstation.  
You will also need to be provided the remote user's vncpassword and standard password.  

Connect to the remote workstation:

```
ssh -i _my_ssh_key_ -L 5901:localhost:5901 ubuntu@cursor.cpp.al
```

In addition to opening an SSH connection, this creates a tunnel on port 5901.  

Open Remmina. Create a connection.  
Name: cursor  
Server: localhost:5901  
Username: ubuntu  
User password: __



