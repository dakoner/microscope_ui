from PyQt5 import QtWidgets
import code

class PythonConsole(QtWidgets.QPlainTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.appendPlainText('>>> ')
        #self.installEventFilter(self)
        self.interp = code.InteractiveInterpreter()
        self.curPos = self.textCursor().position()

    # def eventFilter(self, obj, event):
    #     if event.type() == QtCore.QEvent.KeyPress:
    #         if event.key() == QtCore.Qt.Key_Return and self.hasFocus():
    #             c = self.toPlainText()[self.curPos:self.textCursor().position()]
    #             print(c)
    #             result = self.interp.runsource(c)
    #             print(result)
    #             self.appendPlainText("\n>>> ")
    #             self.curPos = self.textCursor().position()

    #     return super().eventFilter(obj, event)

