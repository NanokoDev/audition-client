import sys
from PyQt6.QtGui import QPixmap, QIcon, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from nanoko.models.question import ConceptType, ProcessType, Question
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QScrollArea,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
)
from qfluentwidgets import (
    InfoBar,
    ComboBox,
    LineEdit,
    TextEdit,
    BodyLabel,
    FluentIcon,
    PushButton,
    ImageLabel,
    isDarkTheme,
    StateToolTip,
    SplitTitleBar,
    SubtitleLabel,
    setThemeColor,
    PlainTextEdit,
    InfoBarPosition,
    PrimaryPushButton,
    NavigationToolButton,
    SingleDirectionScrollArea,
)


from app.utils import isWin11


if isWin11():
    from qframelesswindow import AcrylicWindow as Window
else:
    from qframelesswindow import FramelessWindow as Window


class SubQuestionEditWindow(Window):
    """Window to edit a sub-question"""

    backToQuestionsRequested = pyqtSignal()
    loadDataRequested = pyqtSignal(int)  # question_id
    saveRequested = pyqtSignal(object)  # data
    loadImageRequested = pyqtSignal(int)  # image_id
    uploadImageRequested = pyqtSignal(
        str, int, int, str
    )  # file_path, image_id, sub_question_id, description
    questionApprovedRequested = pyqtSignal(int)  # question_id
    questionDeletedRequested = pyqtSignal(int)  # question_id

    def __init__(self, questionId, subQuestionIndex, parent=None):
        super().__init__(parent=parent)
        self.questionId = questionId
        self.subQuestionIndex = subQuestionIndex
        self.question = None
        self.subQuestion = None
        self.stateTooltip = None

        self._setupUi()

        setThemeColor("#000000")

        self.setWindowTitle("Audition Admin - Edit Sub-Question")
        self.setWindowIcon(QIcon("resources:icon.png"))

        self.resize(1000, 700)
        self.setMinimumSize(800, 600)

        self.windowEffect.setMicaEffect(self.winId(), isDarkMode=isDarkTheme())
        if not isWin11():
            color = QColor(25, 33, 42) if isDarkTheme() else QColor(240, 244, 249)
            self.setStyleSheet(f"SubQuestionEditWindow{{background: {color.name()}}}")

        if sys.platform == "darwin":
            self.setSystemTitleBarButtonVisible(True)
            self.titleBar.minBtn.hide()
            self.titleBar.maxBtn.hide()
            self.titleBar.closeBtn.hide()

        self.titleBar.titleLabel.setStyleSheet("""
            QLabel{
                background: transparent;
                font: 13px 'Segoe UI';
                padding: 0 4px;
                color: black
            }
        """)

    def _setupUi(self):
        # Title bar
        self.setTitleBar(SplitTitleBar(self))
        self.titleBar.raise_()

        # Main layout
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(30, 70, 30, 30)
        self.mainLayout.setSpacing(20)

        self._setupHeader()

        # Scroll area
        self.scrollArea = SingleDirectionScrollArea(orient=Qt.Orientation.Vertical)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scrollArea.setStyleSheet("""
            QAbstractScrollArea {
                background-color: transparent;
            }
            QWidget#scrollAreaWidgetContents {
                background-color: transparent;
            }
        """)
        self.scrollArea.enableTransparentBackground()

        # Form container
        self.formWidget = QWidget()
        self.formWidget.setStyleSheet("background: transparent")
        self.formLayout = QGridLayout(self.formWidget)
        self.formLayout.setContentsMargins(20, 0, 20, 0)
        self.formLayout.setSpacing(15)

        self._setupForm()

        self.scrollArea.setWidget(self.formWidget)
        self.mainLayout.addWidget(self.scrollArea)

        self._setupFooter()

    def _setupHeader(self):
        # Header layout
        self.headerLayout = QHBoxLayout()

        # Back button
        self.backButton = NavigationToolButton(icon=FluentIcon.LEFT_ARROW, parent=self)
        self.backButton.clicked.connect(self._onBackClicked)
        self.headerLayout.addWidget(self.backButton)

        # Title
        self.titleLabel = SubtitleLabel("Edit Sub-Question")
        self.headerLayout.addWidget(self.titleLabel)

        # Navigation buttons
        self.navButtonsLayout = QHBoxLayout()

        # Previous/Next question buttons
        self.prevQuestionButton = PushButton("< Prev Question")
        self.prevQuestionButton.clicked.connect(self._onPrevQuestionClicked)
        self.navButtonsLayout.addWidget(self.prevQuestionButton)

        # Previous/Next sub-question buttons
        self.prevSubQuestionButton = PushButton("< Prev Sub-Q")
        self.prevSubQuestionButton.clicked.connect(self._onPrevSubQuestionClicked)
        self.navButtonsLayout.addWidget(self.prevSubQuestionButton)

        self.nextSubQuestionButton = PushButton("Next Sub-Q >")
        self.nextSubQuestionButton.clicked.connect(self._onNextSubQuestionClicked)
        self.navButtonsLayout.addWidget(self.nextSubQuestionButton)

        self.nextQuestionButton = PushButton("Next Question >")
        self.nextQuestionButton.clicked.connect(self._onNextQuestionClicked)
        self.navButtonsLayout.addWidget(self.nextQuestionButton)

        # Push nav buttons to right
        self.headerLayout.addStretch(1)
        self.headerLayout.addLayout(self.navButtonsLayout)

        # Header to main layout
        self.mainLayout.addLayout(self.headerLayout)

    def _setupForm(self):
        row = 0

        # Name
        self.formLayout.addWidget(BodyLabel("Name:"), row, 0)
        self.nameEdit = LineEdit()
        self.nameEdit.setPlaceholderText("Enter name")
        self.formLayout.addWidget(self.nameEdit, row, 1)
        row += 1

        # Source
        self.formLayout.addWidget(BodyLabel("Source:"), row, 0)
        self.sourceLabel = BodyLabel("")
        self.formLayout.addWidget(self.sourceLabel, row, 1)
        row += 1

        # Question ID
        self.formLayout.addWidget(BodyLabel("Question ID:"), row, 0)
        self.questionIdLabel = BodyLabel("")
        self.formLayout.addWidget(self.questionIdLabel, row, 1)
        row += 1

        # Question Approved
        self.formLayout.addWidget(BodyLabel("Question Approved:"), row, 0)
        self.questionApprovedButton = PushButton("Approve")
        self.questionApprovedButton.clicked.connect(self._onQuestionApprovedClicked)
        self.formLayout.addWidget(self.questionApprovedButton, row, 1)
        row += 1

        # Question Deleted
        self.formLayout.addWidget(BodyLabel("Question Deleted:"), row, 0)
        self.questionDeletedButton = PushButton("Delete")
        self.questionDeletedButton.clicked.connect(self._onQuestionDeletedClicked)
        self.formLayout.addWidget(self.questionDeletedButton, row, 1)
        row += 1

        # Sub-Question ID
        self.formLayout.addWidget(BodyLabel("Sub-Question ID:"), row, 0)
        self.idLabel = BodyLabel("")
        self.formLayout.addWidget(self.idLabel, row, 1)
        row += 1

        # Description
        self.formLayout.addWidget(BodyLabel("Description:"), row, 0)
        self.descriptionEdit = TextEdit()
        self.descriptionEdit.setPlaceholderText("Enter description")
        self.descriptionEdit.setMinimumHeight(100)
        self.formLayout.addWidget(self.descriptionEdit, row, 1)
        row += 1

        # Answer
        self.formLayout.addWidget(BodyLabel("Answer:"), row, 0)
        self.answerEdit = TextEdit()
        self.answerEdit.setPlaceholderText("Enter answer")
        self.answerEdit.setMinimumHeight(100)
        self.formLayout.addWidget(self.answerEdit, row, 1)
        row += 1

        # Concept
        self.formLayout.addWidget(BodyLabel("Concept:"), row, 0)
        self.conceptComboBox = ComboBox()
        for concept in ConceptType:
            self.conceptComboBox.addItem(concept.name)
        self.formLayout.addWidget(self.conceptComboBox, row, 1)
        row += 1

        # Process
        self.formLayout.addWidget(BodyLabel("Process:"), row, 0)
        self.processComboBox = ComboBox()
        for process in ProcessType:
            self.processComboBox.addItem(process.name)
        self.formLayout.addWidget(self.processComboBox, row, 1)
        row += 1

        # Keywords
        self.formLayout.addWidget(BodyLabel("Keywords:"), row, 0)
        self.keywordsEdit = LineEdit()
        self.keywordsEdit.setPlaceholderText("Enter keywords (comma-separated)")
        self.formLayout.addWidget(self.keywordsEdit, row, 1)
        row += 1

        # Options
        self.formLayout.addWidget(BodyLabel("Options:"), row, 0)
        self.optionsEdit = TextEdit()
        self.optionsEdit.setPlaceholderText("Enter options (one per line)")
        self.optionsEdit.setMinimumHeight(100)
        self.formLayout.addWidget(self.optionsEdit, row, 1)
        row += 1

        # Image
        self.formLayout.addWidget(BodyLabel("Image:"), row, 0)
        self.imageLayout = QVBoxLayout()

        # Image preview
        self.imagePreview = ImageLabel()
        self.imagePreview.setMinimumSize(QSize(300, 200))
        self.imagePreview.setMaximumSize(QSize(600, 400))
        self.imagePreview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.imagePreview.setStyleSheet("border: 1px solid #555;")
        self.imagePreview.setPixmap(QPixmap())
        self.imageLayout.addWidget(self.imagePreview)

        # Image description
        self.imageDescription = PlainTextEdit()
        self.imageDescription.setPlaceholderText("Enter image description")
        self.imageLayout.addWidget(self.imageDescription)

        # Image buttons layout
        self.imageButtonsLayout = QHBoxLayout()

        # Upload button
        self.uploadImageButton = PrimaryPushButton("Upload Image")
        self.uploadImageButton.clicked.connect(self._onUploadImageClicked)
        self.imageButtonsLayout.addWidget(self.uploadImageButton)

        # Remove button
        self.removeImageButton = PushButton("Remove Image")
        self.removeImageButton.clicked.connect(self._onRemoveImageClicked)
        self.imageButtonsLayout.addWidget(self.removeImageButton)

        self.imageButtonsLayout.addStretch(1)
        self.imageLayout.addLayout(self.imageButtonsLayout)
        self.formLayout.addLayout(self.imageLayout, row, 1)
        row += 1

        self.formLayout.addItem(
            QSpacerItem(
                20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
            ),
            row,
            0,
            1,
            2,
        )

    def _setupFooter(self):
        self.footerLayout = QHBoxLayout()

        # Push buttons to right
        self.footerLayout.addStretch(1)

        # Cancel button
        self.cancelButton = PushButton("Cancel")
        self.cancelButton.clicked.connect(self._onBackClicked)
        self.footerLayout.addWidget(self.cancelButton)

        # Save button
        self.saveButton = PrimaryPushButton("Save")
        self.saveButton.clicked.connect(self._onSaveClicked)
        self.footerLayout.addWidget(self.saveButton)

        self.mainLayout.addLayout(self.footerLayout)

    def showLoadingState(self):
        """Show loading state"""
        self._setFormEnabled(False)

        if self.stateTooltip is not None:
            self.stateTooltip = StateToolTip("Loading", "Please wait...", self)
            self.stateTooltip.move(
                self.width() // 2 - self.stateTooltip.width() // 2,
                self.height() // 2 - self.stateTooltip.height() // 2,
            )
            self.stateTooltip.show()

    def showUploadingState(self):
        """Show uploading state"""
        if self.stateTooltip is not None:
            self.stateTooltip = StateToolTip("Uploading", "Please wait...", self)
            self.stateTooltip.move(
                self.width() // 2 - self.stateTooltip.width() // 2,
                self.height() // 2 - self.stateTooltip.height() // 2,
            )
            self.stateTooltip.show()

    def finishLoadingState(self):
        """Finish loading state"""
        if self.stateTooltip:
            self.stateTooltip.close()
            self.stateTooltip = None
        try:
            self._setFormEnabled(True)
        except Exception:
            pass

    def showSavingState(self):
        """Show saving state"""
        self._setFormEnabled(False)

        self.stateTooltip = StateToolTip("Saving", "Please wait...", self)
        self.stateTooltip.move(
            self.width() // 2 - self.stateTooltip.width() // 2,
            self.height() // 2 - self.stateTooltip.height() // 2,
        )
        self.stateTooltip.show()

    def onImageUploaded(self):
        """Handle successful image upload"""
        if self.subQuestion.image_id is not None:
            self.loadImageRequested.emit(self.subQuestion.image_id)

            self.stateTooltip.setContent("Image uploaded successfully")
            self.stateTooltip.setState(True)

            QTimer.singleShot(3000, self._onStateTooltipDone)

    def onQuestionApproved(self):
        """Handle question approved completion"""
        self.question.is_audited = True
        self.questionApprovedButton.setEnabled(False)

    def onQuestionDeleted(self):
        """Handle question deleted completion"""
        self.question.is_deleted = True
        self.questionDeletedButton.setEnabled(False)

    def showError(self, title, message):
        """Show error message

        Args:
            title (str): Title of the error message
            message (str): Message of the error
        """
        if self.stateTooltip:
            self.stateTooltip.close()
            self.stateTooltip = None

        self._setFormEnabled(True)

        InfoBar.error(
            title=title,
            content=str(message),
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000,
        )

    def onSaveSuccess(self, data):
        """Handle successful save

        Args:
            data (dict): Data of the saved sub-question
        """
        if self.stateTooltip:
            self.stateTooltip.setContent("Saved successfully")
            self.stateTooltip.setState(True)

            QTimer.singleShot(3000, self._onStateTooltipDone)

    def onSaveError(self, error):
        """Handle save error

        Args:
            error (str): Error message
        """
        self.showError("Save Failed", error)

    def _onStateTooltipDone(self):
        """Clean up state tooltip after completion"""
        self._setFormEnabled(True)
        if self.stateTooltip:
            try:
                self.stateTooltip.close()
            except Exception:
                pass
            self.stateTooltip = None

    def setQuestionData(self, question: Question):
        """Set question data and update UI

        Args:
            question (Question): Question data
        """
        self.question = question
        self.questionId = question.id

        self.subQuestionIndex = 0
        if len(self.question.sub_questions) > 0:
            self.subQuestion = self.question.sub_questions[0]
            self._populateForm()
        else:
            self.showError("Error", "No sub-questions available")

        if self.stateTooltip:
            self.stateTooltip.close()
            self.stateTooltip = None

        self._setFormEnabled(True)

    def setImage(self, image: bytes, description: str):
        """Set image to be displayed in the image preview

        Args:
            image (bytes): Image data
            description (str): Description of the image
        """
        pixmap = QPixmap()
        pixmap.loadFromData(image)
        self.imagePreview.setPixmap(pixmap)
        self.imageDescription.setPlainText(description)
        self.removeImageButton.setEnabled(True)

    def _populateForm(self):
        """Populate form with sub-question data"""
        self.nameEdit.setText(self.question.name)

        self.sourceLabel.setText(self.question.source)
        self.questionIdLabel.setText(str(self.question.id))

        self.questionApprovedButton.setEnabled(not self.question.is_audited)
        self.questionDeletedButton.setEnabled(not self.question.is_deleted)

        self.idLabel.setText(str(self.subQuestion.id))
        self.descriptionEdit.setPlainText(self.subQuestion.description)
        self.answerEdit.setPlainText(self.subQuestion.answer)

        conceptValue = self.subQuestion.concept.name
        for i in range(self.conceptComboBox.count()):
            if self.conceptComboBox.itemText(i) == conceptValue:
                self.conceptComboBox.setCurrentIndex(i)
                break

        processValue = self.subQuestion.process.name
        for i in range(self.processComboBox.count()):
            if self.processComboBox.itemText(i) == processValue:
                self.processComboBox.setCurrentIndex(i)
                break

        keywords = self.subQuestion.keywords
        self.keywordsEdit.setText(", ".join(keywords) if keywords else "")

        options = self.subQuestion.options
        self.optionsEdit.setPlainText("\n".join(options) if options else "")

        imageId = self.subQuestion.image_id
        if imageId is not None:
            self.loadImageRequested.emit(imageId)
            self.removeImageButton.setEnabled(True)
        else:
            self.imagePreview.setPixmap(QPixmap())
            self.removeImageButton.setEnabled(False)
            self.imageDescription.setPlainText("")

        self.titleLabel.setText(
            f"Edit Sub-Question {self.subQuestionIndex + 1} of {len(self.question.sub_questions)}"
        )

        self.prevQuestionButton.setEnabled(
            self.questionId is not None and self.questionId >= 1
        )
        self.prevSubQuestionButton.setEnabled(self.subQuestionIndex > 0)
        self.nextSubQuestionButton.setEnabled(
            self.subQuestionIndex < len(self.question.sub_questions) - 1
        )

    def _getFormData(self):
        """Get form data as a dict for saving"""
        keywords = [k.strip() for k in self.keywordsEdit.text().split(",") if k.strip()]
        options = [
            o.strip() for o in self.optionsEdit.toPlainText().split("\n") if o.strip()
        ]

        return {
            "sub_question_id": self.subQuestion.id,
            "question_id": self.questionId,
            "question_name": self.nameEdit.text(),
            "description": self.descriptionEdit.toPlainText(),
            "answer": self.answerEdit.toPlainText(),
            "concept": ConceptType[self.conceptComboBox.currentText()],
            "process": ProcessType[self.processComboBox.currentText()],
            "keywords": keywords,
            "options": options,
            "image_id": (
                self.subQuestion.image_id
                if not self.imagePreview.pixmap().isNull()
                else None
            ),  # If user removed the image, then image_id is None
            "image_description": (
                self.imageDescription.toPlainText()
                if not self.imagePreview.pixmap().isNull()
                else None
            ),
        }

    def _setFormEnabled(self, enabled):
        """Enable or disable form elements

        Args:
            enabled (bool): Whether to enable or disable the form elements
        """
        # Form fields
        self.nameEdit.setEnabled(enabled)
        self.descriptionEdit.setEnabled(enabled)
        self.answerEdit.setEnabled(enabled)
        self.conceptComboBox.setEnabled(enabled)
        self.processComboBox.setEnabled(enabled)
        self.keywordsEdit.setEnabled(enabled)
        self.optionsEdit.setEnabled(enabled)

        # Buttons
        self.uploadImageButton.setEnabled(enabled)
        self.removeImageButton.setEnabled(
            enabled and bool(self.subQuestion) and bool(self.subQuestion.image_id)
        )
        self.saveButton.setEnabled(enabled)
        self.cancelButton.setEnabled(enabled)

        # Navigation buttons
        self.backButton.setEnabled(enabled)
        self.prevQuestionButton.setEnabled(enabled)
        self.nextQuestionButton.setEnabled(enabled)
        self.prevSubQuestionButton.setEnabled(enabled and self.subQuestionIndex > 0)
        self.nextSubQuestionButton.setEnabled(
            enabled and self.subQuestionIndex < len(self.question.sub_questions) - 1
        )

    def _onBackClicked(self):
        """Handle back button click"""
        self.backToQuestionsRequested.emit()

    def _onPrevQuestionClicked(self):
        """Handle previous question button click"""
        self.loadDataRequested.emit(self.questionId - 1)

    def _onNextQuestionClicked(self):
        """Handle next question button click"""
        self.loadDataRequested.emit(self.questionId + 1)

    def _onPrevSubQuestionClicked(self):
        """Handle previous sub-question button click"""
        if self.subQuestionIndex > 0:
            self.subQuestionIndex -= 1
            self.subQuestion = self.question.sub_questions[self.subQuestionIndex]
            if self.subQuestion.image_id is not None:
                self.loadImageRequested.emit(self.subQuestion.image_id)
            else:
                self.imagePreview.setPixmap(QPixmap())
                self.removeImageButton.setEnabled(False)
            self._populateForm()

    def _onNextSubQuestionClicked(self):
        """Handle next sub-question button click"""
        if self.subQuestionIndex < len(self.question.sub_questions) - 1:
            self.subQuestionIndex += 1
            self.subQuestion = self.question.sub_questions[self.subQuestionIndex]
            if self.subQuestion.image_id is not None:
                self.loadImageRequested.emit(self.subQuestion.image_id)
            else:
                self.imagePreview.setPixmap(QPixmap())
                self.removeImageButton.setEnabled(False)
            self._populateForm()

    def _onUploadImageClicked(self):
        """Handle upload image button click"""
        filePath, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg)"
        )

        if filePath:
            self.uploadImageRequested.emit(
                filePath,
                self.subQuestion.image_id
                if self.subQuestion.image_id is not None
                else -1,
                self.subQuestion.id,
                self.imageDescription.toPlainText(),
            )

        else:
            InfoBar.error(
                title="Error",
                content="Failed to load image",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000,
            )

    def _onRemoveImageClicked(self):
        """Handle remove image button click"""
        self.imagePreview.setPixmap(QPixmap())
        self.removeImageButton.setEnabled(False)

    def _onQuestionApprovedClicked(self):
        """Handle question approved button click"""
        self.questionApprovedRequested.emit(self.questionId)

    def _onQuestionDeletedClicked(self):
        """Handle question deleted button click"""
        self.questionDeletedRequested.emit(self.questionId)

    def _onSaveClicked(self):
        """Handle save button click"""
        formData = self._getFormData()

        self.saveRequested.emit(formData)
