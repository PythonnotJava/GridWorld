import sys
from typing import *
from abc import abstractmethod

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt

class MsgBox(QPlainTextEdit):
    def __init__(self):
        super().__init__()

        self.__setUI()
    def __setUI(self) -> None:
        self.setPlaceholderText('等待运行中……')
        self.setReadOnly(True)

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)

        copy_action = QAction("复制", self)
        clear_action = QAction("清空文本", self)
        select_all = QAction('全选', self)
        save_all = QAction('全选保存', self)

        copy_action.triggered.connect(self.copy)
        clear_action.triggered.connect(self.clear)
        select_all.triggered.connect(self.selectAll)
        save_all.triggered.connect(self.saveTo)

        context_menu.addAction(copy_action)
        context_menu.addAction(clear_action)
        context_menu.addAction(select_all)
        context_menu.addAction(save_all)
        context_menu.exec_(event.globalPos())

    def saveTo(self) -> None:
        name, tp = QFileDialog.getSaveFileName(self, '保存文件', "C:/", "Html(*.html)")
        if name:
            with open(name, 'w', encoding='U8') as f:
                t = self.toPlainText()
                t = t.split('\n')
                t = ''.join([f"<p>{x}</p>" for x in t])
                f.write(
                    f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <title>Title</title>
                        <style>
                            p {{
                                font-size:24px;
                                text-align:center;
                                font-weight:bold;
                            }}
                        </style>
                    </head>
                    <body>
                        <div style="
                            border: 2px solid black;
                            border-radius: 10px;
                            margin: 0 auto;
                            padding: 20px;
                        ">
                        {t}
                        </div>
                    </body>
                    </html>
                    """
                )
                f.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = MsgBox()
    ui.show()
    sys.exit(app.exec())