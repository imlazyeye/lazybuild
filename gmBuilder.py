# Imports
import os
import json
import shutil 
import subprocess
import stat 
import ssh
import time
from termcolor import colored
import colorama
colorama.init()

class GMBuilder:

  def __init__(self, config, sshClient, verbose):

    def LoadOptions(config):
      self._PrintWrapper('Loading user configured options...')
      config['projectName'] = os.path.basename(config['yypPath']).replace('.yyp', '')
      config['remoteProjectPath'] = 'C:\\users\\buildManager\\AppData\\Local\\lazybuild\\Input\\Project'
      return config

    self._sshClient = sshClient
    self._verbose = verbose
    configData = LoadOptions(config)
    self.outputFolder = 'C:\\users\\buildManager\\AppData\\Local\\lazybuild'
    self.cacheFolder = 'C:\\Users\\buildManager\\AppData\\Roaming\\GameMakerStudio2\\Cache\\GMS2CACHE'
    self._yoyoID = configData['yoyoID']
    self._runtimeVersion = configData['runtimeVersion']
    self._steamSDKPath = configData['steamSDKPath']
    self._remoteProjectPath = configData['remoteProjectPath']
    self._projectName = configData['projectName']
    self._configuration = configData['configuration']
    self._gitBranch = configData['gitBranch']
    self._gitURL = configData['gitURL']
    self._gitUsername = configData['gitUsername']
    self._gitPassword = configData['gitPassword']
    self._useCache = True

  def _PrintWrapper(self, message):
    if self._verbose:
      print(message)

  def _SanatizeOptionsDictionary(self, options):
    self._PrintWrapper('Populating file with user data...')
    for key, value in options.items():
      value = value.replace('{BUILD_PATH}', self.outputFolder)
      value = value.replace('{YOYO_ID}', self._yoyoID)
      value = value.replace('{RUNTIME_VERSION}', self._runtimeVersion)
      value = value.replace('{PROJECT_NAME}', self._projectName)
      value = value.replace('{USERNAME}', self._gitUsername)
      value = value.replace('{CONFIG}', self._configuration)
      options[key] = value
    return options

  def _GenerateBuildFile(self):
    self._PrintWrapper('Generating build.bff...')
    buildTemplate = json.load(open('resources/options/build.bff', 'r'))
    buildTemplate = self._SanatizeOptionsDictionary(buildTemplate)
    return buildTemplate

  def _GenerateMacrosFile(self):
    self._PrintWrapper('Generating macros.json...')
    macrosTemplate = json.load(open('resources/options/macros.json', 'r'))
    macrosTemplate = self._SanatizeOptionsDictionary(macrosTemplate)
    return macrosTemplate

  def DumpOptionFiles(self):
    self._PrintWrapper('Creating build option files on remote...')
    sftpClient = self._sshClient.OpenSFTP()
    sftpClient.put('resources/options/targetoptions.json', os.path.join(self.outputFolder, 'Input', 'Options', 'targetoptions.json'))
    sftpClient.put('resources/options/preferences.json', os.path.join(self.outputFolder, 'Input', 'Options', 'preferences.json'))
    json.dump({'steamsdk_path': self._steamSDKPath}, open('temp', 'w+'))
    sftpClient.put('temp', os.path.join(self.outputFolder, 'Input', 'Options', 'steam_options.yy'))
    json.dump(self._GenerateBuildFile(), open('temp', 'w+'), indent=4)
    sftpClient.put('temp', os.path.join(self.outputFolder, 'Input', 'Options', 'build.bff'))
    json.dump(self._GenerateMacrosFile(), open('temp', 'w+'), indent=4)
    sftpClient.put('temp', os.path.join(self.outputFolder, 'Input', 'Options', 'macros.json'))
    os.remove('temp')
    
  def CreateBuildFolders(self, clearCache=False):

    def PurgeDirectory(path):
      self._sshClient.Call(f'rmdir /S /Q "{path}"')
      self._sshClient.Call(f'mkdir "{path}"')

    self._PrintWrapper('Creating build folder architecture...')
    self._sshClient.Call(f'mkdir "{self.outputFolder}"') # No purge to not deleted project, but it has to exist!
    PurgeDirectory(os.path.join(self.outputFolder, 'Output', 'GameZip'))
    PurgeDirectory(os.path.join(self.outputFolder, 'Output', 'GameFiles'))
    PurgeDirectory(os.path.join(self.outputFolder, 'Input', 'Options'))
    if clearCache:
      self._PrintWrapper('Clearing the cache...')
      PurgeDirectory(os.path.join(self.cacheFolder))
      
  def UpdateProject(self):

    self._PrintWrapper('Opening SFTP connection...')
    sftpClient = self._sshClient.OpenSFTP()
    
    # Clone vs Pull
    try:
      sftpClient.stat(os.path.join(self._remoteProjectPath, '.git')) # path test
      self._PrintWrapper('Found project repo!')
      self._PrintWrapper('Fetching and pulling updates...')
      self._sshClient.Call(f'cd {self._remoteProjectPath} && git reset --hard && git checkout {self._gitBranch} && git fetch && git pull && git status')
    
    except IOError:
      self._PrintWrapper('Repository was not found on the remote!')
      self._PrintWrapper('Cloning repository (this may take a while!)...')
      self._sshClient.Call(f'cd {self._remoteProjectPath}')
      findKey = 'https://'
      index = self._gitURL.find(findKey) + len(findKey)
      url = f'{self._gitURL[:index]}{self._gitUsername}:{self._gitPassword}@{self._gitURL[index:]} {self._remoteProjectPath}'
      self._sshClient.Call(f'git clone -b {self._gitBranch} {url}')
      self._PrintWrapper('Finished cloning the repository!')


    # Close connection
    self._PrintWrapper('Closing SFTP connection...')
    self._sshClient.CloseSFTP(sftpClient)
    
  def CompileProject(self):
    self._PrintWrapper('Invoking GameMaker compiler...')
    buildCommand = f'"C:/ProgramData/GameMakerStudio2/Cache/runtimes/runtime-{self._runtimeVersion}/bin/Igor.exe"  -j=8 -options="{self.outputFolder}/Input/Options/build.bff" -v -- Windows PackageZip'
    self._sshClient.Call(buildCommand, printResult=self._verbose)
    self._PrintWrapper('Compiler has finished running.')

  def RetrieveBuild(self):
    sftpClient = self._sshClient.OpenSFTP()
    try:
      path = os.path.join(self.outputFolder, f'Output\\GameZip\\{self._projectName}.zip')
      sftpClient.stat(path)
      self._PrintWrapper('Sending the output back to local machine...')
      sftpClient.get(path, f'./{self._projectName}.zip')
    except:
      self._PrintWrapper(colored('Failed to retrieve ouput file!', 'red'))
      