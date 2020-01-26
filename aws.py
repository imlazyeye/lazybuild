# Imports
import boto3
import time 
import subprocess
from termcolor import colored

class AWSInstance:

  def __init__(self, region, id, shutdownOnDestroy=True):
    self.session = boto3.session.Session(region_name=region)
    self.client = self.session.client('ec2')
    self.id = id
    self.shutdownOnDestroy = shutdownOnDestroy
    self.ip = None
    self.online = self.CheckRunning()
  
  def Startup(self):
    if self.CheckRunning():
      print(colored('Remote server is already running!', 'yellow'))
      self.online = True
      return True
    else:
      print("Booting up remote server...")
      try:
        self.client.start_instances(InstanceIds=[self.id])
      except:
        print(colored('Remote server failed to start! It may be in an unstable state, try again in a few seconds.', 'red'))
        self.online = False
        return False
      print("Waiting for remote server to be set up before continuing...")
      while not self.CheckRunning():
        time.sleep(0.1)
      print('Remote server is online!')
      self.online = True
      return True

  def Shutdown(self):
    print("Shutting down remote server...")
    self.client.stop_instances(InstanceIds=[self.id])
    while not self.CheckStopped():
      time.sleep(0.1)
    print("Remote server has been shut down!")

  def CheckRunning(self):
    resp = self.client.describe_instance_status(InstanceIds=[self.id])
    if len(resp['InstanceStatuses']) == 0:
      return False
    return resp['InstanceStatuses'][0]['InstanceState']['Name'] == 'running'

  def CheckStopped(self):
    resp = self.client.describe_instance_status(InstanceIds=[self.id])
    if len(resp['InstanceStatuses']) == 0:
      return True
    return resp['InstanceStatuses'][0]['InstanceState']['Name'] == 'stopped'

  def GetInstanceIP(self):
    if self.ip == None:
      self.ip = self.client.describe_instances(InstanceIds=[self.id])['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['PrivateIpAddresses'][0]['Association']['PublicIp']
    return self.ip

  def PingInstance(self):
    command = ['ping', '-n', '1', self.GetInstanceIP()]
    if subprocess.call(command, stdout=subprocess.PIPE) == 0:
      return True
    else:
      return False

  def ExecutePowerShellScript(self, scriptPath):
    ssmClient = boto3.client('ssm')
    try:
      scriptLines = open(scriptPath, 'r').readlines()
    except IOError:
      print(colored('Script was not found!', 'red'))
      return
    params = {'commands': scriptLines}
    resp = ssmClient.send_command(DocumentName='AWS-RunPowerShellScript', InstanceIds=[self.id], Parameters=params)
    commandID = resp['Command']['CommandId']
    output = {'ResponseCode': -1}
    while output['ResponseCode'] != 0:
      try:
        output = ssmClient.get_command_invocation(CommandId=commandID, InstanceId=self.id)
      except:
        pass
    return output['StandardOutputContent']