"""Main window for Virtual Controller Manager."""
import logging
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QStatusBar, QMenuBar
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QAction
from pathlib import Path

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""
    
    window_closed = pyqtSignal()

    def __init__(self, app_context):
        """Initialize main window."""
        super().__init__()
        self.app_context = app_context
        self.tabs = {}
        self.setWindowTitle("Virtual Controller Manager")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(QSize(1200, 800))
        
        self._apply_stylesheet()
        self._setup_ui()
        logger.info("Main window initialized")

    def _apply_stylesheet(self):
        """Apply QSS stylesheet."""
        try:
            styles_path = Path(__file__).parent / "styles.qss"
            if styles_path.exists():
                with open(styles_path, 'r') as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            logger.warning(f"Failed to load stylesheet: {e}")

    def _setup_ui(self):
        """Setup UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        self._setup_menu_bar()

    def _setup_menu_bar(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("&File")
        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def update_status(self, message: str):
        """Update status bar."""
        self.statusBar.showMessage(message)

    def closeEvent(self, event):
        """Handle window close."""
        self.window_closed.emit()
        event.accept()
