import sys
import cv

from PyQt4 import QtGui,QtCore

class Frame1(QtGui.QListWidget):
    def __init__(self):
        super(Frame1,self).__init__()
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setViewMode(QtGui.QListView.IconMode)
        self.setIconSize(QtCore.QSize(60, 60))
        self.setSpacing(0)

	self.splitImage()
	
	for y in range(5):
		for x in range(5):
			name=str(y)+str(x)
			image=QtGui.QPixmap(name + '.jpg')
        		part=QtGui.QListWidgetItem(self)
        		part.setIcon(QtGui.QIcon(image))
        		part.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled)


    def splitImage(self):
        im = cv.LoadImage("1.jpg")
        thumbnail = cv.CreateImage( ( 400, 400), im.depth, im.nChannels)
        cv.Resize(im, thumbnail)
        cropped = cv.CreateImage( (80, 80), thumbnail.depth, thumbnail.nChannels)
        for y in range(5):
            for x in range(5):
                src_region = cv.GetSubRect(thumbnail,(x*80, y*80, 80, 80) )
                cv.Copy(src_region, cropped)
                name=str(x)+str(y)
                cv.SaveImage(name +'.jpg',cropped)
 

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('image'):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('image'):
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def startDrag(self, event):
        c_item=self.currentItem()
        c_data=QtCore.QByteArray()
        c_Stream=QtCore.QDataStream(c_data,QtCore.QIODevice.WriteOnly)
        pixmap = QtGui.QPixmap(c_item.data(QtCore.Qt.UserRole))
        location = c_item.data(QtCore.Qt.UserRole+1)

        c_Stream << pixmap << location

        mimeData = QtCore.QMimeData()
        mimeData.setData('image', c_data)

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(QtCore.QPoint(pixmap.width()/2, pixmap.height()/2))
        drag.setPixmap(pixmap)

        if drag.exec_(QtCore.Qt.MoveAction) == QtCore.Qt.MoveAction:
            self.takeItem(self.row(c_item))


    def dropEvent(self, event):
        if event.mimeData().hasFormat('image'):
            c_data = event.mimeData().data('image')
            c_Stream = QtCore.QDataStream(c_Data, QtCore.QIODevice.ReadOnly)
            pixmap = QtGui.QPixmap()
            location = QtCore.QPoint()
            c_Stream >> pixmap >> location

            self.addPiece(pixmap, location)#needs editing

            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()
        else:
            event.ignore()


class Frame2(QtGui.QWidget):
    def __init__(self):
        super(Frame2,self).__init__()
        self.setAcceptDrops(True)
	self.piecePixmaps = []
        self.pieceRects = []
        self.pieceLocations = []
        self.highlightedRect = QtCore.QRect()
        self.inPlace = 0

        self.setMinimumSize(200, 200)
        self.setMaximumSize(400, 400)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('image'):
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        updateRect = self.highlightedRect
        self.highlightedRect = QtCore.QRect()
        self.update(updateRect)
        event.accept()

    def dragMoveEvent(self, event):
        updateRect = self.highlightedRect.unite(self.targetSquare(event.pos()))

        if event.mimeData().hasFormat('image') and self.findPiece(self.targetSquare(event.pos())) == -1:
            self.highlightedRect = self.targetSquare(event.pos())
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()
        else:
            self.highlightedRect = QtCore.QRect()
            event.ignore()

        self.update(updateRect)

    def dropEvent(self, event):
        if event.mimeData().hasFormat('image') and self.findPiece(self.targetSquare(event.pos())) == -1:
            pieceData = event.mimeData().data('image')
            c_Stream = QtCore.QDataStream(pieceData, QtCore.QIODevice.ReadOnly)
            square = self.targetSquare(event.pos())
            pixmap = QtGui.QPixmap()
            location = QtCore.QPoint()
            c_Stream >> pixmap >> location

            self.pieceLocations.append(location)
            self.piecePixmaps.append(pixmap)
            self.pieceRects.append(square)

            self.hightlightedRect = QtCore.QRect()
            self.update(square)

            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()

            if location == QtCore.QPoint(square.x() / 80, square.y() / 80):
                self.inPlace += 1
                if self.inPlace == 25:
                    self.puzzleCompleted.emit()
        else:
            self.highlightedRect = QtCore.QRect()
            event.ignore()

    def findPiece(self, pieceRect):
        try:
            return self.pieceRects.index(pieceRect)
        except ValueError:
            return -1

    def mousePressEvent(self, event):
        square = self.targetSquare(event.pos())
        found = self.findPiece(square)

        if found == -1:
            return

        location = self.pieceLocations[found]
        pixmap = self.piecePixmaps[found]
        del self.pieceLocations[found]
        del self.piecePixmaps[found]
        del self.pieceRects[found]

        if location == QtCore.QPoint(square.x() / 80, square.y() / 80):
            self.inPlace -= 1

        self.update(square)

        itemData = QtCore.QByteArray()
        c_Stream = QtCore.QDataStream(itemData, QtCore.QIODevice.WriteOnly)

        c_Stream << pixmap << location

        mimeData = QtCore.QMimeData()
        mimeData.setData('image', itemData)

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(event.pos() - square.topLeft())
        drag.setPixmap(pixmap)

        if drag.exec_(QtCore.Qt.MoveAction) != QtCore.Qt.MoveAction:
            self.pieceLocations.insert(found, location)
            self.piecePixmaps.insert(found, pixmap)
            self.pieceRects.insert(found, square)
            self.update(self.targetSquare(event.pos()))

            if location == QtCore.QPoint(square.x() / 80, square.y() / 80):
                self.inPlace += 1

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.fillRect(event.rect(), QtCore.Qt.white)

        if self.highlightedRect.isValid():
            painter.setBrush(QtGui.QColor("#ffcccc"))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(self.highlightedRect.adjusted(0, 0, -1, -1))

        for rect, pixmap in zip(self.pieceRects, self.piecePixmaps):
            painter.drawPixmap(rect, pixmap)

        painter.end()

    def targetSquare(self, position):
        return QtCore.QRect(position.x() // 80 * 80, position.y() // 80 * 80, 80, 80)		


class Puzzle_Window(QtGui.QMainWindow):
    def __init__(self):
        super(Puzzle_Window,self).__init__()
        self.setWindowTitle("Jigsaw Puzzle")

        frame=QtGui.QFrame()
        layout=QtGui.QVBoxLayout(frame)

        frame1=Frame1()
        frame2=Frame2()

        layout.addWidget(frame1)
        layout.addWidget(frame2)

        self.setCentralWidget(frame)

def main():
    app=QtGui.QApplication(sys.argv)
    puzzleWindow=Puzzle_Window()
    puzzleWindow.show()
    sys.exit(app.exec_())



if __name__=="__main__":
    main()
