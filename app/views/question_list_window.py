import sys
from typing import List
from PyQt6.QtGui import QIcon, QColor
from nanoko.models.question import Question
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem
from qfluentwidgets import (
    InfoBar,
    BodyLabel,
    PushButton,
    FluentIcon,
    TableWidget,
    isDarkTheme,
    StateToolTip,
    IconInfoBadge,
    SubtitleLabel,
    SplitTitleBar,
    SearchLineEdit,
    InfoBarPosition,
    PrimaryPushButton,
)

from app.utils import isWin11


if isWin11():
    from qframelesswindow import AcrylicWindow as Window
else:
    from qframelesswindow import FramelessWindow as Window


class QuestionListWindow(Window):
    """Window to display a list of questions"""

    logoutRequested = pyqtSignal()
    editSubQuestionRequested = pyqtSignal(int, int)  # question_id, sub_question_index
    loadQuestionsRequested = pyqtSignal()  # Signal to request loading questions

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.questions: List[Question] = []
        self.filtered_questions: List[Question] = []

        self.page_size = 20
        self.current_page = 1
        self.total_pages = 1

        self.stateTooltip = None

        self._setupUi()

        self.setWindowTitle("Audition Admin - Questions")
        self.setWindowIcon(QIcon("resources:icon.png"))

        self.resize(900, 600)
        self.setMinimumSize(800, 500)

        self.windowEffect.setMicaEffect(self.winId(), isDarkMode=isDarkTheme())
        if not isWin11():
            color = QColor(25, 33, 42) if isDarkTheme() else QColor(240, 244, 249)
            self.setStyleSheet(f"QuestionListWindow{{background: {color.name()}}}")

        if sys.platform == "darwin":
            self.setSystemTitleBarButtonVisible(True)
            self.titleBar.minBtn.hide()
            self.titleBar.maxBtn.hide()
            self.titleBar.closeBtn.hide()

    def _setupUi(self):
        # Title bar
        self.setTitleBar(SplitTitleBar(self))
        self.titleBar.raise_()

        # Main layout
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 30, 0, 0)
        self.mainLayout.setSpacing(20)
        self.mainLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._setupQuestionListPage()

    def _setupQuestionListPage(self):
        # Main container widget
        self.contentWidget = QWidget()
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(30, 30, 30, 30)
        self.contentLayout.setSpacing(15)

        # Question list page
        self.questionListPage = QWidget()
        self.questionListLayout = QVBoxLayout(self.questionListPage)
        self.questionListLayout.setContentsMargins(0, 0, 0, 0)
        self.questionListLayout.setSpacing(15)

        # Header layout
        self.headerLayout = QHBoxLayout()

        # Title
        self.titleLabel = SubtitleLabel("Question List")
        self.headerLayout.addWidget(self.titleLabel)

        # Search
        self.searchEdit = SearchLineEdit(self)
        self.searchEdit.setPlaceholderText("Search questions...")
        self.searchEdit.textChanged.connect(self._onSearchTextChanged)
        self.headerLayout.addWidget(self.searchEdit)

        self.questionListLayout.addLayout(self.headerLayout)

        # Question table
        self.questionTable = TableWidget(self)
        self.questionTable.setColumnCount(5)
        self.questionTable.setHorizontalHeaderLabels(
            ["ID", "Source", "Audited", "Deleted", "Sub-Questions"]
        )
        self.questionTable.horizontalHeader().setStretchLastSection(True)
        self.questionTable.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.questionTable.setSelectionBehavior(
            TableWidget.SelectionBehavior.SelectRows
        )
        self.questionTable.cellDoubleClicked.connect(self._onQuestionDoubleClicked)

        self.questionListLayout.addWidget(self.questionTable)

        # Pagination controls
        self.paginationLayout = QHBoxLayout()

        # Page navigation
        self.prevPageButton = PushButton("Previous")
        self.prevPageButton.clicked.connect(self._onPrevPage)
        self.paginationLayout.addWidget(self.prevPageButton)

        self.pageLabel = BodyLabel("Page 1 of 1")
        self.paginationLayout.addWidget(self.pageLabel)

        self.nextPageButton = PushButton("Next")
        self.nextPageButton.clicked.connect(self._onNextPage)
        self.paginationLayout.addWidget(self.nextPageButton)

        self.paginationLayout.addStretch()

        # Refresh button
        self.refreshButton = PrimaryPushButton("Refresh")
        self.refreshButton.clicked.connect(self._onRefreshClicked)
        self.paginationLayout.addWidget(self.refreshButton)

        self.questionListLayout.addLayout(self.paginationLayout)
        self.contentLayout.addWidget(self.questionListPage)
        self.mainLayout.addWidget(self.contentWidget)

    def _updatePaginationControls(self):
        """Update pagination controls state"""
        self.prevPageButton.setEnabled(self.current_page > 1)
        self.nextPageButton.setEnabled(self.current_page < self.total_pages)
        self.pageLabel.setText(f"Page {self.current_page} of {self.total_pages}")

    def _onPrevPage(self):
        """Handle previous page button click"""
        if self.current_page > 1:
            self.current_page -= 1
            self._updatePaginationControls()
            self._displayCurrentPage()

    def _onNextPage(self):
        """Handle next page button click"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._updatePaginationControls()
            self._displayCurrentPage()

    def _updatePagination(self):
        """Update pagination state"""
        self.total_pages = max(
            1, (len(self.filtered_questions) + self.page_size - 1) // self.page_size
        )
        self.current_page = min(self.current_page, self.total_pages)
        self._updatePaginationControls()

    def _displayCurrentPage(self):
        """Display current page of questions"""
        self.questionTable.setRowCount(0)

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.filtered_questions))

        for question in self.filtered_questions[start_idx:end_idx]:
            row = self.questionTable.rowCount()
            self.questionTable.insertRow(row)

            # ID
            idItem = QTableWidgetItem(str(question.id))
            self.questionTable.setItem(row, 0, idItem)

            # Source
            sourceItem = QTableWidgetItem(question.source)
            self.questionTable.setItem(row, 1, sourceItem)

            # Audited
            statusItem = QTableWidgetItem()
            statusWidget = QWidget()
            statusLayout = QHBoxLayout(statusWidget)
            statusLayout.setContentsMargins(0, 0, 0, 0)
            statusLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            statusIcon = (
                IconInfoBadge.success(FluentIcon.ACCEPT_MEDIUM)
                if question.is_audited
                else IconInfoBadge.error(FluentIcon.CANCEL_MEDIUM)
            )
            statusIcon.setFixedSize(QSize(20, 20))
            statusLayout.addWidget(statusIcon)

            self.questionTable.setItem(row, 2, statusItem)
            self.questionTable.setCellWidget(row, 2, statusWidget)

            # Deleted
            deletedItem = QTableWidgetItem()
            deletedWidget = QWidget()
            deletedLayout = QHBoxLayout(deletedWidget)
            deletedLayout.setContentsMargins(0, 0, 0, 0)
            deletedLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            deletedIcon = (
                IconInfoBadge.error(FluentIcon.DELETE)
                if question.is_deleted
                else IconInfoBadge.info(FluentIcon.ACCEPT_MEDIUM)
            )
            deletedIcon.setFixedSize(QSize(20, 20))
            deletedLayout.addWidget(deletedIcon)

            self.questionTable.setItem(row, 3, deletedItem)
            self.questionTable.setCellWidget(row, 3, deletedWidget)

            # Sub-question
            subCount = len(question.sub_questions)
            countItem = QTableWidgetItem(
                f"{subCount} sub-questions" if subCount > 1 else "1 sub-question"
            )
            self.questionTable.setItem(row, 4, countItem)

    def populateQuestionTable(self, questions: List[Question]):
        """Populate the question table with data from API

        Args:
            questions (List[Question]): The questions to populate the table with
        """
        self.questions = questions
        self.filtered_questions = questions
        self._updatePagination()
        self._displayCurrentPage()
        self.finishLoadingState()

    def _onSearchTextChanged(self, text):
        """Filter questions based on search text

        Args:
            text (str): The search text
        """
        if not text:
            self.filtered_questions = self.questions
        else:
            self.filtered_questions = [
                q
                for q in self.questions
                if text.lower() in q.source.lower()
                or text in str(q.id)
                or text in ("yes" if q.is_audited else "no")
            ]

        self.current_page = 1
        self._updatePagination()
        self._displayCurrentPage()

    def _onQuestionDoubleClicked(self, row: int, column: int):
        """Handle double click on question row"""
        if row < len(self.filtered_questions):
            question = self.filtered_questions[
                (self.current_page - 1) * self.page_size + row
            ]
            questionId = question.id

            if question.sub_questions:
                self.editSubQuestionRequested.emit(questionId, 0)

    def showLoadingState(self):
        """Show loading state"""
        self.questionTable.setEnabled(False)
        self.refreshButton.setEnabled(False)
        self.searchEdit.setEnabled(False)

        self.stateTooltip = StateToolTip(
            "Loading", "Loading questions, please wait...", self
        )
        self.stateTooltip.move(
            self.width() // 2 - self.stateTooltip.width() // 2,
            self.height() // 2 - self.stateTooltip.height() // 2,
        )
        self.stateTooltip.show()

    def finishLoadingState(self):
        """Finish loading state"""
        self.questionTable.setEnabled(True)
        self.refreshButton.setEnabled(True)
        self.searchEdit.setEnabled(True)

        if self.stateTooltip:
            self.stateTooltip.close()
            self.stateTooltip = None

    def showError(self, title, message):
        """Show error message

        Args:
            title (str): The title of the error message
            message (str): The message of the error message
        """
        self.finishLoadingState()

        InfoBar.error(
            title=title,
            content=str(message),
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000,
        )

    def _onLogoutClicked(self):
        """Handle logout click"""
        self.logoutRequested.emit()

    def _onRefreshClicked(self):
        """Handle refresh button click"""
        self.loadQuestionsRequested.emit()
