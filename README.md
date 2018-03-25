# liarcom

[![PyPI version](https://img.shields.io/pypi/v/liarcom.svg)](https://pypi.python.org/pypi/liarcom)

基于python3的第三方Drcom登录器。由[@EverybodyLies](https://github.com/Everyb0dyLies)开发维护。

本登陆器有图形界面和命令行两种运行模式，图形界面基于PyQt5实现，可跨平台运行，在路由器上可以以命令行模式运行。

#### 安装

使用pip安装

`pip install liarcom`

或从GitHub获取

`git clone https://github.com/Everyb0dyLies/liarcom.git`

#### 使用

支持图形界面模式和命令行模式。

在Windows10中，可以下载辅助工具中的vbs脚本启动，输入学号密码然后点登陆即可。

在Linux或路由器中，建议以命令行模式使用。命令行模式仅用liarcom.py和tools.py两个文件，请修改liarcom.py中`# local config`部分，然后用`python liarcom.py`运行。

在Mac中建议用pip安装，之后在终端中执行`python -m liarcom`即可打开图形界面。

#### 发起issue

欢迎大家在issue提交bug，我会尽量跟进并尽可能及时修复，如果大神比较着急，自己修改代码，也欢迎发送pull requests。

如果你不能登录，或中途闪退，请发issue的时候详细描述bug出现之前的每一步具体操作和软件崩溃的表现行为，以及操作系统和运行环境，如果可能请附上INFO级日志输出。

**请不要提交无效的issue！**

[提问的智慧](https://github.com/ryanhanwu/How-To-Ask-Questions-The-Smart-Way/blob/master/README-zh_CN.md)，不负责教授基础操作！

#### 感谢

本项目参考了以下项目，顺序不分先后

drcoms/drcom-generic，https://github.com/drcoms/drcom-generic

coverxit/EasyDrcom，https://github.com/coverxit/EasyDrcom/

mchome/dogcom，https://github.com/mchome/dogcom

dantmnf/drcom-client，https://github.com/dantmnf/drcom-client

非常感谢这些前辈，如果没有他们，本项目很难开展

#### License

liarcom is licensed under the GNU General Public License v3.0

重申本代码仅用于实验和学习，使用者的一切商业行为及非法行为皆由其本人承担责任。

