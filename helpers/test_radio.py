import sys
from PyQt5.QtWidgets import QApplication, QRadioButton, QWidget, QVBoxLayout
app = QApplication(sys.argv)
w = QWidget()
l = QVBoxLayout(w)
rb = QRadioButton("Radio Style Checkbox")
rb.setAutoExclusive(False)
l.addWidget(rb)
w.show()
sys.exit(app.exec_())
