# Import libraries
import paramiko
import sys
import time 
from termcolor import colored
import colorama
colorama.init()

class SSHClient:

  def __init__(self, username, ip, password, keyFile=''):
    print(f'Attempting to SSH to {ip}...')
    self.ip = ip 
    self.username = username
    self.password = password 
    self.keyFile = keyFile
    self.client = paramiko.SSHClient()
    self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    self._Connect()

  def __del__(self):
    self._Disconnect()

  def _Connect(self):
    try:
      self.client.connect(self.ip, 22, self.username, self.password, key_filename=self.keyFile)
      print('Connected!')
    except:
      print(colored('Connection failed, trying again...', 'yellow'))
      self._Connect()

  def _Disconnect(self):
    try:
      self.client.close()
      print('Closed SSH connection!')
    except:
      print(colored(f'Failed to disconnect from {self.ip}!', 'red'))
      print(sys.exc_info()[0])

  def Call(self, command, printResult=False):
    stdin, stdout, stderr = self.client.exec_command(command)
    for line in iter(lambda: stdout.readline(2048), ''):
      if printResult:
        print(line, end='')
    return stdin, stdout, stderr

  def OpenSFTP(self):
    return self.client.open_sftp()
  
  def CloseSFTP(self, sftpClient):
    sftpClient.close()
    return 

  def CheckFileExistsOnRemote(self, path):
    sftpClient = self.OpenSFTP()
    try:
      sftpClient.stat(path)
      return True 
    except:
      return False