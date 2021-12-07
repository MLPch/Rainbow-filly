import subprocess

def status(service):
    status = subprocess.check_output(('sudo systemctl status ' + service + '.service; exit 0'), shell=True)
    status = status.decode('UTF-8')
    status = status.partition('CGroup:')
    status = status[0].strip()
    return status
    
if __name__ == "__main__":
    service = input('Введите имя сервиса :')
    print(status(service))