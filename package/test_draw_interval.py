import os

import OpenGL.GL as gl
import numpy as np
from PIL import Image
from PySide6.QtCore import QTimerEvent, Qt
from PySide6.QtGui import QMouseEvent, QCursor
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication

import live2d.v3 as live2d
# import live2d.v2 as live2d
import resources


def callback():
    print("motion end")


class Win(QOpenGLWidget):

    def __init__(self) -> None:
        super().__init__()
        self.isInLA = False
        self.clickInLA = False
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.a = 0
        self.resize(400, 500)
        self.read = False
        self.clickX = -1
        self.clickY = -1
        self.model: live2d.LAppModel | None = None
        self.systemScale = QGuiApplication.primaryScreen().devicePixelRatio()

    def initializeGL(self) -> None:
        # 将当前窗口作为 OpenGL 的上下文
        # 图形会被绘制到当前窗口
        self.makeCurrent()

        if live2d.LIVE2D_VERSION == 3:
            live2d.glewInit()

        # 创建模型
        self.model = live2d.LAppModel()

        if live2d.LIVE2D_VERSION == 3:
            self.model.LoadModelJson(os.path.join(resources.RESOURCES_DIRECTORY, "v3/Mao/Mao.model3.json"))
        else:
            self.model.LoadModelJson(os.path.join(resources.RESOURCES_DIRECTORY, "v2/shizuku/shizuku.model.json"))

        # 以高帧率绘制
        self.startTimer(int(1000 / 120))

    def resizeGL(self, w: int, h: int) -> None:
        # 使模型的参数按窗口大小进行更新
        if self.model:
            self.model.Resize(w, h)
        
    def onMotionStarted(self, group, no):
        print(group, no)

    def paintGL(self) -> None:
        live2d.clearBuffer()

        self.model.Update()
        if self.model.IsMotionFinished():
            self.model.StartRandomMotion(onStartMotionHandler=self.onMotionStarted)

        self.model.Draw()

    def timerEvent(self, a0: QTimerEvent | None) -> None:
        if not self.isVisible():
            return

        local_x, local_y = QCursor.pos().x() - self.x(), QCursor.pos().y() - self.y()
        self.model.Drag(local_x, local_y)
        if self.isInL2DArea(local_x, local_y):
            self.isInLA = True
            # print("in l2d area")
        else:
            self.isInLA = False
            # print("out of l2d area")

        self.update()

    def isInL2DArea(self, click_x, click_y):
        h = self.height()
        alpha = gl.glReadPixels(click_x * self.systemScale, (h - click_y) * self.systemScale, 1, 1, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)[3]
        return alpha > 0

    def mousePressEvent(self, event: QMouseEvent) -> None:
        x, y = event.scenePosition().x(), event.scenePosition().y()
        # 传入鼠标点击位置的窗口坐标
        if self.isInL2DArea(x, y):
            self.clickInLA = True
            self.clickX, self.clickY = x, y
            print("pressed")

    def mouseReleaseEvent(self, event):
        x, y = event.scenePosition().x(), event.scenePosition().y()
        # if self.isInL2DArea(x, y):
        if self.isInLA:
            self.model.Touch(x, y)
            self.clickInLA = False
            print("released")

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        x, y = event.scenePosition().x(), event.scenePosition().y()
        if self.clickInLA:
            self.move(int(self.x() + x - self.clickX), int(self.y() + y - self.clickY))


if __name__ == "__main__":
    import sys

    from PySide6.QtGui import QSurfaceFormat

    live2d.init()
    # --垂直同步--
    format = QSurfaceFormat.defaultFormat()
    format.setSwapInterval(0) # 1=>开启
    QSurfaceFormat.setDefaultFormat(format)
    # --垂直同步--

    app = QApplication(sys.argv)
    win = Win()
    win.show()
    app.exec()

    live2d.dispose()
