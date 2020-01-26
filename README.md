# lazybuild
#### a remote compiling tool for GameMaker Studio 2


### What is this?
lazybuild is a Python project allowing the user to create builds of their GMS2 project with a remote machine. For users who need to create builds often, this tool is useful to avoid locking up their computer waiting for a compile to finish, or even allowing non-programmer's on their team to create their own builds as needed.

While intended to be used for distributed builds only, users who have lower-end machines may be able also to use lazybuild to make their testing more efficient by utilizing a powerful remote machine. Please do note, however, that my experiments indicate that the GMS2 compiler does not scale up very well on powerful hardware, and you receive diminishing returns quickly.

### What is supported?
* Both VM and YYC builds
* Git integration to automatically and quickly update the remote server's project files
* SSH / RDP access through the tool's interface
* AWS instance control

### What is not supported?
* Set up for the remote machine (more details below)
* Non-AWS setups
* Non-Windows platforms

### Who is this meant for?
This tool is primarily aimed at professional game developers who would benefit from this efficiency boost, but are also familiar enough with Python and cloud computing to configure lazybuild to their needs. **This tool is not necessarily ready to use "out of the box."** You can not clone this repository, boot up the scripts, and build your project. This repository merely serves as a home for the Python required to make everything happen. **Contributions to extend the behavior of lazybuild out of the box are welcome!**

### How do I get started?
1. First, you need an AWS instance set up and ready to go. The instance should have the following requirements fulfilled:
  * Running Windows 10
  * GameMaker Studio 2 Installed
  * OpenSSH installed and running (server mode) 
2. Next, ensure that your computer has Python 3 and pip installed and configured. Once this finishes, install the needed modules by entering to your terminal:
`pip install -r requirements.txt`
3. Once pip finishes installing your modules, you can start the tool by running:
`python lazybuild.py`
4. Fill out all necessary items for the configuration. lazybuild should prompt you to do this automatically.

### Configuration options

* **region**: The AWS instance's region (ex: `us-east-2`)
* **instanceID**: The unique ID of the AWS instance
* **sshUsername**: The username of the SSH-enabled user on the remote machine
* **sshPassword**: The password of the SSH-enabled user on the remote machine
* **yoyoID**: Your YoYoGames account ID, which you can find as the name of the child folder in `C:\Users\<username>\AppData\Roaming\GameMakerStudio2`. This ID is used to find this exact folder on the remote machine.
* **runtimeVersion**: The runtime version to be built with (must be installed manually on the remote machine already), ex: `2.2.4.374`
* **steamSDKPath**: If needed, the path of the Steam SDK on the remote machine
* **yypPath**: The local path to the desired project's yyp file
* **configuration**: The name off the project configuration to use. If you do not use configurations, use `default`
* **gitUsername**: The username of the Git account to use
* **gitPassword**: The password of the Git account to use
* **gitURL**: The .git URL for your project's repository


### Warnings
lazybuild stores your remote machine's credentials locally as well as your git credentials in a base64 encoded file. This is hardly secure, so only use lazybuild if you feel secure about where you are using it!