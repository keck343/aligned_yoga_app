import paramiko
from os.path import expanduser
from user_definition import *
import time


# Assumption : Anaconda, Git (configured)
def ssh_client():
    """Return ssh client object"""
    return paramiko.SSHClient()


def ssh_connection(ssh, ec2_address, user, key_file):
    """Connect to ssh and return ssh connect object"""
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    time.sleep(10)
    ssh.connect(ec2_address, username=user,
                key_filename=expanduser("~") + key_file)
    return ssh


def create_or_update_environment(ssh):
    """Build environment from .yml file """
    print('Installing Environment . . . This may take a few minutes')
    stdin, stdout, stderr = \
        ssh.exec_command("conda env create -f "
                         "~/" + git_repo_name + "/venv/environment.yml")
    # print(stderr.read())
    if b'already exists' in stderr.read():
        stdin, stdout, stderr = \
            ssh.exec_command("conda env update -f "
                             "~/" + git_repo_name + "/venv/env.yml")


def git_clone(ssh):
    """Clone or pull git repo"""
    print('Pulling files from github')
    git_oauth = "296a5a48dcf2f4377455599deca2ecb0a3489768"
    stdin, stdout, stderr = ssh.exec_command("git --version")
    if b"" is stderr.read():
        git_clone_command = "git clone " + \
                            "https://" + \
                            git_oauth + \
                            "@github.com/" + \
                            git_repo_owner + "/" + git_repo_name + ".git"
        stdin, stdout, stderr = ssh.exec_command(git_clone_command)
        #print(stderr.read())

    if b'already exists' in stderr.read():
        stdin, stdout, stderr = ssh.exec_command("cd " + git_repo_name +
                                                 "; git pull")


def run_flask(ssh):
    """Initiate the flask route"""
    print('Launching Flask - Go to {0}:5001/upload\n'
          'Aligned page is up and running'.format(ip))

    transport = ssh.get_transport()
    channel = transport.open_session()
    channel.exec_command('source activate aligned \n cd ' + git_repo_name +
                         'checkin_2/code/front_end_server \n' +
                         'python upload_flask.py > /dev/null 2>&1 &')


def main():
    """Main driver function"""
    ssh = ssh_client()
    ssh_connection(ssh, ec2_address, user, key_file)
    git_clone(ssh)
    create_or_update_environment(ssh)
    run_flask(ssh)

    print('Logging out')
    ssh.close()
    print('Done')


if __name__ == '__main__':
    main()
