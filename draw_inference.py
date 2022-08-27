        # if self.results:
        #     p = QtGui.QPainter()
        
        #     p.begin(image)
        #     p.setCompositionMode( QtGui.QPainter.CompositionMode_SourceOver )
        #     p.setRenderHints( QtGui.QPainter.HighQualityAntialiasing )

        #     pen1 = QtGui.QPen(QtCore.Qt.black)
        #     pen1.setWidth(2)
                
            
        #     pen2 = QtGui.QPen(QtCore.Qt.blue)
        #     pen2.setWidth(2)
        #     first = True
        #     for result in self.results['results']:
        #         prediction_score = result[0]
        #         label = result[1]
        #         box = result[2]
        #         p.setPen(pen1)
        #         box = QtCore.QRectF(QtCore.QPointF(*box[0]), QtCore.QPointF(*box[1]))
        #         p.drawRect(box)
        #         p.setPen(pen2)
        #         p.drawText(box.bottomRight(), "%5.2f %s" % (prediction_score, label))
        #         image_center = QtCore.QPointF(image.width()/2, image.height()/2)
        #         if label == 'tardigrade' and prediction_score == 1.0 and first:
        #             p.drawLine(image_center, box.center())
        #             first = False

        #     self.results = None
        #     p.end()