# Form implementation generated from reading ui file 'd:\Desktop_Folders\SFU\Assignments\Summer 2022\CMPT 371\Project\ui\question_prompt.ui'
#
# Created by: PyQt6 UI code generator 6.3.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(700, 457)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setStyleSheet("QWidget {\n"
"background: #5F8BFF\n"
"}")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setSpacing(15)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.categoryLabel = QtWidgets.QLabel(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.categoryLabel.sizePolicy().hasHeightForWidth())
        self.categoryLabel.setSizePolicy(sizePolicy)
        self.categoryLabel.setMinimumSize(QtCore.QSize(0, 0))
        self.categoryLabel.setStyleSheet("QLabel {\n"
"    font-weight: 700;\n"
"    font-family: \'Lato\';\n"
"    font-size: 40px;\n"
"    color: #FFFFFF;\n"
"}")
        self.categoryLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.categoryLabel.setObjectName("categoryLabel")
        self.verticalLayout_2.addWidget(self.categoryLabel)
        self.verticalWidget = QtWidgets.QWidget(Form)
        self.verticalWidget.setStyleSheet("QWidget {\n"
"    background: #3B29FF;\n"
"    border-radius: 30px;\n"
"    color:white;\n"
"}")
        self.verticalWidget.setObjectName("verticalWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.questionLabel = QtWidgets.QLabel(self.verticalWidget)
        self.questionLabel.setStyleSheet("QLabel {\n"
"    font-family: \'CantoraOne\';\n"
"    font-size: 40px;\n"
"    text-align: center;\n"
"    font-weight: 400;\n"
"}")
        self.questionLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.questionLabel.setWordWrap(True)
        self.questionLabel.setObjectName("questionLabel")
        self.verticalLayout.addWidget(self.questionLabel)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.timerLabel = QtWidgets.QLabel(self.verticalWidget)
        self.timerLabel.setStyleSheet("QLabel {\n"
"    font-family: \'Lato\';\n"
"    font-style: normal;\n"
"    font-size: 50px;\n"
"}")
        self.timerLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.timerLabel.setObjectName("timerLabel")
        self.verticalLayout.addWidget(self.timerLabel)
        spacerItem2 = QtWidgets.QSpacerItem(20, 13, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.verticalLayout.addItem(spacerItem2)
        self.verticalLayout_2.addWidget(self.verticalWidget)
        self.answerLineEdit = QtWidgets.QLineEdit(Form)
        self.answerLineEdit.setMinimumSize(QtCore.QSize(0, 50))
        self.answerLineEdit.setStyleSheet("QLineEdit { \n"
"    background-color: white;\n"
"    color: black;\n"
"    border-radius: 13px;\n"
"    font: 15pt \"Inter\";\n"
"    margin: 0px 15px;\n"
"    padding: 0px 15px\n"
"}")
        self.answerLineEdit.setObjectName("answerLineEdit")
        self.verticalLayout_2.addWidget(self.answerLineEdit)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.categoryLabel.setText(_translate("Form", "NEWS TO ME"))
        self.questionLabel.setText(_translate("Form", "A 7.0 magnitude earthquake in this Caribbean country Jan. 12, 2010 brought a world outpouring of aid"))
        self.timerLabel.setText(_translate("Form", "0:30"))
        self.answerLineEdit.setPlaceholderText(_translate("Form", "Answer here"))
