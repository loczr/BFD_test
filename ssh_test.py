import paramiko
from yagmail import SMTP
from PyQt5.QtGui import QIcon,QDesktopServices
from PyQt5.QtWidgets import QSystemTrayIcon,QAction,QMenu,QMainWindow,QApplication,QMessageBox
from PyQt5.QtCore import  pyqtSignal,QThread,QMutex,QUrl
from ssh_test_ui import Ui_MainWindow
import sys
import os
import re
import time

class ssh_conn(QMainWindow,Ui_MainWindow):

    def __init__(self,parent= None):
        super(ssh_conn, self).__init__(parent)
        self.setupUi(self)

        self.setWindowIcon(QIcon('icon/icon.ico'))

        self.logAction = QAction("日志", self)
        self.logAction.setIcon(QIcon('icon/log.png'))
        self.openAction = QAction("打开", self)
        self.openAction.setIcon(QIcon('icon/open.png'))
        self.quitAction = QAction("退出", self)
        self.quitAction.setIcon(QIcon('icon/quit.png'))  # 从系统主题获取图标

        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(self.logAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.openAction)
        self.trayIconMenu.addAction(self.quitAction)

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setIcon(QIcon("icon/icon.ico"))
        self.trayIcon.setToolTip("what are you looking for ???")
        self.trayIcon.activated.connect(self.act)
        self.trayIcon.show()
        self.trayicon_connect()

        self.all_times = 0
        self.mail_test = True

        self.start_button.clicked.connect(self.buttonclick)
        self.stop_button.clicked.connect(self.stop_done)
        self.Mail_test_button.clicked.connect(self.Mail_test_bu)
        self.actionshow_Status.triggered.connect(self.view_show)#菜单栏控制文本窗口隐藏与否


        # 信息提示
        # 参数1：标题
        # 参数2：内容
        # 参数3：图标（0没有图标 1信息图标 2警告图标 3错误图标），0还是有一个小图标
        self.trayIcon.showMessage('python', 'for_test', icon=2)
        self.trayIcon.messageClicked.connect(self.show_Normal)

    '''
    #系统关闭事件修改
    def closeEvent(self, event):
        # 按程序关闭时，弹窗显示
        QMessageBox.information(
                self, "系统托盘", "程序将继续在系统托盘中运行。要终止该程序，请在系统托盘条目的上下文菜单中选择[退出]。")
        # 程序主窗口不可视（隐藏）
        self.setVisible(False)
        # 关闭时间忽略
        event.ignore()
    '''

    def act(self,reason):
        # 鼠标点击icon传递的信号会带有一个整形的值，1是表示单击右键，2是双击，3是单击左键，4是用鼠标中键点击
        if reason == 2 or reason == 3:
            self.show_Normal()

    def trayicon_connect(self):
        self.logAction.triggered.connect(self.open_log)
        self.quitAction.triggered.connect(QApplication.quit)
        self.openAction.triggered.connect(self.show_Normal)

    def view_show(self):
        if self.actionshow_Status.isChecked():
            self.Status_dock_widge.show()
        else:
            self.Status_dock_widge.hide()

    def open_log(self):
        if os.path.exists('log.txt'):
            QDesktopServices.openUrl(QUrl('log.txt'))
        else:
            open('log.txt', 'a+')
            QDesktopServices.openUrl(QUrl('log.txt'))

    def show_Normal(self):
        self.showNormal()

    def script_information(self):
        host = self.host.text()
        port = self.port.text()
        username = self.username.text()
        password = self.passwd.text()
        ping_cmd1 = self.ping_cmd1.text()
        ping_cmd2 = self.ping_cmd2.text()
        cmd_text = self.Cmd_text.toPlainText()
        cmd_reback_text = self.Cmd_reback_text.toPlainText()
        go_ahead = False
        self.cmd_list = [cmd_text,cmd_reback_text,False]
        self.login_list = [host, port, username, password,ping_cmd1,ping_cmd2]

        for check in [host, port, username, password, ping_cmd1, ping_cmd2, cmd_text, cmd_reback_text]:
            if check == '':
                self.append_status_info('something is null,please check again')
                go_ahead = False
                break
            else:
                go_ahead = True
        #print(self.login_list)
        return go_ahead

    def buttonclick(self):

        go_ahead =  self.script_information()

        if go_ahead:
            # 主线信号发射及线程开启
            self.test_thread_master = Master_link(self.login_list)
            self.test_thread_master.log_sin.connect(self.append_status_info)
            self.test_thread_master.ping_error.connect(self.line_error)
            self.test_thread_master.button_setFalse.connect(self.statr_done)
            self.test_thread_master.start()
            self.statr_done()

            # cmd命令线程绑定
            # 在link_error函数触发线程
            self.cmd_thread = BFD_cmd(self.cmd_list)
            self.cmd_thread.cmd_log.connect(self.log_txt)
            self.cmd_thread.cmd_mail.connect(self.Mail_ser)

    def statr_done(self):
        self.host.setEnabled(False)
        self.port.setEnabled(False)
        self.username.setEnabled(False)
        self.passwd.setEnabled(False)
        self.ping_cmd1.setEnabled(False)
        self.ping_cmd2.setEnabled(False)
        self.Cmd_text.setEnabled(False)
        self.Cmd_reback_text.setEnabled(False)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_done(self):
        self.test_thread_master.stop_thread()
        self.host.setEnabled(True)
        self.port.setEnabled(True)
        self.username.setEnabled(True)
        self.passwd.setEnabled(True)
        self.ping_cmd1.setEnabled(True)
        self.ping_cmd2.setEnabled(True)
        self.Cmd_text.setEnabled(True)
        self.Cmd_reback_text.setEnabled(True)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def Mail_test_bu(self):
        self.mail_test = True
        self.Mail_ser()

    def Mail_ser(self,content=False):
        #content = self.Mail_content_text.text()
        if self.Mail_server.isChecked():
            '''
        self.username = mail_information[0]
        self.pwd = mail_information[1]
        self.host = mail_information[2]
        self.port = mail_information[3]
        self.content = mail_information[4]
            '''

            mail_information = [
                self.Mail_user.text(),
                self.Mail_passwd.text(),
                self.Server_host.text(),
                self.Server_port.text(),
                self.Mail_content_text.toPlainText()
            ]

            if self.mail_test:
                mail_information[4] = 'test'
                self.Mail_threa = Mail_thread(mail_information)
                self.Mail_threa.start()
                self.mail_test = False
            else:
                if content:
                    mail_information[4] = content
                    self.Mail_threa = Mail_thread(mail_information)
                    self.Mail_threa.start()
                    self.mail_test = False
                else:
                    self.Mail_threa = Mail_thread(mail_information)
                    self.Mail_threa.start()

    def append_status_info(self, msg):

        if msg == 'Connect error!!!!!!!!!!!!!': #ssh连接错误判断
            self.stop_done()

        self.Status_browser.append(msg)
        if self.Status_browser.textCursor().blockNumber() == 999:
            self.Status_browser.clear()

    def log_txt(self,str=False):
        current_time =time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        csvFile = open('log.txt', 'a+')

        if str:
            csvFile.write(current_time + '\t'+str+'\n')
        else:
            csvFile.write(current_time + '\tall_link_down\n')
        csvFile.close()

    def line_error(self,link1,link2):
        '''
        link = 1 时，线路up
        link = 2 时，线路douw
        :param link1:
        :param link2:
        :return:
        '''
        #bfd_cmd_flag 为False 时不调用BFD_CMD()
        bfd_cmd_flag = False
        #双线路正常，且BFD—flag为False,流量正常走向
        if link1== 2 and link2== 2 and bfd_cmd_flag == False:
            pass
            #print('双线路正常，且BFD—flag为False,流量正常走向')
        #主线die，备线存活，且bfd_flag为False时，切换线路
        elif link1 == 1 and link2 == 2 and bfd_cmd_flag == False:
            #切换线路，重置flag为Ture
            # True 时执行线路线路切换
            self.cmd_list.append(True)
            # 开启BFD_cmd线程
            self.cmd_thread.start()
            #send_mail(tell it is change to link2 )
            bfd_cmd_flag = True
            #print('主线die，备线存活，且bfd_flag为False时，切换线路')
            self.trayIcon.showMessage('link_change', 'link_change_to_line2', icon=2)
            self.trayIcon.messageClicked.connect(self.show_Normal)

        #主线online，备线死亡，flag为False,不切换线路
        elif link1 == 2 and link2 == 1 and bfd_cmd_flag == False:
            pass
            #print('主线online，备线死亡，flag为False,不切换线路')
        # 主线online，备线死亡，flag为True,切换线路
        elif link1 == 2 and link2 == 1 and bfd_cmd_flag == True:
            #send_mail(tell it is change to link1 )
            #print('主线online，备线死亡，flag为True,切换回主线路')
            # False 时执行线路倒退
            self.cmd_list.append(False)
            # 开启BFD_cmd线程
            self.cmd_thread.start()
            self.trayIcon.showMessage('link_change', 'link_change_to_line1', icon=2)
            self.trayIcon.messageClicked.connect(self.show_Normal)

        #双线die，线路死亡次数加一
        else:
            self.all_times +=1
            #当死亡次数大于3时，发送邮件提示管理员
            if self.all_times >3:
                self.test_thread_master.quit()
                self.log_txt()
                self.yagmail()

                app.quit()

qmut1 = QMutex()
class Master_link(QThread):
    log_sin = pyqtSignal(str)
    ping_error = pyqtSignal(int,int)
    button_setFalse = pyqtSignal(object)

    def __init__(self, login_list):
        '''
        :param login_list:host,port,username,pwd,master_link_ping
        '''
        QThread.__init__(self)
        self.login_list = login_list
        self.host = self.login_list[0]
        self.port = self.login_list[1]
        self.username = self.login_list[2]
        self.pwd = self.login_list[3]
        self.ping1_cmd = self.login_list[4]
        self.ping2_cmd = self.login_list[5]
        self.link1_sig = False
        self.link2_sig = False
        self.flag = True
        self.re_end = r'<.*?>'
        self.re_ping = r'Reply from\s(.*?):\sbytes=.*\sSequence=\d\s(.*?)\s(.*?)$'
        self.re_ping_error = r'(\d)%\spacket\sloss'

    def __del__(self):
        #线程状态改变与线程终止
        self.exit()

    def stop_thread(self):
        self.flag = False


    def login(self):
        try:
            self.Client = paramiko.SSHClient()
            self.Client.load_system_host_keys()
            self.Client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.Client.connect(self.host,
                           self.port,
                           self.username,
                           self.pwd,
                           allow_agent=False,
                           look_for_keys=False)
            self.ssh_shell = self.Client.invoke_shell()
            while True:
                line = self.ssh_shell.recv(1024)
                if line and line.endswith(b'>'):
                    # print(line.decode())
                    break
        except:
            self.Client.close()
            self.log_sin.emit('Connect error!!!!!!!!!!!!!')
            self.flag = False
            return False


    def link1(self):
        if self.login():
            self.ssh_shell.send(self.ping1_cmd + '\n')
            while True:
                line = self.ssh_shell.recv(9999)
                # print(line.decode())
                end = re.search(self.re_end, line.decode())
                ping = re.search(self.re_ping, line.decode())
                ping_error = re.search(self.re_ping_error,line.decode())
                #print(line)
                if line:
                    # b'---- More - ---'
                    #当显示内容过多时回显示上述内容，则需要发送空格来显示更多内容
                    if line.endswith(b'-'):
                        # 发送空格
                        self.ssh_shell.send(chr(32))
                    elif end != None:
                    #判断是否匹配到了设备名称，（当命令结束之后，会回显设备名称）
                    #如果是回显设备名称则跳出循环
                        break
                    elif ping_error != None:
                        if ping_error.group(1) == '100':
                            self.link1_sig = 1
                        elif ping_error.group(1) == '0':
                            self.link1_sig = 2

                    elif ping != None:
                    #判断是否为ping命令回包，并且提取其中的目的地址，TTL，延迟
                    #ping 10.10.2.1 ttl=127 time=1 ms
                        #print(2)
                        self.log_sin.emit(time.strftime("%X")+':'+"ping "+ping.group(1)+' '+ping.group(2)+' '+ping.group(3))
            self.Client.close()
            return self.link1_sig
        else:
            return False

    def link2(self):
        if self.login():
            self.ssh_shell.send(self.ping2_cmd + '\n')
            while True:
                line = self.ssh_shell.recv(9999)
                # print(line.decode())
                end = re.search(self.re_end, line.decode())
                ping = re.search(self.re_ping, line.decode())
                ping_error = re.search(self.re_ping_error, line.decode())
                #print(line)
                if line:
                    if line.endswith(b'-'):
                        self.ssh_shell.send(chr(32))
                    elif end != None:
                        break
                    elif ping_error != None:
                        if ping_error.group(1) == '100':
                            self.link2_sig = 1
                        elif ping_error.group(1) == '0':
                            self.link2_sig = 2
                    elif ping != None:
                        self.log_sin.emit(time.strftime("%X") + ':' + "ping " + ping.group(1) + ' ' + ping.group(
                                2) + ' ' + ping.group(3))
            self.Client.close()
            return self.link2_sig
        else:
            return  False

    def run(self):
        qmut1.lock()
        while self.flag:
            link1 = self.link1()
            link2 = self.link2()
            if link1 and link2:
                self.sleep(5)
                if link1  and link2 :
                    self.ping_error.emit(link1,link2)
                    link1 = False
                    link2 = False
        qmut1.unlock()
        self.quit()

class Mail_thread(QThread):

    def __init__(self,mail_information):
        QThread.__init__(self)
        self.mail = mail_information
        self.username = mail_information[0]
        self.pwd = mail_information[1]
        self.host = mail_information[2]
        self.port = mail_information[3]
        self.content = mail_information[4]


    def yagmail(self):
        #如果有开启邮件服务
        '''
        Mail_username = self.Mail_user.text()
        Mail_passwd = self.Mail_passwd.text()
        Server_host = self.Server_host.text()
        Server_port = self.Server_port.text()
        #Mail_list = [Mail_username, Mail_passwd, Server_host, Server_port]
        '''

        # 链接邮箱服务器
        yag = SMTP(user=self.username,
                    password = self.pwd,
                    host=self.host,
                    port= self.port)
        # 发送邮件
        yag.send(
            to=self.username,  # 如果多个收件人的话，写成list就行了，如果只是一个账号，就直接写字符串就行to='123@qq.com'
            #cc='735@qq.com',  # 抄送

            subject='for_test',  # 邮件标题
            contents=self.content,  # 邮件正文
            #attachments=[r'd://log.txt', r'd://baidu_img.jpg']  # 附件如果只有一个的话，用字符串就行，attachments=r'd://baidu_img.jpg'
            )
        #可简写成：
        #yag.send('aaaa@126.com', '发送附件', contents, ["d://log.txt", "d://baidu_img.jpg"])
        # 关闭
        yag.close()

    def yagmail_test(self):
        # 链接邮箱服务器
        yag = SMTP(user=self.username,
                    password = self.pwd,
                    host=self.host,
                    port= self.port)
        # 发送邮件
        yag.send(
            to=self.username,
            subject='for_test',
            contents='test for script'
        )

        #yag.send('aaaa@126.com', '发送附件', contents, ["d://log.txt", "d://baidu_img.jpg"])
        # 关闭
        yag.close()

    def run(self):
        if self.content == 'test':
            self.yagmail_test()
        else:
            self.yagmail()
        self.quit()

class BFD_cmd(QThread):
    cmd_mail = pyqtSignal(str)
    cmd_log = pyqtSignal(str)

    def __init__(self,bfd_cmd):
        QThread.__init__(self)
        self.bfd = bfd_cmd
        self.cmd_exec = bfd_cmd[0]
        self.cmd_reback = bfd_cmd[1]
        self.flag = bfd_cmd[2]

    def ssh_login(self):
        self.Client = paramiko.SSHClient()
        self.Client.load_system_host_keys()
        self.Client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.Client.connect(self.host,
                       self.port,
                       self.username,
                       self.pwd,
                       allow_agent=False,
                       look_for_keys=False)
        self.ssh_shell = self.Client.invoke_shell()

        while True:
            line = self.ssh_shell.recv(1024)
            if line and line.endswith(b'>'):
                #print(line.decode())
                break

    def Command_Execution(self,cmd_exec):
        self.ssh_login()
        self.ssh_shell.send(self.ping1_cmd + '\n')

        ssh_shell = self.Client.invoke_shell()
        '''
        cmd_exec = ['sy',
                        'interface  Vlanif1000',
                        'ip address  192.168.1.1 24 ',
                        'display this'
                        ]
        '''
        for cmd in cmd_exec:
            ssh_shell.send(cmd + '\n')
            time.sleep(1)

        lines = []
        while True:
            line = ssh_shell.recv(9999)
            # print(line)

            if line:
                # b'---- More - ---'
                if line.endswith(b'-'):
                    # 发送空格键
                    ssh_shell.send(chr(32))
                elif line.endswith(b'>') or line.endswith(b']'):
                    break
                else:
                    # 对回显信息进行解码，并写入列表中
                    #print(line)
                    lines.append(line.decode())
        self.Client.close()
        #print(lines)
        return lines

    def Command_Reback(self, cmd_reback):
        self.ssh_login()
        self.ssh_shell.send(self.ping1_cmd + '\n')
        ssh_shell = self.Client.invoke_shell()
        for cmd in cmd_reback:
            ssh_shell.send(cmd + '\n')
            time.sleep(1)
        lines = []
        while True:
            line = ssh_shell.recv(9999)
            # print(line)

            if line:
                # b'---- More - ---'
                if line.endswith(b'-'):
                    # 发送空格键
                    ssh_shell.send(chr(32))
                elif line.endswith(b'>') or line.endswith(b']'):
                    break
                else:
                    # 对回显信息进行解码，并写入列表中
                    #print(line)
                    lines.append(line.decode())
        self.Client.close()
        #print(lines)
        return lines

    def run(self):
        if self.flag:
            self.Command_Execution(self.cmd_exec)
            self.cmd_log.emit('turn to backup-link')
            self.cmd_mail.emit('test')
        else:
            self.Command_Reback(self.cmd_reback)
            self.cmd_log.emit('turn to master-link')
            self.cmd_mail.emit('test')

if __name__ == '__main__':

    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)
    ui = ssh_conn()
    ui.show()
    sys.exit(app.exec_())

