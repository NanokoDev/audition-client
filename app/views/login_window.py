import sys
import keyring
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from qfluentwidgets import (
    InfoBar,
    LineEdit,
    CheckBox,
    BodyLabel,
    isDarkTheme,
    StateToolTip,
    setThemeColor,
    SubtitleLabel,
    SplitTitleBar,
    InfoBarPosition,
    PrimaryPushButton,
    TransparentPushButton,
)

from app.utils import isWin11


if isWin11():
    from qframelesswindow import AcrylicWindow as Window
else:
    from qframelesswindow import FramelessWindow as Window


class LoginWindow(Window):
    """Login window for the application"""

    loginSucceeded = pyqtSignal()
    loginRequested = pyqtSignal(str, str)  # username, password

    KEYRING_SERVICE = "nanoko-audition"
    KEYRING_USERNAME_KEY = "remembered_username"
    KEYRING_PASSWORD_KEY = "remembered_password"
    KEYRING_REMEMBER_KEY = "remember_enabled"

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._setupUi()
        self._loadSavedCredentials()

        setThemeColor("#000000")

        self.setWindowTitle("Audition Admin Login")
        self.setWindowIcon(QIcon("resources:icon.png"))

        self.resize(500, 400)
        self.setMinimumSize(400, 300)

        self.windowEffect.setMicaEffect(self.winId(), isDarkMode=isDarkTheme())
        if not isWin11():
            color = QColor(25, 33, 42) if isDarkTheme() else QColor(240, 244, 249)
            self.setStyleSheet(f"LoginWindow{{background: {color.name()}}}")

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
        self.centralWidget = QWidget()
        self.mainLayout = QVBoxLayout(self.centralWidget)
        self.mainLayout.setContentsMargins(30, 70, 30, 30)
        self.mainLayout.setSpacing(20)
        self.mainLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        self.titleLabel = SubtitleLabel("Audition Admin")
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mainLayout.addWidget(self.titleLabel)

        # Login form layout
        self.formWidget = QWidget()
        self.formLayout = QGridLayout(self.formWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setSpacing(10)

        # Username
        self.usernameLabel = BodyLabel("Username:")
        self.formLayout.addWidget(self.usernameLabel, 0, 0)

        self.usernameEdit = LineEdit()
        self.usernameEdit.setPlaceholderText("Enter username")
        self.formLayout.addWidget(self.usernameEdit, 0, 1)

        # Password
        self.passwordLabel = BodyLabel("Password:")
        self.formLayout.addWidget(self.passwordLabel, 1, 0)

        self.passwordEdit = LineEdit()
        self.passwordEdit.setPlaceholderText("Enter password")
        self.passwordEdit.setEchoMode(LineEdit.EchoMode.Password)
        self.formLayout.addWidget(self.passwordEdit, 1, 1)

        # Remember password
        self.rememberCheckbox = CheckBox("Remember password")
        self.formLayout.addWidget(self.rememberCheckbox, 2, 1)

        # Buttons
        self.buttonsLayout = QHBoxLayout()
        self.buttonsLayout.setSpacing(10)

        self.cancelButton = TransparentPushButton("Cancel")
        self.cancelButton.clicked.connect(self.close)
        self.buttonsLayout.addWidget(self.cancelButton)

        self.loginButton = PrimaryPushButton("Login")
        self.loginButton.clicked.connect(self._onLoginClicked)
        self.buttonsLayout.addWidget(self.loginButton)

        self.formLayout.addLayout(self.buttonsLayout, 3, 1, Qt.AlignmentFlag.AlignRight)

        # Add form to main layout
        self.mainLayout.addWidget(self.formWidget)

        # Set layout
        self.setLayout(self.mainLayout)

        # State tooltip
        self.stateTooltip = None

    def _loadSavedCredentials(self):
        """Load saved credentials if they exist"""
        try:
            remember_enabled = keyring.get_password(
                self.KEYRING_SERVICE, self.KEYRING_REMEMBER_KEY
            )
            if remember_enabled == "true":
                username = keyring.get_password(
                    self.KEYRING_SERVICE, self.KEYRING_USERNAME_KEY
                )
                password = keyring.get_password(
                    self.KEYRING_SERVICE, self.KEYRING_PASSWORD_KEY
                )

                if username and password:
                    self.usernameEdit.setText(username)
                    self.passwordEdit.setText(password)
                    self.rememberCheckbox.setChecked(True)
        except Exception:
            pass

    def _saveCredentials(self, username, password):
        """Save credentials to keyring

        Args:
            username (str): The username to save
            password (str): The password to save
        """
        try:
            keyring.set_password(
                self.KEYRING_SERVICE, self.KEYRING_USERNAME_KEY, username
            )
            keyring.set_password(
                self.KEYRING_SERVICE, self.KEYRING_PASSWORD_KEY, password
            )
            keyring.set_password(
                self.KEYRING_SERVICE, self.KEYRING_REMEMBER_KEY, "true"
            )
        except Exception:
            InfoBar.warning(
                title="Warning",
                content="Could not save credentials",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000,
            )

    def _clearSavedCredentials(self):
        """Clear saved credentials from keyring"""
        try:
            keyring.delete_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME_KEY)
            keyring.delete_password(self.KEYRING_SERVICE, self.KEYRING_PASSWORD_KEY)
            keyring.delete_password(self.KEYRING_SERVICE, self.KEYRING_REMEMBER_KEY)
        except Exception:
            pass

    def _onLoginClicked(self):
        """Handle login button click"""
        username = self.usernameEdit.text()
        password = self.passwordEdit.text()
        rememberPassword = self.rememberCheckbox.isChecked()

        if not username or not password:
            InfoBar.error(
                title="Error",
                content="Please enter both username and password",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000,
            )
            return

        if rememberPassword:
            self._saveCredentials(username, password)
        else:
            self._clearSavedCredentials()

        self._setFormEnabled(False)

        self.stateTooltip = StateToolTip("Logging in", "Please wait...", self)
        self.stateTooltip.move(
            self.width() // 2 - self.stateTooltip.width() // 2,
            self.height() // 2 - self.stateTooltip.height() // 2,
        )
        self.stateTooltip.show()

        self.loginRequested.emit(username, password)

    def onLoginFailed(self, errorMessage):
        """Handle login failure

        Args:
            errorMessage (str): The error message to display
        """
        if self.stateTooltip:
            self.stateTooltip.close()
            self.stateTooltip = None

        InfoBar.error(
            title="Error",
            content=errorMessage,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000,
        )
        self._setFormEnabled(True)

    def _setFormEnabled(self, enabled):
        """Enable or disable form elements

        Args:
            enabled (bool): Whether to enable or disable the form elements
        """
        self.usernameEdit.setEnabled(enabled)
        self.passwordEdit.setEnabled(enabled)
        self.rememberCheckbox.setEnabled(enabled)
        self.loginButton.setEnabled(enabled)
        self.cancelButton.setEnabled(enabled)
