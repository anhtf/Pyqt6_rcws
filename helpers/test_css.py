import sys
from PyQt5.QtWidgets import QApplication, QCheckBox, QWidget, QVBoxLayout
app = QApplication(sys.argv)
w = QWidget()
l = QVBoxLayout(w)
cb = QCheckBox("Radio Style Checkbox")
cb.setStyleSheet("""
QCheckBox {
    font-family: Arial;
    font-size: 14px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border-radius: 8px; /* bằng một nửa của 14+1+1 */
    border: 2px solid #757575;
    background-color: white;
}
QCheckBox::indicator:checked {
    border: 2px solid #009688;
    background-color: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #009688, stop:0.6 #009688, stop:0.75 transparent, stop:1 transparent);
}
""")
l.addWidget(cb)
w.show()
sys.exit(app.exec_())
