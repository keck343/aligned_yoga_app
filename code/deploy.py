import paramiko
from os.path import expanduser
from user_definition import *

# ## Assumption : Anaconda, Git (configured)


def ssh_client():
    """Return ssh client object"""
    return paramiko.SSHClient()


def ssh_connection(ssh, ec2_address, user, key_file):
    """Connect to ssh and return ssh connect object"""
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ec2_address, username=user,
                key_filename=expanduser("~") + key_file)
    return ssh


def create_or_update_environment(ssh):
    """Build environment from .yml file """
    stdin, stdout, stderr = \
        ssh.exec_command("conda env create -f "
                         "~/" + git_repo_name + "/venv/environment.yml")
    if (b'already exists' in stderr.read()):
        stdin, stdout, stderr = \
            ssh.exec_command("conda env update -f "
                             "~/" + git_repo_name + "/venv/environment.yml")


def git_clone(ssh):
    """Clone or pull git repo"""
    git_oauth = "296a5a48dcf2f4377455599deca2ecb0a3489768"
    stdin, stdout, stderr = ssh.exec_command("git --version")
    if (b"" is stderr.read()):
        git_clone_command = "git clone " + \
                            "https://" + \
                            git_oauth + \
                            "@github.com/" + \
                            git_repo_owner + "/" + git_repo_name + ".git"
        stdin, stdout, stderr = ssh.exec_command(git_clone_command)

    if (b'already exists' in stderr.read()):
        stdin, stdout, stderr = ssh.exec_command("cd " + git_repo_name +
                                                 "; git pull")


def set_cronjob(ssh):
    """Set cronjob executing code from git repo"""
    stdin, stdout, stderr = \
        ssh.exec_command('(crontab -l ;'
                         ' echo "* * * * * ~/.conda/envs/MSDS603/bin/python '
                         '/home/ec2-user/' + git_repo_name + '/code' +
                         '/calculate_driving_time.py")'
                         ' | sort - | uniq - | crontab -')


def main():
    """Main driver function"""
    ssh = ssh_client()
    ssh_connection(ssh, ec2_address, user, key_file)
    git_clone(ssh)
    create_or_update_environment(ssh)
    set_cronjob(ssh)


if __name__ == '__main__':
    main()
