    # def collide(self):
    #     items = pm.collidingItems()
        
    #     #items = self.items()
    #     #print("Intersections:", items)
    #     for item in items:
    #         # compute PCC
    #         if isinstance(item, QtWidgets.QGraphicsPixmapItem):
    #             i = item.pixmap().toImage()
    #             reference = i.convertToFormat(QtGui.QImage.Format.Format_RGB888).bits()
    #             height = i.height()
    #             width = i.width()
    #             reference.setsize(height * width * 3)
    #             rn = np.frombuffer(reference, np.uint8).reshape(width, height, 3)
    #             #i2 = pm.pixmap().toImage()
    #             #height = i2.height()
    #             #width = i2.width()
    #             #moving = i2.convertToFormat(QtGui.QImage.Format.Format_RGB888).constBits()
    #             #moving.setsize(height * width * 3)
    #             #rm = np.frombuffer(moving, np.uint8).reshape((width, height, 3))
    #             print(rn[0][0])
    #             #print(phase_cross_correlation(rn, rm))
