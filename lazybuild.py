"""lazybuild: a remote compiling tool for GameMaker Studio 2"""

# Import libraries
import sys
import os
import subprocess
import json 
import time
import getpass
import base64
import aws
import ssh
import gmBuilder
from termcolor import colored
import colorama
colorama.init()

__author__ = "Gabe Weiner"
__license__ = "MIT"
__version__ = "1.0.1"
__maintainer__ = "Gabe Weiner"
__email__ = "imlazyeye (at) gmail.com"
__status__ = "Prototype"

class LazyBuild:

  def __init__(self):
    
    # Core data
    print('Loading user defined options...')
    self._configurationKeys = ['region', 'instanceID', 'sshUsername', 'sshPassword', 'yoyoID', 'runtimeVersion', 'steamSDKPath', 'yypPath', 'configuration', 'gitUsername', 'gitPassword', 'gitBranch', 'gitURL']
    try:
      self.config = self.LoadConfig()
    except:
      print(colored('Configure options were not found. Please set them now!', 'yellow'))
      self.config = {}
      for key in self._configurationKeys:
        self.config[key] = ''
      self.Configure()
    print('Checking SSH permission file...')
    self.sshKeyFilePath = './resources/misc/rsa.pem'
    if not os.path.exists(self.sshKeyFilePath):
      print(colored('SSH permission file not found. Please refer to the README!', 'red'))
      sys.exit()
    print('Initializing...')
    self.region = self.config['region']
    self.instanceID = self.config['instanceID']
    self.sshUsername = self.config['sshUsername']
    self.sshPassword = self.config['sshPassword']
    self.shutdownOnDestroy = True
    self.inputCommands = {
      'configure': 'Configure the needed options for lazybuild',
      'status': 'Check if the remote server is online',
      'startup': 'Starts the remote server',  
      'shutdown': 'Shuts down the remote server',
      'build': 'Builds the project on the remote server',
      'console': 'Connects you to your instance via SSH',
      'rdp': 'Starts a remote desktop session with the remote server',
      'help': 'Prints these commands again',
      'exit': 'Exits this program'
    }
    print('Fetching instance...')
    try:
      self.builderInstance = aws.AWSInstance(self.region, self.instanceID, self.shutdownOnDestroy)
    except:
      print(colored('There was an issue trying to access your remote machine!', 'red'))
      if self.YesNoPrompt('Would you like to edit your configuration options?'):
        self.Configure()
        print('Please start lazybuild again to apply these changes.')
      sys.exit()

    # Welcome message
    asciiMessage = r'''
-------------------------------------------------

      _                 _           _ _     _ 
    | |               | |         (_) |   | |
    | | __ _ _____   _| |__  _   _ _| | __| |
    | |/ _` |_  / | | | '_ \| | | | | |/ _` |
    | | (_| |/ /| |_| | |_) | |_| | | | (_| |
    |_|\__,_/___|\__, |_.__/ \__,_|_|_|\__,_|
                  __/ |                      
                  |___/                       
-------------------------------------------------
    '''
    print(colored(asciiMessage, 'green'))
    welcomeMessage = f'''Welcome to lazybuild! You are running version {__VERSION__}

Please ensure you have read the README file before continuing!

Available commands:
    '''
    print(welcomeMessage)
    self.Help()

  def YesNoPrompt(self, message):
    resp = input(f'{message} [y/n] ')
    if (resp =='y'):
      return True 
    elif (resp == 'n'):
      return False 
    else:
      print(colored('Response invalid! Please use either "y" or "n".', 'yellow'))
      return self.YesNoPrompt(message)

  def Help(self):
    commands = ''
    for key, value in self.inputCommands.items():
      name = colored(key, 'cyan')
      commands += f'{name}: {value}\n'
    print(commands)

  def SaveConfig(self): # I just don't wanna save passwords in plaintext, man
    print('Saving configuration...')
    open('lazybuildConfig.dat', 'wb').write(base64.b64encode(json.dumps(self.config).encode('utf-8')))

  def LoadConfig(self):
    print('Opening configuration...')
    text = open('lazybuildConfig.dat', 'rb').read()
    return json.loads(base64.decodebytes(text))

  def ReadUserInput(self):
    commandToRun = input('>> ')
    try:
      self.inputCommands[commandToRun] # ensures this is an allowed function call
      getattr(self, commandToRun.capitalize())()
    except KeyError:
      print(colored('Command not recognized! Please try again.', 'yellow'))
      return

  def Configure(self):
    def InputHandle(key):
      currentValueString = '[]'
      if self.config[key] != '':
        currentValueString = f'[{self.config[key]}]'
      message = '{:<30}'.format(f'{key} {currentValueString}:')
      if 'password' in key.lower():
        resp = getpass.getpass(message)
      else:
        resp = input(message)
      if resp != '':
        self.config[key] = resp

    print('\nProvide a value for each option or press enter to keep the current value.')
    print('Please check the README for more information on each option!\n')
    for key in self._configurationKeys:
      InputHandle(key)
    self.SaveConfig()

  def Status(self):
    status = 'not online'
    if self.builderInstance.online:
      status = 'online'
    print(f'Remote machine is {status}.')

  def Console(self):
    if not self.builderInstance.online:
      print(colored('Remote machine is not online!', 'yellow'))
      return
    os.system(f'ssh -i {self.sshKeyFilePath} {self.sshUsername}@{self.builderInstance.GetInstanceIP()}')
    
  def Rdp(self):
    if not self.builderInstance.online:
      print(colored('Remote machine is not online!', 'yellow'))
      return
    open('temp.rdp', 'w+').write(f'auto connect:i:1\nfull address:s:{self.builderInstance.GetInstanceIP()}\nusername:s:{self.sshUsername}\ndrivestoredirect:s:')
    os.system('temp.rdp')
    time.sleep(1)
    os.remove('temp.rdp')
    print('Started remote desktop connection!')

  def Build(self):
    if not self.builderInstance.online:
      print(colored('Remote machine is not online!', 'yellow'))
      return
    else:
      clearCache = self.YesNoPrompt('Would you like to clear the cache prior to building?')
      verbose = self.YesNoPrompt('Would you like verbose output?')
      sshClient = ssh.SSHClient(self.sshUsername, self.builderInstance.GetInstanceIP(), self.sshPassword, self.sshKeyFilePath)
      if not verbose:
        print('Starting build (this may take a while!)...')
      myBuilder = gmBuilder.GMBuilder(self.config, sshClient, verbose)
      myBuilder.CreateBuildFolders(clearCache=clearCache)
      myBuilder.DumpOptionFiles()
      myBuilder.UpdateProject()
      myBuilder.CompileProject()
      myBuilder.RetrieveBuild()
      if self.YesNoPrompt('Would you like to shut down the instance?'):
        self.builderInstance.Shutdown()

  def Startup(self):
    self.builderInstance.Startup()
  
  def Shutdown(self):
    self.builderInstance.Shutdown()

  def Exit(self):
    sys.exit()

# Run the script!
if __name__ == '__main__':
    lazyBuild = LazyBuild()
    while (True):
      lazyBuild.ReadUserInput()