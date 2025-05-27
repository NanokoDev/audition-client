from nanoko import Nanoko
from nanoko.models.question import Question
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from app.views.login_window import LoginWindow
from app.views.question_list_window import QuestionListWindow
from app.views.sub_question_edit_window import SubQuestionEditWindow


class ApiWorker(QThread):
    """Worker thread for API operations"""

    loginFinished = pyqtSignal(bool, object)  # success, result/error
    questionsLoaded = pyqtSignal(bool, object)  # success, result/error
    questionLoaded = pyqtSignal(bool, object)  # success, result/error
    imageLoaded = pyqtSignal(bool, object)  # success, result/error
    imageUploaded = pyqtSignal(bool, object)  # success, result/error
    saveFinished = pyqtSignal(bool, object)  # success, result/error
    questionApproved = pyqtSignal(bool, object)  # success, result/error
    questionDeleted = pyqtSignal(bool, object)  # success, result/error

    def __init__(self, nanokoClient: Nanoko):
        super().__init__()
        self.nanokoClient = nanokoClient
        self.operation = None
        self.params = None

    def setup(self, operation, **params):
        """Setup the worker with operation and parameters

        Args:
            operation (str): The operation to perform
            **params: Additional parameters for the operation
        """
        self.operation = operation
        self.params = params

    def run(self):
        """Execute the operation in a separate thread"""
        if not self.operation:
            return

        try:
            # Login operation
            if self.operation == "login":
                self.nanokoClient.user.login(
                    username=self.params.get("username", ""),
                    password=self.params.get("password", ""),
                )
                self.loginFinished.emit(True, None)

            # Load questions list
            elif self.operation == "load_questions":
                questions = self.nanokoClient.bank.get_questions()
                self.questionsLoaded.emit(True, questions)

            # Load single question
            elif self.operation == "load_question":
                questionId = self.params.get("questionId")

                questions = self.nanokoClient.bank.get_questions(question_id=questionId)

                if not questions:
                    self.questionLoaded.emit(False, "Question not found")
                else:
                    self.questionLoaded.emit(True, questions[0])

            # Approve Question
            elif self.operation == "question_approved":
                questionId = self.params.get("questionId")
                self.nanokoClient.bank.approve_question(question_id=questionId)
                self.questionApproved.emit(True, None)

            # Delete Question
            elif self.operation == "question_deleted":
                questionId = self.params.get("questionId")
                self.nanokoClient.bank.delete_question(question_id=questionId)
                self.questionDeleted.emit(True, None)

            # Load image
            elif self.operation == "load_image":
                imageId = self.params.get("imageId")
                image = self.nanokoClient.bank.get_image(image_id=imageId)
                description = self.nanokoClient.bank.get_image_description(
                    image_id=imageId
                )
                self.imageLoaded.emit(
                    True, {"image": image, "description": description}
                )

            # Upload image
            elif self.operation == "upload_image":
                filePath = self.params.get("filePath")
                imageId = self.params.get("imageId")
                subQuestionId = self.params.get("subQuestionId")
                description = self.params.get(
                    "description", "Input the image description here"
                )

                imageHash = self.nanokoClient.bank.upload_image(file=filePath)

                if imageId != -1:
                    self.nanokoClient.bank.set_image_hash(
                        image_id=imageId, hash=imageHash
                    )
                else:
                    imageId = self.nanokoClient.bank.add_image(
                        hash=imageHash,
                        description=description,
                    )
                    self.nanokoClient.bank.set_sub_question_image(
                        sub_question_id=subQuestionId, image_id=imageId
                    )

                self.imageUploaded.emit(True, imageId)

            # Save sub-question
            elif self.operation == "save_sub_question":
                subQuestionData = self.params.get("data")

                questionId = subQuestionData.get("question_id")
                subQuestionId = subQuestionData.get("sub_question_id")
                questionName = subQuestionData.get("question_name")

                if questionName.strip() != "":
                    self.nanokoClient.bank.set_question_name(
                        question_id=questionId, name=questionName
                    )

                originalSubQuestions = self.nanokoClient.bank.get_questions(
                    question_id=questionId
                )

                if not originalSubQuestions:
                    self.saveFinished.emit(False, "Sub-question not found")

                originalSubQuestion = None

                for originalSubQuestion_ in originalSubQuestions[0].sub_questions:
                    if originalSubQuestion_.id == subQuestionId:
                        originalSubQuestion = originalSubQuestion_
                        break

                if originalSubQuestion is None:
                    self.saveFinished.emit(False, "Sub-question not found")
                    return

                originalImageDescription = self.nanokoClient.bank.get_image_description(
                    image_id=originalSubQuestion.image_id
                )

                if (
                    originalSubQuestion.image_id is not None
                    and originalImageDescription.strip()
                    != subQuestionData.get("image_description").strip()
                ):
                    self.nanokoClient.bank.set_image_description(
                        image_id=originalSubQuestion.image_id,
                        description=subQuestionData.get("image_description"),
                    )

                if (
                    originalSubQuestion.image_id is not None
                    and subQuestionData.get("image_id") is None
                ):
                    self.nanokoClient.bank.delete_sub_question_image(
                        sub_question_id=subQuestionId
                    )

                if (
                    originalSubQuestion.description.strip()
                    != subQuestionData.get("description").strip()
                ):
                    self.nanokoClient.bank.set_sub_question_description(
                        sub_question_id=subQuestionId,
                        description=subQuestionData.get("description"),
                    )

                if (
                    originalSubQuestion.answer.strip()
                    != subQuestionData.get("answer").strip()
                ):
                    self.nanokoClient.bank.set_sub_question_answer(
                        sub_question_id=subQuestionId,
                        answer=subQuestionData.get("answer"),
                    )

                if originalSubQuestion.concept != subQuestionData.get("concept"):
                    self.nanokoClient.bank.set_sub_question_concept(
                        sub_question_id=subQuestionId,
                        concept=subQuestionData.get("concept"),
                    )

                if originalSubQuestion.process != subQuestionData.get("process"):
                    self.nanokoClient.bank.set_sub_question_process(
                        sub_question_id=subQuestionId,
                        process=subQuestionData.get("process"),
                    )

                if originalSubQuestion.keywords != subQuestionData.get("keywords"):
                    self.nanokoClient.bank.set_sub_question_keywords(
                        sub_question_id=subQuestionId,
                        keywords=subQuestionData.get("keywords"),
                    )

                if (originalSubQuestion.options or []) != (
                    subQuestionData.get("options")
                ):
                    self.nanokoClient.bank.set_sub_question_options(
                        sub_question_id=subQuestionId,
                        options=subQuestionData.get("options"),
                    )

                self.saveFinished.emit(True, subQuestionData)

        except Exception as e:
            if self.operation == "login":
                self.loginFinished.emit(False, str(e))
            elif self.operation == "load_questions":
                self.questionsLoaded.emit(False, str(e))
            elif self.operation == "load_question":
                self.questionLoaded.emit(False, str(e))
            elif self.operation == "load_image":
                self.imageLoaded.emit(False, str(e))
            elif self.operation == "upload_image":
                self.imageUploaded.emit(False, str(e))
            elif self.operation == "save_sub_question":
                self.saveFinished.emit(False, str(e))


class MainController(QObject):
    """Main controller to manage application flow"""

    def __init__(self):
        super().__init__()

        self.loginWindow = None
        self.questionListWindow = None
        self.subQuestionEditWindow = None

        self.setupNanokoClient()
        self.apiWorker = ApiWorker(self.nanokoClient)
        self.setupApiWorkerConnections()

    def setupApiWorkerConnections(self):
        """Setup connections for API worker signals"""
        self.apiWorker.loginFinished.connect(self.onLoginFinished)
        self.apiWorker.questionsLoaded.connect(self.onQuestionsLoaded)
        self.apiWorker.questionLoaded.connect(self.onQuestionLoaded)
        self.apiWorker.imageLoaded.connect(self.onImageLoaded)
        self.apiWorker.imageUploaded.connect(self.onImageUploaded)
        self.apiWorker.saveFinished.connect(self.onSaveFinished)
        self.apiWorker.questionApproved.connect(self.onQuestionApproved)
        self.apiWorker.questionDeleted.connect(self.onQuestionDeleted)

    def setupNanokoClient(self):
        """Setup nanoko client for API interaction"""
        self.nanokoClient = Nanoko(base_url="http://localhost:25324")

    def start(self):
        """Start the application flow"""
        self.showLoginWindow()

    def showLoginWindow(self):
        """Show the login window"""
        if self.questionListWindow:
            self.questionListWindow.close()
            self.questionListWindow = None

        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.close()
            self.subQuestionEditWindow = None

        self.loginWindow = LoginWindow()
        self.loginWindow.loginRequested.connect(self.performLogin)
        self.loginWindow.show()

    def performLogin(self, username, password):
        """Perform login in a separate thread

        Args:
            username (str): The username to login with
            password (str): The password to login with
        """
        self.apiWorker.setup("login", username=username, password=password)
        self.apiWorker.start()

    @pyqtSlot(bool, object)
    def onLoginFinished(self, success, result):
        """Handle login completion

        Args:
            success (bool): Whether the login was successful
            result (object): The result of the login
        """
        if success:
            self.showQuestionListWindow()
        else:
            self.loginWindow.onLoginFailed(result)

    def showQuestionListWindow(self):
        """Show the question list window"""
        if self.loginWindow:
            self.loginWindow.close()
            self.loginWindow = None

        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.close()
            self.subQuestionEditWindow = None

        self.questionListWindow = QuestionListWindow()
        self.questionListWindow.logoutRequested.connect(self.showLoginWindow)
        self.questionListWindow.editSubQuestionRequested.connect(
            self.showSubQuestionEditWindow
        )
        self.questionListWindow.loadQuestionsRequested.connect(self.loadQuestions)
        self.questionListWindow.show()

        self.loadQuestions()

    def loadQuestions(self):
        """Load questions in a separate thread"""
        if self.questionListWindow:
            self.questionListWindow.showLoadingState()
            self.apiWorker.setup("load_questions")
            self.apiWorker.start()

    @pyqtSlot(bool, object)
    def onQuestionsLoaded(self, success, result):
        """Handle questions loading completion

        Args:
            success (bool): Whether the questions were loaded successfully
            result (object): The result of the questions loading
        """
        if self.questionListWindow:
            if success:
                self.questionListWindow.finishLoadingState()
                self.questionListWindow.questions = result
                self.questionListWindow.populateQuestionTable(result)
            else:
                self.questionListWindow.showError("Failed to load questions", result)

    def showSubQuestionEditWindow(self, questionId, subQuestionIndex):
        """Show the sub-question edit window

        Args:
            questionId (int): The ID of the question to edit
            subQuestionIndex (int): The index of the sub-question to edit
        """
        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.close()
            self.subQuestionEditWindow = None

        self.subQuestionEditWindow = SubQuestionEditWindow(questionId, subQuestionIndex)

        self.subQuestionEditWindow.backToQuestionsRequested.connect(
            self.showQuestionListWindow
        )
        self.subQuestionEditWindow.loadDataRequested.connect(self.loadQuestionData)
        self.subQuestionEditWindow.saveRequested.connect(self.saveSubQuestion)
        self.subQuestionEditWindow.loadImageRequested.connect(self.loadImage)
        self.subQuestionEditWindow.uploadImageRequested.connect(self.uploadImage)
        self.subQuestionEditWindow.questionApprovedRequested.connect(
            self.questionApproved
        )
        self.subQuestionEditWindow.questionDeletedRequested.connect(
            self.questionDeleted
        )

        self.subQuestionEditWindow.show()
        self.loadQuestionData(questionId)

    def loadQuestionData(self, questionId):
        """Load question data in a separate thread

        Args:
            questionId (int): The ID of the question to load
        """
        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.showLoadingState()
            self.apiWorker.setup("load_question", questionId=questionId)
            self.apiWorker.start()

    @pyqtSlot(bool, object)
    def onQuestionLoaded(self, success, result: Question):
        """Handle question loading completion

        Args:
            success (bool): Whether the question was loaded successfully
            result (Question): The result of the question loading
        """
        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.finishLoadingState()
            if success:
                self.subQuestionEditWindow.setQuestionData(result)
            else:
                self.subQuestionEditWindow.showError("Failed to load question", result)

    @pyqtSlot(bool, object)
    def onImageLoaded(self, success, result):
        """Handle image loading completion

        Args:
            success (bool): Whether the image was loaded successfully
            result (object): The result of the image loading
        """
        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.finishLoadingState()
            if success:
                self.subQuestionEditWindow.setImage(
                    result["image"], result["description"]
                )
            else:
                self.subQuestionEditWindow.showError("Failed to load image", result)

    @pyqtSlot(bool, object)
    def onImageUploaded(self, success, result):
        """Handle image upload completion

        Args:
            success (bool): Whether the image was uploaded successfully
            result (object): The result of the image upload
        """
        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.finishLoadingState()
            if success:
                self.subQuestionEditWindow.subQuestion.image_id = result
                self.subQuestionEditWindow.onImageUploaded()
            else:
                self.subQuestionEditWindow.showError("Failed to upload image", result)

    @pyqtSlot(bool, object)
    def onQuestionApproved(self, success, result):
        """Handle question approved completion

        Args:
            success (bool): Whether the question was approved successfully
            result (object): The result of the question approval
        """
        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.finishLoadingState()

            if success:
                self.subQuestionEditWindow.onQuestionApproved()
            else:
                self.subQuestionEditWindow.showError(
                    "Failed to approve question", result
                )

    @pyqtSlot(bool, object)
    def onQuestionDeleted(self, success, result):
        """Handle question deleted completion

        Args:
            success (bool): Whether the question was deleted successfully
            result (object): The result of the question deletion
        """
        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.finishLoadingState()

            if success:
                self.subQuestionEditWindow.onQuestionDeleted()
            else:
                self.subQuestionEditWindow.showError(
                    "Failed to delete question", result
                )

    def saveSubQuestion(self, data):
        """Save sub-question data in a separate thread

        Args:
            data (object): The data to save
        """
        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.showSavingState()
            self.apiWorker.setup("save_sub_question", data=data)
            self.apiWorker.start()

    def loadImage(self, imageId):
        """Load image in a separate thread

        Args:
            imageId (int): The ID of the image to load
        """
        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.showLoadingState()
            self.apiWorker.setup("load_image", imageId=imageId)
            self.apiWorker.start()

    def uploadImage(self, filePath, imageId, subQuestionId, description):
        """Upload image in a separate thread

        Args:
            filePath (str): The path to the image file
            imageId (int): The ID of the image to upload
            subQuestionId (int): The ID of the sub-question to upload the image to
            description (str): The description of the image
        """
        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.showUploadingState()
            self.apiWorker.setup(
                "upload_image",
                filePath=filePath,
                imageId=imageId,
                subQuestionId=subQuestionId,
                description=description,
            )
            self.apiWorker.start()

    def questionApproved(self, questionId):
        """Handle question approved completion

        Args:
            questionId (int): The ID of the question to approve
        """
        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.showLoadingState()
            self.apiWorker.setup("question_approved", questionId=questionId)
            self.apiWorker.start()

    def questionDeleted(self, questionId):
        """Handle question deleted completion

        Args:
            questionId (int): The ID of the question to delete
        """
        if self.subQuestionEditWindow:
            self.subQuestionEditWindow.showLoadingState()
            self.apiWorker.setup("question_deleted", questionId=questionId)
            self.apiWorker.start()

    @pyqtSlot(bool, object)
    def onSaveFinished(self, success, result):
        """Handle save completion

        Args:
            success (bool): Whether the save was successful
            result (object): The result of the save
        """
        if self.subQuestionEditWindow:
            if success:
                self.subQuestionEditWindow.onSaveSuccess(result)
            else:
                self.subQuestionEditWindow.onSaveError(result)
