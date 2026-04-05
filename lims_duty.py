import requests
from bs4 import BeautifulSoup
import sys
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt


class Lims():
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
        }
        self.session = requests.Session()

    def get_loginstamp(self):
        url = "http://lmis-shigong.subway.com/maximo/webclient/login/login.jsp"
        r = self.session.get(url, headers=self.headers, verify=False)
        soup = BeautifulSoup(r.text, 'lxml')
        loginstamp = soup.find('input', attrs={"name": "loginstamp"})['value']
        self.loginstamp = loginstamp

    def get_csrftoken(self, username, password):
        url = "http://lmis-shigong.subway.com/maximo/ui/login"
        data = {
            "allowinsubframe": "null",
            "mobile": "false",
            "login": "jsp",
            "loginstamp": self.loginstamp,
            "username": username,
            "password": password,
        }
        r = self.session.post(url, headers=self.headers, data=data, verify=False)
        soup = BeautifulSoup(r.text, 'lxml')
        csrftoken = soup.find('input', attrs={"id": "csrftokenholder"})['value']
        self.csrftoken = csrftoken
        userfullname = soup.find('span', attrs={"class": "homeButtontxtappname"}).text
        self.userfullname = userfullname
        uisessionid = soup.find('input', attrs={"id": "uisessionid"})['value']
        self.uisessionid = uisessionid

    def login(self):
        self.get_loginstamp()
        self.get_csrftoken(username, password)

    def maximo(self, station):
        url = f"http://lmis-shigong.subway.com/maximo/ui/?event=loadapp&value=gzmstduty&uisessionid={self.uisessionid}&csrftoken={self.csrftoken}"
        self.session.get(url, headers=self.headers, verify=False)

        url = "http://lmis-shigong.subway.com/maximo/ui/maximo.jsp"
        data = {
            "uisessionid": self.uisessionid,
            "csrftoken": self.csrftoken,
            "currentfocus": "mx377",
            "events": '[{"type":"setvalue","targetId":"mx377","value":"' + station + '","requestType":"ASYNC","csrftokenholder":"' + self.csrftoken + '"},{"type":"filterrows","targetId":"mx304","value":"","requestType":"SYNC","csrftokenholder":"' + self.csrftoken + '"}]'
        }
        self.session.post(url, headers=self.headers, data=data, verify=False)

        data = {
            "uisessionid": self.uisessionid,
            "csrftoken": self.csrftoken,
            "currentfocus": "mx435[R:0]",
            "events": '[{"type":"click","targetId":"mx435[R:0]","value":"","requestType":"SYNC","csrftokenholder":"' + self.csrftoken + '"}]'
        }
        response = self.session.post(url, headers=self.headers, data=data, verify=False)
        soup = BeautifulSoup(response.text, 'lxml')

        names = soup.find_all('input',
                              attrs={'fldinfo': '{"length":"62","inttype":"0","lookup":"longdesc","eventpriority":1}'})
        on_duty = soup.find_all('a', attrs={'fldinfo': '{"length":"","inttype":"","eventpriority":2}'})

        rota = {}
        for a, b in enumerate(zip(names, on_duty)):
            rota[b[0]['ov']] = {
                'id': str(a),
                'duty': b[1]['title']
            }

        if self.userfullname not in rota:
            raise ValueError("受令当班登记没有用户信息...")
        for key, value in rota.items():
            if key != self.userfullname and value['duty'] == '当班： 已选中' or key == self.userfullname and value[
                'duty'] == '当班： 未选中':
                url = "http://lmis-shigong.subway.com/maximo/ui/maximo.jsp"
                data = {
                    "uisessionid": self.uisessionid,
                    "csrftoken": self.csrftoken,
                    "currentfocus": f"mx970[R:{value['id']}]",
                    "events": '[{"type":"toggle","targetId":"mx970[R:' + value[
                        'id'] + ']","value":"","requestType":"ASYNC","csrftokenholder":"' + self.csrftoken + '"}]'
                }
                self.session.post(url, headers=self.headers, data=data, verify=False)

        url = "http://lmis-shigong.subway.com/maximo/ui/maximo.jsp"
        data = {
            "uisessionid": self.uisessionid,
            "csrftoken": self.csrftoken,
            "currentfocus": f"mx970[R:{len(rota) - 1}]",
            "events": '[{"type":"click","targetId":"mx280","value":"","requestType":"SYNC","csrftokenholder":"' + self.csrftoken + '"}]'
        }
        self.session.post(url, headers=self.headers, data=data, verify=False)


# ==================== 修改密码验证窗口大小位置 ====================
# 修改 setFixedSize(280, 160) 中的数值来调整窗口大小
# 第一个参数是宽度，第二个参数是高度
class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("验证")
        self.setFixedSize(180, 140)  # <--- 修改这里调整窗口大小 (宽度, 高度)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(25, 20, 25, 20)

        label = QLabel("请输入密码")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(32)
        self.password_input.returnPressed.connect(self.check_password)
        layout.addWidget(self.password_input)

        btn = QPushButton("验证")
        btn.setFixedHeight(34)
        btn.clicked.connect(self.check_password)
        layout.addWidget(btn)

        self.setLayout(layout)

        # 圆润简洁风格样式
        self.setStyleSheet("""
            QDialog {
                background-color: #fafafa;
                border-radius: 8px;
            }
            QLabel {
                color: #444;
                font-size: 13px;
            }
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 4px 10px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #aaa;
            }
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)

    def check_password(self):
        if self.password_input.text() == "0":
            self.accept()
        else:
            QMessageBox.critical(self, "错误", "密码错误！")
            sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    password_dialog = PasswordDialog()
    if password_dialog.exec() != QDialog.DialogCode.Accepted:
        sys.exit()

    username = 'chenmengxi'
    password = 'Sbdt1124@'
    station = '508'

    try:
        Shigong = Lims()
        Shigong.login()
        Shigong.maximo(station)

        QMessageBox.information(None, "完成", f"受令员当班登记： {Shigong.userfullname} √")

    except Exception as e:
        QMessageBox.critical(None, "失败", "受令员当班登记失败！")