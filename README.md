# BFD_test

简要说明一下功能：
![image](https://user-images.githubusercontent.com/42598441/233272845-791d611c-71a4-4394-af05-dad3bbd19344.png)



ping测试模块
![image](https://user-images.githubusercontent.com/42598441/233272879-60293e27-d570-4777-af94-f79403bd6977.png)



此模块功能在点击Start按钮之后，将无法对内容进行修改及填写，当然如果你全都没有填写会在信息窗口给出错误反馈。

这一块的话主要是登陆信息、检测命令及对配置命令和回退命令：

检测命令用来检测源网络去往目的网络的网络线路情况；

当主线或备线网络线路出故障时，可能会执行配置命令或回退命令，保证网络稳定。



邮件通知模块

你需要勾选来开启这个功能，且在你的邮箱开启SMTP服务。

1.配置你的SMTP服务器

不过有些SMTP服务器的Mail_password 这一块有点区别，有可能是用户邮箱密码，有可能是用户生成的识别码或key。

所以如果你在按下Test按钮等待大约十几秒之后，你仍然没有收到自己发给自己的邮件的话，可以从Mail_password这里去排查一下。

![image](https://user-images.githubusercontent.com/42598441/233272915-bbe38c4d-778b-47dd-a566-40c6bf13223b.png)


2.发生故障邮件发送内容设置

你可以在线路切换或主线备线都断网的情况下，设置你的发送内容



![image](https://user-images.githubusercontent.com/42598441/233272947-f9b2c3f8-6ce0-4032-bc54-b4c3c5123510.png)


信息反馈窗口Status

这个窗口主要是用来显示线路情况及错误反馈的

目前应该有三种信息反馈


![image](https://user-images.githubusercontent.com/42598441/233272975-3675461c-80b0-4b5c-80f5-d30acebd4f39.png)


当然这个窗口的位置是可以变动的，也可以独立开
![image](https://user-images.githubusercontent.com/42598441/233273010-102a7a71-0d7e-40f3-b4db-a414719b5e4f.png)



![image](https://user-images.githubusercontent.com/42598441/233273029-bb0793e6-2e3a-497d-a311-f12f2acf1225.png)


你也可以将它关闭，在菜单栏view里面你可以进行设置



系统托盘及图标

![image](https://user-images.githubusercontent.com/42598441/233273070-185a8755-6d49-40d4-b907-40b31216f636.png)

其中需要注意的是，程序在主窗口按关闭并不会关闭程序，需要在系统托盘按退出才能完全退出



说一下逻辑处理：

当你登陆内容、测试命令、配置命令都填写完毕之后，按Start 开始程序循环检测。

当主线或备线3次无法ping通时，会在log.txt中记录事件：

当主线切换至备线时，执行CMD配置命令，记录log，发送邮件；

当备线切换至主线时，执行CMD_reback配置命令，记录log，发送邮件；

当双线都无法通信时，记录log，发送邮件，退出程序。

