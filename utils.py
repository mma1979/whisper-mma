import os.path
from datetime import datetime


class Utils:
    @staticmethod
    def log_line(msg):
        now = datetime.now()
        return f'<li><span style="color: red;">[{now.strftime("%d/%b/%Y %H:%M:%S")}]</span> <span style="color: green;">{msg}</span> </li>'

    @staticmethod
    def log_info(msg):
        with open(os.path.join('logs', 'log.txt'), 'a') as log:
            log.write(Utils.log_line(msg))
            log.write('\n')
