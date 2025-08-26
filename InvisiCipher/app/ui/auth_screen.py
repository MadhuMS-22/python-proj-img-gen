import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

# Get project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

def show_auth_screen(main_window):
    """Show authentication screen on app startup"""
    main_window.clear_main_layout()
    
    # Main container
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    main_layout = QVBoxLayout(container)
    main_layout.setContentsMargins(50, 50, 50, 50)
    main_layout.setSpacing(30)
    
    # Header with logo and title
    header_widget = QWidget()
    header_widget.setStyleSheet("background: transparent;")
    header_layout = QVBoxLayout(header_widget)
    header_layout.setSpacing(15)
    header_layout.setContentsMargins(0, 0, 0, 0)
    
    logo = QLabel()
    lp = QPixmap(os.path.join(PROJECT_ROOT, "logo.png"))
    if not lp.isNull():
        logo.setPixmap(lp.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    logo.setAlignment(Qt.AlignCenter)
    
    title = QLabel("<h1 style='color: #ffffff; font-size: 36px; font-weight: bold; margin: 0;'>Welcome to InvisiCipher</h1>")
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet("color: #ffffff; margin: 0; padding: 0; background: transparent;")
    
    subtitle = QLabel("<p style='color: #cccccc; font-size: 18px; margin: 0;'>Secure Image Steganography Platform</p>")
    subtitle.setAlignment(Qt.AlignCenter)
    subtitle.setStyleSheet("color: #cccccc; margin: 0; padding: 0; background: transparent;")
    
    header_layout.addWidget(logo)
    header_layout.addWidget(title)
    header_layout.addWidget(subtitle)
    
    # Authentication buttons container
    auth_container = QWidget()
    auth_container.setStyleSheet("""
        QWidget {
            background-color: rgba(40, 40, 40, 0.85);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
    """)
    auth_container.setFixedWidth(400)
    
    auth_layout = QVBoxLayout(auth_container)
    auth_layout.setSpacing(20)
    auth_layout.setContentsMargins(40, 40, 40, 40)
    
    # Welcome message
    welcome_msg = QLabel("<h3 style='color: #ffffff; font-size: 20px; text-align: center; margin: 0;'>Get Started</h3>")
    welcome_msg.setAlignment(Qt.AlignCenter)
    welcome_msg.setStyleSheet("color: #ffffff; background: transparent; border: none;")
    
    # Login button
    login_btn = QPushButton("Log In")
    login_btn.clicked.connect(main_window.show_login_page)
    login_btn.setStyleSheet("""
        QPushButton {
            background-color: #dc3545;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
            min-height: 20px;
        }
        QPushButton:hover {
            background-color: #c82333;
        }
        QPushButton:pressed {
            background-color: #bd2130;
        }
    """)
    
    # Signup button
    signup_btn = QPushButton("Sign Up")
    signup_btn.clicked.connect(main_window.show_signup_page)
    signup_btn.setStyleSheet("""
        QPushButton {
            background-color: transparent;
            color: #ffffff;
            border: 2px solid #dc3545;
            padding: 15px 30px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
            min-height: 20px;
        }
        QPushButton:hover {
            background-color: rgba(220, 53, 69, 0.1);
            border-color: #c82333;
        }
        QPushButton:pressed {
            background-color: rgba(220, 53, 69, 0.2);
        }
    """)
    
    # Add widgets to auth container
    auth_layout.addWidget(welcome_msg)
    auth_layout.addWidget(login_btn)
    auth_layout.addWidget(signup_btn)
    
    # Center the auth container
    auth_center_layout = QHBoxLayout()
    auth_center_layout.addStretch()
    auth_center_layout.addWidget(auth_container)
    auth_center_layout.addStretch()
    
    # Add to main layout
    main_layout.addWidget(header_widget)
    main_layout.addLayout(auth_center_layout)
    main_layout.addStretch()
    
    main_window.main_layout.addWidget(container)
