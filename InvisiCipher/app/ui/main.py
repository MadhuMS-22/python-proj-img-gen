import os
import sys

import cv2
import shutil
import os
import sys
import re
import requests
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from auth_screen import show_auth_screen
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QMessageBox, QFileDialog, QDialog, QRadioButton, QButtonGroup, QLineEdit, QScrollArea, QSizePolicy


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.models.DEEP_STEGO.hide_image import hide_image
from app.models.DEEP_STEGO.reveal_image import reveal_image
from app.models.ESRGAN import RRDBNet_arch as arch
from app.models.encryption import aes, blowfish
from app.ui.components.backgroundwidget import BackgroundWidget
from app.ui.components.customtextbox import CustomTextBox

# Get the base directory for assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Project root (InvisiCipher/) two levels up from ui/
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
BACKEND_BASE_URL = "http://127.0.0.1:8000"

class MainAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # vars
        self.last_download_path = None
        self.current_user = None
        self.auth_token = None
        self.is_authenticated = False
        self.main_content = None
        self.blowfish_radio_dec = None
        self.aes_radio_dec = None
        self.key_text_box_of_dec = None
        self.enc_filepath = None
        self.dec_display_label = None
        self.download_dec_button = None
        self.dec_img_text_label = None
        self.enc_img_text_label = None
        self.key_text_box = None
        self.blowfish_radio = None
        self.aes_radio = None
        self.image_tobe_enc_filepath = None
        self.download_enc_button = None
        self.enc_display_label = None
        self.container_image_filepath = None
        self.secret_out_display_label = None
        self.container_display_label = None
        self.download_revealed_secret_image_button = None
        self.download_steg_button = None
        self.secret_image_filepath = None
        self.cover_image_filepath = None
        self.steg_display_label = None
        self.secret_display_label = None
        self.cover_display_label = None
        self.low_res_image_text_label = None
        self.image_label = None
        self.low_res_image_filepath = None
        self.download_HR_button = None

        # Set window properties
        self.setWindowTitle("ImageSteganography")
        self.setGeometry(200, 200, 1400, 800)
        self.setWindowIcon(QIcon(os.path.join(PROJECT_ROOT, "logo.png")))
        self.setStyleSheet("background-color: #2b2b2b;")
        # self.setWindowFlags(Qt.FramelessWindowHint)

        # Set up the main window layout
        main_layout = QHBoxLayout()

        # Create the side navigation bar
        side_navigation = BackgroundWidget()
        # Set sidebar background image from project root (vertical menu background)
        menubg_path = os.path.join(PROJECT_ROOT, "menubg.jpg")
        if os.path.exists(menubg_path):
            side_navigation.set_background_image(menubg_path)
        side_navigation.setObjectName("side_navigation")
        side_navigation.setFixedWidth(200)
        side_layout = QVBoxLayout()

        # label for logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(os.path.join(PROJECT_ROOT, "logo.png")).scaled(50, 50, Qt.KeepAspectRatio)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)

        # label for app name (avoid overflow in narrow sidebar)
        name_label = QLabel()
        name_label.setText("ImageSteganography")
        name_label.setWordWrap(True)
        name_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 800;")
        name_label.setAlignment(Qt.AlignCenter)

        # Create buttons for each option
        encryption_button = QPushButton("Encryption")
        decryption_button = QPushButton("Decryption")
        image_hiding_button = QPushButton("Image Hide")
        image_reveal_button = QPushButton("Image Reveal")
        super_resolution_button = QPushButton("Super Resolution")

        # Connect button signals to their corresponding slots
        encryption_button.clicked.connect(self.show_image_hide_page)
        decryption_button.clicked.connect(self.show_decryption_page)
        image_hiding_button.clicked.connect(self.show_image_hide_page)
        image_reveal_button.clicked.connect(self.show_reveal_page)
        super_resolution_button.clicked.connect(self.show_super_resolution_page)

        # Add buttons to the side navigation layout
        side_layout.addWidget(logo_label)
        side_layout.addWidget(name_label)
        side_layout.addSpacing(8)
        side_layout.addWidget(image_hiding_button)
        side_layout.addWidget(encryption_button)
        side_layout.addWidget(decryption_button)
        side_layout.addWidget(image_reveal_button)
        side_layout.addWidget(super_resolution_button)

        # Add logout/exit button based on authentication status
        logout_button = QPushButton("Exit")
        logout_button.setObjectName("logout_button")
        if self.is_authenticated:
            logout_button.setText("Logout")
            logout_button.clicked.connect(self.handle_logout)
        else:
            logout_button.clicked.connect(self.close)
        
        side_layout.addStretch()
        side_layout.addWidget(logout_button)

        # Set the layout for the side navigation widget
        side_navigation.setLayout(side_layout)

        # Create the main content area
        self.main_content = BackgroundWidget()
        self.main_content.setObjectName("main_content")
        # Set background image from project root bg.jpg
        bg_path = os.path.join(PROJECT_ROOT, "bg.jpg")
        if os.path.exists(bg_path):
            self.main_content.set_background_image(bg_path)
        self.main_layout = QVBoxLayout()
        self.main_content.setLayout(self.main_layout)

        # Add the side navigation and main content to the main window layout (scrollable)
        main_layout.addWidget(side_navigation)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setWidget(self.main_content)
        main_layout.addWidget(scroll_area)

        # Set the main window layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Show authentication screen on startup
        self.show_auth_screen()
        
        # Hide sidebar during authentication
        self.hide_sidebar()

    def show_image_reveal_page(self):
        # Only allow access if authenticated
        if not self.is_authenticated:
            self.show_auth_screen()
            return
            
        # Redirect to reveal page
        self.show_reveal_page()
        self.image_tobe_enc_filepath = None
        self.key_text_box = None
        self.enc_img_text_label = None
        # Clear the main window layout
        self.clear_main_layout()

    def show_image_hide_page(self):
        # Only allow access if authenticated
        if not self.is_authenticated:
            self.show_auth_screen()
            return
            
        # ensure bg applied
        bg_path = os.path.join(PROJECT_ROOT, "bg.jpg")
        if os.path.exists(bg_path):
            self.main_content.set_background_image(bg_path)
        self.image_tobe_enc_filepath = None
        self.key_text_box = None
        self.enc_img_text_label = None
        # Clear the main window layout
        self.clear_main_layout()

        # Add content to the super resolution page
        title_label = QLabel("<H2>Image Encryption</H2>")
        title_label.setStyleSheet("font-size: 24px; color: #ffffff;")
        title_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(title_label)

        # label layout
        label_layout = QHBoxLayout()

        method_text_label = QLabel("Select encryption method:")
        method_text_label.setAlignment(Qt.AlignVCenter)
        method_text_label.setStyleSheet("font-size: 16px; color: #c6c6c6; margin-bottom: 10px; font-weight: bold;")
        label_layout.addWidget(method_text_label)

        self.enc_img_text_label = QLabel("Select Image to be Encrypted:")
        self.enc_img_text_label.setAlignment(Qt.AlignCenter)
        self.enc_img_text_label.setStyleSheet("font-size: 16px; color: #c6c6c6; margin-bottom: 10px; font-weight: bold;")
        label_layout.addWidget(self.enc_img_text_label)

        label_layout_widget = QWidget()
        label_layout_widget.setLayout(label_layout)
        self.main_layout.addWidget(label_layout_widget)

        # Image  display layout
        image_display_layout = QHBoxLayout()

        radio_layout = QVBoxLayout()
        radio_layout.setAlignment(Qt.AlignLeft)
        self.aes_radio = QRadioButton("AES Encryption")
        self.aes_radio.setToolTip("Widely adopted symmetric-key block cipher with strong security and flexibility")

        self.blowfish_radio = QRadioButton("Blowfish Encryption")
        self.blowfish_radio.setToolTip("Fast, efficient symmetric-key block cipher with versatile key lengths")

        self.encryption_group = QButtonGroup(self)
        self.encryption_group.addButton(self.aes_radio)
        self.encryption_group.addButton(self.blowfish_radio)
        radio_layout.addWidget(self.blowfish_radio)
        radio_layout.addWidget(self.aes_radio)

        key_text_label = QLabel("<br><br><br>Enter the secret key")
        key_text_label.setStyleSheet("font-size: 18px; color: #ffffff; font-weight: bold;")
        radio_layout.addWidget(key_text_label)

        self.key_text_box = CustomTextBox()
        self.key_text_box.setFixedWidth(300)
        radio_layout.addWidget(self.key_text_box)

        radio_layout_widget = QWidget()
        radio_layout_widget.setLayout(radio_layout)
        image_display_layout.addWidget(radio_layout_widget)

        self.enc_display_label = QLabel()
        self.set_label_placeholder(self.enc_display_label, 256, 256, "Select the image")
        image_display_layout.addWidget(self.enc_display_label)

        image_display_layout_widget = QWidget()
        image_display_layout_widget.setLayout(image_display_layout)
        self.main_layout.addWidget(image_display_layout_widget)

        # button layout
        button_layout = QHBoxLayout()
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.show_encryption_page())
        button_layout.addWidget(clear_button)

        browse_enc_button = QPushButton("Browse image")
        browse_enc_button.clicked.connect(lambda: self.select_enc_image(self.enc_display_label))
        button_layout.addWidget(browse_enc_button)

        encrypt_button = QPushButton("Encrypt")
        encrypt_button.clicked.connect(lambda: self.perform_encryption(self.image_tobe_enc_filepath))
        button_layout.addWidget(encrypt_button)

        self.download_enc_button = QPushButton("Download🔽")
        self.download_enc_button.setEnabled(False)
        self.download_enc_button.clicked.connect(lambda: self.download_image())
        button_layout.addWidget(self.download_enc_button)

        button_layout_widget = QWidget()
        button_layout_widget.setLayout(button_layout)
        self.main_layout.addWidget(button_layout_widget)

    def show_decryption_page(self):
        bg_path = os.path.join(PROJECT_ROOT, "bg.jpg")
        if os.path.exists(bg_path):
            self.main_content.set_background_image(bg_path)
        self.key_text_box_of_dec = None
        # Clear the main window layout
        self.clear_main_layout()

        # Add content to the super resolution page
        title_label = QLabel("<H2>Image Decryption</H2>")
        title_label.setStyleSheet("font-size: 24px; color: #ffffff;")
        title_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(title_label)

        # label layout
        label_layout = QHBoxLayout()

        method_text_label = QLabel("Select Decryption method:")
        method_text_label.setAlignment(Qt.AlignVCenter)
        method_text_label.setStyleSheet("font-size: 16px; color: #c6c6c6; margin-bottom: 10px; font-weight: bold;")
        label_layout.addWidget(method_text_label)

        self.dec_img_text_label = QLabel("Select the file to be decrypted:")
        self.dec_img_text_label.setAlignment(Qt.AlignCenter)
        self.dec_img_text_label.setStyleSheet("font-size: 16px; color: #c6c6c6; margin-bottom: 10px; font-weight: bold;")
        label_layout.addWidget(self.dec_img_text_label)

        label_layout_widget = QWidget()
        label_layout_widget.setLayout(label_layout)
        self.main_layout.addWidget(label_layout_widget)

        # Image  display layout
        image_display_layout = QHBoxLayout()

        radio_layout = QVBoxLayout()
        radio_layout.setAlignment(Qt.AlignLeft)
        self.aes_radio_dec = QRadioButton("AES Decryption")
        self.aes_radio_dec.setToolTip("Widely adopted symmetric-key block cipher with strong security and flexibility")

        self.blowfish_radio_dec = QRadioButton("Blowfish Decryption")
        self.blowfish_radio_dec.setToolTip("Fast, efficient symmetric-key block cipher with versatile key lengths")

        self.decryption_group = QButtonGroup(self)
        self.decryption_group.addButton(self.aes_radio_dec)
        self.decryption_group.addButton(self.blowfish_radio_dec)
        radio_layout.addWidget(self.blowfish_radio_dec)
        radio_layout.addWidget(self.aes_radio_dec)

        key_text_label = QLabel("<br><br><br>Enter the secret key")
        key_text_label.setStyleSheet("font-size: 18px; color: #ffffff; font-weight: bold;")
        radio_layout.addWidget(key_text_label)

        self.key_text_box_of_dec = CustomTextBox()
        self.key_text_box_of_dec.setFixedWidth(300)
        radio_layout.addWidget(self.key_text_box_of_dec)

        radio_layout_widget = QWidget()
        radio_layout_widget.setLayout(radio_layout)
        image_display_layout.addWidget(radio_layout_widget)

        self.dec_display_label = QLabel()
        self.dec_display_label.setAlignment(Qt.AlignLeft)
        self.set_label_placeholder(self.dec_display_label, 256, 256, "Select the image")
        image_display_layout.addWidget(self.dec_display_label)

        image_display_layout_widget = QWidget()
        image_display_layout_widget.setLayout(image_display_layout)
        self.main_layout.addWidget(image_display_layout_widget)

        # button layout
        button_layout = QHBoxLayout()
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.show_decryption_page())
        button_layout.addWidget(clear_button)

        browse_enc_button = QPushButton("Browse encrypted file")
        browse_enc_button.clicked.connect(lambda: self.select_dec_image(self.dec_display_label))
        button_layout.addWidget(browse_enc_button)

        decrypt_button = QPushButton("Decrypt")
        decrypt_button.clicked.connect(lambda: self.perform_decryption(self.enc_filepath))
        button_layout.addWidget(decrypt_button)

        self.download_dec_button = QPushButton("Download🔽")
        self.download_dec_button.setEnabled(False)
        self.download_dec_button.clicked.connect(lambda: self.download_image())
        button_layout.addWidget(self.download_dec_button)

        button_layout_widget = QWidget()
        button_layout_widget.setLayout(button_layout)
        self.main_layout.addWidget(button_layout_widget)

    def show_image_hiding_page(self):
        bg_path = os.path.join(PROJECT_ROOT, "bg.jpg")
        if os.path.exists(bg_path):
            self.main_content.set_background_image(bg_path)
        self.secret_image_filepath = None
        self.cover_image_filepath = None
        # Clear the main window layout
        self.clear_main_layout()

        # Add content to the super resolution page
        title_label = QLabel("<H2>STEGO CNN : Steganography Hide</H2>")
        title_label.setStyleSheet("font-size: 24px; color: #ffffff;")
        title_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(title_label)

        # STEGO CNN model path label
        model_path_label = QLabel("<h5>Model Path: InvisiCipher/app/models/DEEP_STEGO/models/hide.h5</h5>")
        model_path_label.setStyleSheet("font-size: 16px; color: #c6c6c6;")
        model_path_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(model_path_label)

        # GPU Info
        gpu_info_label = QLabel("<b><ul><li>Device info will appear if available</li></ul></b>")
        gpu_info_label.setStyleSheet("font-size: 13px; color: #fae69e;")
        gpu_info_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(gpu_info_label)

        # label layout
        label_layout = QHBoxLayout()
        cover_text_label = QLabel("Select cover image:")
        cover_text_label.setAlignment(Qt.AlignCenter)
        cover_text_label.setStyleSheet("font-size: 16px; color: #c6c6c6; margin-bottom: 10px; font-weight: bold;")
        label_layout.addWidget(cover_text_label)

        secret_text_label = QLabel("Select secret image:")
        secret_text_label.setAlignment(Qt.AlignCenter)
        secret_text_label.setStyleSheet("font-size: 16px; color: #c6c6c6; margin-bottom: 10px; font-weight: bold;")
        label_layout.addWidget(secret_text_label)

        steg_text_label = QLabel("Generated steg image:")
        steg_text_label.setAlignment(Qt.AlignCenter)
        steg_text_label.setStyleSheet("font-size: 16px; color: #00ff00; margin-bottom: 10px; font-weight: bold;")
        label_layout.addWidget(steg_text_label)
        # keep a reference for status updates after hide
        self.steg_text_label = steg_text_label

        label_layout_widget = QWidget()
        label_layout_widget.setLayout(label_layout)
        self.main_layout.addWidget(label_layout_widget)

        # Image  display layout
        image_display_layout = QHBoxLayout()
        self.cover_display_label = QLabel()
        self.cover_display_label.setAlignment(Qt.AlignCenter)
        self.set_label_placeholder(self.cover_display_label, 256, 256, "Select the image")
        image_display_layout.addWidget(self.cover_display_label)

        self.secret_display_label = QLabel()
        self.secret_display_label.setAlignment(Qt.AlignCenter)
        self.set_label_placeholder(self.secret_display_label, 256, 256, "Select the image")
        image_display_layout.addWidget(self.secret_display_label)

        self.steg_display_label = QLabel()
        self.steg_display_label.setAlignment(Qt.AlignCenter)
        self.set_label_placeholder(self.steg_display_label, 256, 256, "Select the image")
        image_display_layout.addWidget(self.steg_display_label)

        image_display_layout_widget = QWidget()
        image_display_layout_widget.setLayout(image_display_layout)
        self.main_layout.addWidget(image_display_layout_widget)

        # button layout
        button_layout = QHBoxLayout()
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.show_image_hiding_page())
        button_layout.addWidget(clear_button)

        browse_cover_button = QPushButton("Browse cover image")
        browse_cover_button.clicked.connect(lambda: self.select_cover_image(self.cover_display_label))
        button_layout.addWidget(browse_cover_button)

        browse_secret_button = QPushButton("Browse secret image")
        browse_secret_button.clicked.connect(lambda: self.select_secret_image(self.secret_display_label))
        button_layout.addWidget(browse_secret_button)

        hide_button = QPushButton("Hide")
        hide_button.clicked.connect(lambda: self.perform_hide(self.cover_image_filepath, self.secret_image_filepath))
        button_layout.addWidget(hide_button)

        self.download_steg_button = QPushButton("Download steg image🔽")
        self.download_steg_button.setEnabled(False)
        self.download_steg_button.clicked.connect(lambda: self.download_image())
        button_layout.addWidget(self.download_steg_button)

        button_layout_widget = QWidget()
        button_layout_widget.setLayout(button_layout)
        self.main_layout.addWidget(button_layout_widget)

    def show_reveal_page(self):
        bg_path = os.path.join(PROJECT_ROOT, "bg.jpg")
        if os.path.exists(bg_path):
            self.main_content.set_background_image(bg_path)
        self.clear_main_layout()

        # Add content to the super resolution page
        title_label = QLabel("<H2>STEGO CNN : Steganography Reveal</H2>")
        title_label.setStyleSheet("font-size: 24px; color: #ffffff;")
        title_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(title_label)

        # STEGO CNN model path label
        model_path_label = QLabel("<h5>Model Path: InvisiCipher/app/models/DEEP_STEGO/models/reveal.h5</h5>")
        model_path_label.setStyleSheet("font-size: 16px; color: #c6c6c6;")
        model_path_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(model_path_label)

        # GPU Info
        gpu_info_label = QLabel("<b><ul><li>Device info will appear if available</li></ul></b>")
        gpu_info_label.setStyleSheet("font-size: 13px; color: #fae69e;")
        gpu_info_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(gpu_info_label)

        # image text layout
        image_text_layout = QHBoxLayout()
        container_text_label = QLabel("Select steg image:")
        container_text_label.setAlignment(Qt.AlignCenter)
        container_text_label.setStyleSheet("font-size: 16px; color: #c6c6c6; margin-bottom: 10px; font-weight: bold;")
        image_text_layout.addWidget(container_text_label)

        secret_out_text_label = QLabel("Revealed secret image:")
        secret_out_text_label.setAlignment(Qt.AlignCenter)
        secret_out_text_label.setStyleSheet("font-size: 16px; color: #00ff00; margin-bottom: 10px; font-weight: bold;")
        image_text_layout.addWidget(secret_out_text_label)
        # keep a reference for status updates after reveal
        self.secret_out_text_label = secret_out_text_label

        image_text_layout_widget = QWidget()
        image_text_layout_widget.setLayout(image_text_layout)
        self.main_layout.addWidget(image_text_layout_widget)
        
        # Image display layout
        image_layout = QHBoxLayout()
        self.container_display_label = QLabel()
        self.container_display_label.setAlignment(Qt.AlignCenter)
        self.set_label_placeholder(self.container_display_label, 256, 256, "Select the image")
        image_layout.addWidget(self.container_display_label)
        
        self.secret_out_display_label = QLabel()
        self.secret_out_display_label.setAlignment(Qt.AlignCenter)
        self.set_label_placeholder(self.secret_out_display_label, 256, 256, "Select the image")
        image_layout.addWidget(self.secret_out_display_label)

        image_layout_widget = QWidget()
        image_layout_widget.setLayout(image_layout)
        self.main_layout.addWidget(image_layout_widget)

        # button layout
        button_layout = QHBoxLayout()
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.show_reveal_page())
        button_layout.addWidget(clear_button)

        browse_cover_button = QPushButton("Browse steg image")
        browse_cover_button.clicked.connect(lambda: self.select_container_image(self.container_display_label))
        button_layout.addWidget(browse_cover_button)

        reveal_button = QPushButton("Reveal")
        reveal_button.clicked.connect(lambda: self.perform_reveal(self.container_image_filepath))
        button_layout.addWidget(reveal_button)

        self.download_revealed_secret_image_button = QPushButton("Download🔽")
        self.download_revealed_secret_image_button.setEnabled(False)
        self.download_revealed_secret_image_button.clicked.connect(lambda: self.download_image())
        button_layout.addWidget(self.download_revealed_secret_image_button)

    def show_super_resolution_page(self):
        # Only allow access if authenticated
        if not self.is_authenticated:
            self.show_auth_screen()
            return
            
        # ensure bg applied
        bg_path = os.path.join(PROJECT_ROOT, "bg.jpg")
        if os.path.exists(bg_path):
            self.main_content.set_background_image(bg_path)
        self.low_res_image_filepath = None
        # Clear the main window layout
        self.clear_main_layout()

        # Add content to the super resolution page
        title_label = QLabel("<H2>Enhanced Super Resolution using ESRGAN</H2>")
        title_label.setAlignment(Qt.AlignTop)
        title_label.setStyleSheet("font-size: 24px; color: #ffffff; margin-bottom: 20px;")
        self.main_layout.addWidget(title_label)

        # ESRGAN model path label
        model_path_label = QLabel("<h5>Model Path: InvisiCipher/app/models/ESRGAN/models/RRDB_ESRGAN_x4.pth</h5>")
        model_path_label.setStyleSheet("font-size: 16px; color: #c6c6c6; margin-bottom: 20px;")
        model_path_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(model_path_label)

        # GPU Info
        gpu_info_label = QLabel(
            "<b><ul><li>Device info will appear if available</li></ul></b>")
        gpu_info_label.setStyleSheet("font-size: 13px; color: #fae69e;")
        gpu_info_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(gpu_info_label)

        # Low resolution image selection
        low_res_label = QLabel("Select Low Resolution Image:")
        low_res_label.setAlignment(Qt.AlignCenter)
        low_res_label.setStyleSheet("font-size: 16px; color: #c6c6c6; margin-bottom: 10px; font-weight: bold;")
        self.main_layout.addWidget(low_res_label)

        # image display
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        self.set_label_placeholder(image_label, 384, 384, "Select the image")
        self.main_layout.addWidget(image_label)

        # defining button layout
        button_layout = QHBoxLayout()

        # Browse button
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.show_super_resolution_page())
        button_layout.addWidget(clear_button)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(lambda: self.select_low_resolution_image(image_label))
        button_layout.addWidget(browse_button)

        # Up-scale button
        upscale_button = QPushButton("UP-SCALE")
        upscale_button.clicked.connect(lambda: self.upscaleImage(image_label))
        button_layout.addWidget(upscale_button)

        # Download button
        download_button = QPushButton("Download🔽")
        download_button.setObjectName("download_button")
        download_button.setEnabled(False)
        download_button.clicked.connect(self.download_image)
        button_layout.addWidget(download_button)

        # add the button layout to the main layout
        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        self.main_layout.addWidget(button_widget)

        # Set the image labels as attributes
        self.low_res_image_text_label = low_res_label
        self.image_label = image_label
        self.download_HR_button = download_button

    def show_reveal_page(self):
        bg_path = os.path.join(PROJECT_ROOT, "bg.jpg")
        if os.path.exists(bg_path):
            self.main_content.set_background_image(bg_path)
        self.clear_main_layout()

        # Add content to the super resolution page
        title_label = QLabel("<H2>STEGO CNN : Steganography Reveal</H2>")
        title_label.setStyleSheet("font-size: 24px; color: #ffffff;")
        title_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(title_label)

        # STEGO CNN model path label
        model_path_label = QLabel("<h5>Model Path: InvisiCipher/app/models/DEEP_STEGO/models/reveal.h5</h5>")
        model_path_label.setStyleSheet("font-size: 16px; color: #c6c6c6;")
        model_path_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(model_path_label)

        # GPU Info
        gpu_info_label = QLabel("<b><ul><li>Device info will appear if available</li></ul></b>")
        gpu_info_label.setStyleSheet("font-size: 13px; color: #fae69e;")
        gpu_info_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(gpu_info_label)

        # image text layout
        image_text_layout = QHBoxLayout()
        container_text_label = QLabel("Select steg image:")
        container_text_label.setAlignment(Qt.AlignCenter)
        container_text_label.setStyleSheet("font-size: 16px; color: #c6c6c6; margin-bottom: 10px; font-weight: bold;")
        image_text_layout.addWidget(container_text_label)

        secret_out_text_label = QLabel("Revealed secret image:")
        secret_out_text_label.setAlignment(Qt.AlignCenter)
        secret_out_text_label.setStyleSheet("font-size: 16px; color: #00ff00; margin-bottom: 10px; font-weight: bold;")
        image_text_layout.addWidget(secret_out_text_label)
        # keep a reference for status updates after reveal
        self.secret_out_text_label = secret_out_text_label

        image_text_layout_widget = QWidget()
        image_text_layout_widget.setLayout(image_text_layout)
        self.main_layout.addWidget(image_text_layout_widget)
        
        # Image display layout
        image_layout = QHBoxLayout()
        self.container_display_label = QLabel()
        self.container_display_label.setAlignment(Qt.AlignCenter)
        self.set_label_placeholder(self.container_display_label, 256, 256, "Select the image")
        image_layout.addWidget(self.container_display_label)
        
        self.secret_out_display_label = QLabel()
        self.secret_out_display_label.setAlignment(Qt.AlignCenter)
        self.set_label_placeholder(self.secret_out_display_label, 256, 256, "Select the image")
        image_layout.addWidget(self.secret_out_display_label)

        image_layout_widget = QWidget()
        image_layout_widget.setLayout(image_layout)
        self.main_layout.addWidget(image_layout_widget)

        # button layout
        button_layout = QHBoxLayout()
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.show_reveal_page())
        button_layout.addWidget(clear_button)

        browse_cover_button = QPushButton("Browse steg image")
        browse_cover_button.clicked.connect(lambda: self.select_container_image(self.container_display_label))
        button_layout.addWidget(browse_cover_button)

        reveal_button = QPushButton("Reveal")
        reveal_button.clicked.connect(lambda: self.perform_reveal(self.container_image_filepath))
        button_layout.addWidget(reveal_button)

        self.download_revealed_secret_image_button = QPushButton("Download🔽")
        self.download_revealed_secret_image_button.setEnabled(False)
        self.download_revealed_secret_image_button.clicked.connect(lambda: self.download_image())
        button_layout.addWidget(self.download_revealed_secret_image_button)

        button_layout_widget = QWidget()
        button_layout_widget.setLayout(button_layout)
        self.main_layout.addWidget(button_layout_widget)

    def show_decryption_page(self):
        # Only allow access if authenticated
        if not self.is_authenticated:
            self.show_auth_screen()
            return
            
        # ensure bg applied
        bg_path = os.path.join(PROJECT_ROOT, "bg.jpg")
        if os.path.exists(bg_path):
            self.main_content.set_background_image(bg_path)
        
        self.clear_main_layout()

        # Add content to the decryption page
        title_label = QLabel("<H2>STEGO CNN : Steganography Decrypt</H2>")
        title_label.setStyleSheet("font-size: 24px; color: #ffffff;")
        title_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(title_label)

        # STEGO CNN model path label
        model_path_label = QLabel("<h5>Model Path: InvisiCipher/app/models/DEEP_STEGO/models/decrypt.h5</h5>")
        model_path_label.setStyleSheet("font-size: 16px; color: #c6c6c6;")
        model_path_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(model_path_label)

        # GPU Info
        gpu_info_label = QLabel("<b><ul><li>Device info will appear if available</li></ul></b>")
        gpu_info_label.setStyleSheet("font-size: 13px; color: #fae69e;")
        gpu_info_label.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(gpu_info_label)

        # label layout
        label_layout = QHBoxLayout()
        enc_text_label = QLabel("Select encrypted image:")
        enc_text_label.setAlignment(Qt.AlignCenter)
        enc_text_label.setStyleSheet("font-size: 16px; color: #c6c6c6; margin-bottom: 10px; font-weight: bold;")
        label_layout.addWidget(enc_text_label)

        dec_text_label = QLabel("Decrypted image:")
        dec_text_label.setAlignment(Qt.AlignCenter)
        dec_text_label.setStyleSheet("font-size: 16px; color: #00ff00; margin-bottom: 10px; font-weight: bold;")
        label_layout.addWidget(dec_text_label)

        label_layout_widget = QWidget()
        label_layout_widget.setLayout(label_layout)
        self.main_layout.addWidget(label_layout_widget)

        # Image  display layout
        image_display_layout = QHBoxLayout()
        self.enc_display_label = QLabel()
        self.enc_display_label.setAlignment(Qt.AlignCenter)
        self.set_label_placeholder(self.enc_display_label, 256, 256, "Select the image")
        image_display_layout.addWidget(self.enc_display_label)

        self.dec_display_label = QLabel()
        self.dec_display_label.setAlignment(Qt.AlignCenter)
        self.set_label_placeholder(self.dec_display_label, 256, 256, "Select the image")
        image_display_layout.addWidget(self.dec_display_label)

        image_display_layout_widget = QWidget()
        image_display_layout_widget.setLayout(image_display_layout)
        self.main_layout.addWidget(image_display_layout_widget)

        # button layout
        button_layout = QHBoxLayout()
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.show_decryption_page())
        button_layout.addWidget(clear_button)

        browse_enc_button = QPushButton("Browse encrypted file")
        browse_enc_button.clicked.connect(lambda: self.select_dec_image(self.dec_display_label))
        button_layout.addWidget(browse_enc_button)

        decrypt_button = QPushButton("Decrypt")
        decrypt_button.clicked.connect(lambda: self.perform_decryption(self.enc_filepath))
        button_layout.addWidget(decrypt_button)

        self.download_dec_button = QPushButton("Download🔽")
        self.download_dec_button.setEnabled(False)
        self.download_dec_button.clicked.connect(lambda: self.download_image())
        button_layout.addWidget(self.download_dec_button)

        button_layout_widget = QWidget()
        button_layout_widget.setLayout(button_layout)
        self.main_layout.addWidget(button_layout_widget)

    def show_auth_screen(self):
        """Show authentication screen on app startup"""
        show_auth_screen(self)

    def handle_logout(self):
        """Handle user logout"""
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Clear user session
            self.current_user = None
            self.auth_token = None
            self.is_authenticated = False
            
            # Update sidebar
            self.update_sidebar_auth_state()
            
            # Show authentication screen
            self.hide_sidebar()
            self.show_auth_screen()
            
            QMessageBox.information(self, "Logged Out", "You have been successfully logged out.")

    def show_login_page(self):
        # Set background image
        bg_path = os.path.join(PROJECT_ROOT, "bg.jpg")
        if os.path.exists(bg_path):
            self.main_content.set_background_image(bg_path)
        
        self.clear_main_layout()
        
        # Main container with fixed height to prevent scrolling
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Compact header section
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        logo = QLabel()
        lp = QPixmap(os.path.join(PROJECT_ROOT, "logo.png"))
        if not lp.isNull():
            logo.setPixmap(lp.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        
        name = QLabel("<h2 style='color: #ffffff; font-size: 26px; font-weight: bold; margin: 0;'>InvisiCipher</h2>")
        name.setAlignment(Qt.AlignCenter)
        name.setStyleSheet("color: #ffffff; margin: 0; padding: 0; background: transparent;")
        
        subtitle = QLabel("<p style='color: #cccccc; font-size: 16px; margin: 0;'>Secure Image Steganography</p>")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #cccccc; margin: 0; padding: 0; background: transparent;")
        
        header_layout.addWidget(logo)
        header_layout.addWidget(name)
        header_layout.addWidget(subtitle)
        
        # Login form container - optimal width for login form
        form_container = QWidget()
        optimal_width = min(450, int(self.width() * 0.35))
        form_container.setFixedWidth(max(350, optimal_width))
        form_container.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 40, 0.85);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(18)
        form_layout.setContentsMargins(30, 35, 30, 35)
        
        # Form title
        title = QLabel("<h3 style='color: #ffffff; font-size: 22px; font-weight: bold; text-align: center; margin: 0; border: none;'>Log In</h3>")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ffffff; margin-bottom: 15px; background: transparent; border: none;")
        
        # Form fields with larger labels
        id_label = QLabel("Username or Email")
        id_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 500; background: transparent; border: none;")
        id_input = CustomTextBox()
        id_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #555555;
                border-radius: 6px;
                background-color: rgba(60, 60, 60, 0.8);
                color: #ffffff;
                font-size: 13px;
                min-height: 16px;
            }
            QLineEdit:focus {
                border-color: #007acc;
                background-color: rgba(70, 70, 70, 0.9);
            }
        """)
        
        pwd_label = QLabel("Password")
        pwd_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 500; background: transparent; border: none;")
        pwd_input = CustomTextBox()
        pwd_input.setEchoMode(QLineEdit.Password)
        pwd_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #555555;
                border-radius: 6px;
                background-color: rgba(60, 60, 60, 0.8);
                color: #ffffff;
                font-size: 13px;
                min-height: 16px;
            }
            QLineEdit:focus {
                border-color: #007acc;
                background-color: rgba(70, 70, 70, 0.9);
            }
        """)
        
        submit = QPushButton("Log In")
        submit.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-height: 16px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        submit.clicked.connect(lambda: self._login_request(id_input.text(), pwd_input.text()))
        
        # Add widgets to form
        form_layout.addWidget(title)
        form_layout.addWidget(id_label)
        form_layout.addWidget(id_input)
        form_layout.addWidget(pwd_label)
        form_layout.addWidget(pwd_input)
        form_layout.addWidget(submit)
        
        # Center the form horizontally
        form_center_layout = QHBoxLayout()
        form_center_layout.addStretch()
        form_center_layout.addWidget(form_container)
        form_center_layout.addStretch()
        
        # Add sections with controlled spacing
        main_layout.addWidget(header_widget)
        main_layout.addLayout(form_center_layout)
        main_layout.addStretch()
        
        self.main_layout.addWidget(container)

    def show_signup_page(self):
        # Set background image
        bg_path = os.path.join(PROJECT_ROOT, "bg.jpg")
        if os.path.exists(bg_path):
            self.main_content.set_background_image(bg_path)
        
        self.clear_main_layout()
        
        # Main container with transparent background
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(10)

        # Compact header section
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(6)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        logo = QLabel()
        lp = QPixmap(os.path.join(PROJECT_ROOT, "logo.png"))
        if not lp.isNull():
            logo.setPixmap(lp.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        
        name = QLabel("<h3 style='color: #ffffff; font-size: 24px; font-weight: bold; margin: 0;'>InvisiCipher</h3>")
        name.setAlignment(Qt.AlignCenter)
        name.setStyleSheet("color: #ffffff; margin: 0; padding: 0; background: transparent;")
        
        subtitle = QLabel("<p style='color: #cccccc; font-size: 14px; margin: 0;'>Secure Image Steganography</p>")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #cccccc; margin: 0; padding: 0; background: transparent;")
        
        header_layout.addWidget(logo)
        header_layout.addWidget(name)
        header_layout.addWidget(subtitle)
        
        # Signup form container - optimal width for signup form
        form_container = QWidget()
        optimal_width = min(600, int(self.width() * 0.45))
        form_container.setFixedWidth(max(450, optimal_width))
        form_container.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 40, 0.85);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(30, 30, 30, 30)
        
        # Form title
        title = QLabel("<h4 style='color: #ffffff; font-size: 20px; font-weight: bold; text-align: center; margin: 0; border: none;'>Sign Up</h4>")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ffffff; margin-bottom: 12px; background: transparent; border: none;")
        
        # Compact input and label styles
        input_style = """
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #555555;
                border-radius: 5px;
                background-color: rgba(60, 60, 60, 0.8);
                color: #ffffff;
                font-size: 12px;
                min-height: 14px;
            }
            QLineEdit:focus {
                border-color: #007acc;
                background-color: rgba(70, 70, 70, 0.9);
            }
        """
        
        label_style = "color: #ffffff; font-size: 13px; font-weight: 500; background: transparent; border: none;"
        
        # Form fields with compact styling
        fn_label = QLabel("Full Name")
        fn_label.setStyleSheet(label_style)
        fn_input = CustomTextBox()
        fn_input.setStyleSheet(input_style)
        
        em_label = QLabel("Email Address")
        em_label.setStyleSheet(label_style)
        em_input = CustomTextBox()
        em_input.setStyleSheet(input_style)
        
        ph_label = QLabel("Phone Number")
        ph_label.setStyleSheet(label_style)
        ph_input = CustomTextBox()
        ph_input.setStyleSheet(input_style)
        
        un_label = QLabel("Username")
        un_label.setStyleSheet(label_style)
        un_input = CustomTextBox()
        un_input.setStyleSheet(input_style)
        
        pw_label = QLabel("Password")
        pw_label.setStyleSheet(label_style)
        pw_input = CustomTextBox()
        pw_input.setEchoMode(QLineEdit.Password)
        pw_input.setStyleSheet(input_style)
        
        cpw_label = QLabel("Confirm Password")
        cpw_label.setStyleSheet(label_style)
        cpw_input = CustomTextBox()
        cpw_input.setEchoMode(QLineEdit.Password)
        cpw_input.setStyleSheet(input_style)
        
        submit = QPushButton("Sign Up")
        submit.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
                min-height: 14px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        submit.clicked.connect(lambda: self._signup_request(fn_input.text(), em_input.text(), ph_input.text(), un_input.text(), pw_input.text(), cpw_input.text()))
        
        # Add widgets to form
        form_layout.addWidget(title)
        form_layout.addWidget(fn_label)
        form_layout.addWidget(fn_input)
        form_layout.addWidget(em_label)
        form_layout.addWidget(em_input)
        form_layout.addWidget(ph_label)
        form_layout.addWidget(ph_input)
        form_layout.addWidget(un_label)
        form_layout.addWidget(un_input)
        form_layout.addWidget(pw_label)
        form_layout.addWidget(pw_input)
        form_layout.addWidget(cpw_label)
        form_layout.addWidget(cpw_input)
        form_layout.addWidget(submit)
        
        # Center the form horizontally
        form_center_layout = QHBoxLayout()
        form_center_layout.addStretch()
        form_center_layout.addWidget(form_container)
        form_center_layout.addStretch()
        
        # Add sections with minimal spacing
        main_layout.addWidget(header_widget)
        main_layout.addLayout(form_center_layout)
        main_layout.addStretch()
        
        self.main_layout.addWidget(container)

    def _validate_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_phone(self, phone: str) -> bool:
        # Remove any non-digit characters and check if it's exactly 10 digits
        digits_only = re.sub(r'\D', '', phone)
        return len(digits_only) == 10 and digits_only.isdigit()
    
    def _signup_request(self, full_name: str, email: str, phone: str, username: str, password: str, confirm_password: str):
        # Validate required fields
        if not all([full_name, email, username, password]):
            QMessageBox.warning(self, "Sign Up Error", "Please fill in all required fields.")
            return
        
        # Validate email format
        if not self._validate_email(email):
            QMessageBox.warning(self, "Sign Up Error", "Please enter a valid email address.")
            return
        
        # Validate phone number (if provided)
        if phone and not self._validate_phone(phone):
            QMessageBox.warning(self, "Sign Up Error", "Please enter a valid 10-digit phone number.")
            return
        
        # Validate password confirmation
        if password != confirm_password:
            QMessageBox.warning(self, "Sign Up Error", "Passwords do not match. Please try again.")
            return
        
        # Validate password strength
        if len(password) < 8:
            QMessageBox.warning(self, "Sign Up Error", "Password must be at least 8 characters long.")
            return
            
        try:
            # Clean phone number - send empty string if not provided
            clean_phone = phone.strip() if phone and phone.strip() else ""
            
            payload = {
                "full_name": full_name.strip(),
                "email": email.strip(),
                "username": username.strip(),
                "password": password
            }
            
            # Only include phone if it's not empty
            if clean_phone:
                payload["phone"] = clean_phone
            
            print(f"DEBUG: Sending signup request: {payload}")  # Debug log
            
            r = requests.post(f"{BACKEND_BASE_URL}/api/auth/signup", json=payload, timeout=10)
            
            if r.status_code == 201:
                QMessageBox.information(self, "Sign Up Success", "Account created successfully! Please log in.")
                self.show_login_page()
            else:
                print(f"DEBUG: Signup failed with status {r.status_code}: {r.text}")  # Debug log
                try:
                    error_data = r.json()
                    if 'detail' in error_data:
                        if isinstance(error_data['detail'], list):
                            # Pydantic validation errors
                            error_msgs = []
                            for error in error_data['detail']:
                                field = error.get('loc', ['unknown'])[-1]
                                msg = error.get('msg', 'Invalid value')
                                error_msgs.append(f"{field}: {msg}")
                            error_msg = "Validation errors:\n" + "\n".join(error_msgs)
                        else:
                            error_msg = error_data['detail']
                    else:
                        error_msg = str(error_data)
                except:
                    error_msg = f"Registration failed (Status: {r.status_code})"
                QMessageBox.critical(self, "Sign Up Error", error_msg)
        except requests.exceptions.RequestException:
            QMessageBox.critical(self, "Connection Error", "Cannot connect to authentication server. Please ensure the backend is running.")
        except Exception as e:
            QMessageBox.critical(self, "Sign Up Error", str(e))

    def _login_request(self, identifier: str, password: str):
        if not identifier or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username/email and password.")
            return
            
        try:
            r = requests.post(f"{BACKEND_BASE_URL}/api/auth/login", json={
                "identifier": identifier,
                "password": password
            }, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                self.current_user = data.get('user')
                self.auth_token = data.get('token')
                self.is_authenticated = True
                QMessageBox.information(self, "Login Success", f"Welcome back, {self.current_user.get('username')}!")
                self.show_sidebar()
                self.update_sidebar_auth_state()
                self.show_home_page()
            else:
                print(f"DEBUG: Login failed with status {r.status_code}: {r.text}")  # Debug log
                
                if r.status_code == 401:
                    # Unauthorized - user doesn't exist or wrong credentials
                    reply = QMessageBox.question(
                        self, 
                        "Login Failed", 
                        "Invalid username/email or password.\n\nDon't have an account yet?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    if reply == QMessageBox.Yes:
                        self.show_signup_page()
                else:
                    # Other errors
                    try:
                        error_data = r.json()
                        error_msg = error_data.get('detail', f'Login failed (Status: {r.status_code})')
                    except:
                        error_msg = f'Login failed (Status: {r.status_code})'
                    QMessageBox.critical(self, "Login Error", error_msg)
        except requests.exceptions.RequestException:
            QMessageBox.critical(self, "Connection Error", "Cannot connect to authentication server. Please ensure the backend is running.")
        except Exception as e:
            QMessageBox.critical(self, "Login Error", str(e))

    def perform_hide(self, cover_filepath: str, secret_filepath: str):
        if not cover_filepath or not secret_filepath:
            QMessageBox.information(self, "Hiding Error", "Please select the cover and secret images first.")
            return
        try:
            steg_image_path = hide_image(cover_filepath, secret_filepath)
            self.set_label_image_box(self.steg_display_label, steg_image_path, 256, 256)
            self.download_steg_button.setEnabled(True)
            self.last_download_path = steg_image_path
            if hasattr(self, 'steg_text_label') and self.steg_text_label is not None:
                self.steg_text_label.setText("Image Hidden Successfully!")
                self.steg_text_label.setStyleSheet("font-size: 16px; color: #00ff00; margin-bottom: 10px; font-weight: bold;")
        except Exception as e:
            QMessageBox.critical(self, "Hiding Error", f"Failed to hide the image.\n{e}")

    def perform_reveal(self, filepath: str):
        if not filepath:
            QMessageBox.information(self, "Revealing Error", "Please select the steg image first.")
            return
        try:
            secret_out_filepath = reveal_image(filepath)
            self.set_label_image_box(self.secret_out_display_label, secret_out_filepath, 256, 256)
            self.download_revealed_secret_image_button.setEnabled(True)
            self.last_download_path = secret_out_filepath
            if hasattr(self, 'secret_out_text_label') and self.secret_out_text_label is not None:
                self.secret_out_text_label.setText("Image Revealed Successfully!")
                self.secret_out_text_label.setStyleSheet("font-size: 16px; color: #00ff00; margin-bottom: 10px; font-weight: bold;")
        except Exception as e:
            QMessageBox.critical(self, "Revealing Error", f"Failed to reveal the image.\n{e}")

    def perform_encryption(self, filepath: str):
        if not filepath:
            QMessageBox.information(self, "Encrypting Error", "Please select the image first.")
            return
        if not (self.aes_radio.isChecked() or self.blowfish_radio.isChecked()):
            QMessageBox.information(self, "Encrypting Error", "Please select an encryption method.")
            return
        if self.key_text_box.text() == "":
            QMessageBox.information(self, "Encrypting Error", "Please enter a secret key.")
            return
        try:
            if self.aes_radio.isChecked():
                aes.encrypt(filepath, self.key_text_box.text())
            else:
                blowfish.encrypt(filepath, self.key_text_box.text())
            # In both cases, the encrypted output is saved as original + '.enc'
            self.last_download_path = filepath + '.enc'
            self.download_enc_button.setEnabled(True)
            if self.enc_img_text_label is not None:
                self.enc_img_text_label.setText("Encrypted!")
                self.enc_img_text_label.setStyleSheet("font-size: 16px; color: #00ff00; margin-bottom: 10px; font-weight: bold;")
            self.key_text_box.setText("")
        except Exception as e:
            QMessageBox.critical(self, "Encrypting Error", f"Failed to encrypt the image.\n{e}")

    def perform_decryption(self, filepath: str):
        if not filepath:
            QMessageBox.information(self, "Decrypting Error", "Please select the encrypted file first.")
            return
        if not (self.aes_radio_dec.isChecked() or self.blowfish_radio_dec.isChecked()):
            QMessageBox.information(self, "Decrypting Error", "Please select a decryption method.")
            return
        if self.key_text_box_of_dec.text() == "":
            QMessageBox.information(self, "Decrypting Error", "Please enter a secret key.")
            return
        try:
            result = 0
            dec_filename = None
            if self.aes_radio_dec.isChecked():
                result, dec_filename = aes.decrypt(filepath, self.key_text_box_of_dec.text())
            else:
                result, dec_filename = blowfish.decrypt(filepath, self.key_text_box_of_dec.text())
            if result == -1 or not dec_filename:
                QMessageBox.critical(self, "Decrypting Error", "Wrong key or failed to decrypt.")
                return
            self.download_dec_button.setEnabled(True)
            if self.dec_img_text_label is not None:
                self.dec_img_text_label.setText("Decrypted!")
                self.dec_img_text_label.setStyleSheet("font-size: 16px; color: #00ff00; margin-bottom: 10px; font-weight: bold;")
            # Show decrypted output in the box
            self.set_label_image_box(self.dec_display_label, dec_filename, 256, 256)
            self.last_download_path = dec_filename
            self.key_text_box_of_dec.setText("")
        except Exception as e:
            QMessageBox.critical(self, "Decrypting Error", f"Failed to decrypt the file.\n{e}")

    def clear_main_layout(self):
        """Clear all widgets from the main layout"""
        if self.main_layout:
            while self.main_layout.count():
                child = self.main_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

    def show_home_page(self):
        """Show home page with authentication check"""
        # Only allow access to home page if authenticated
        if not self.is_authenticated:
            self.show_auth_screen()
            return
            
        self.clear_main_layout()
        # Apply page margins for full-width blocks
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        # Logo on home page
        logo_home = QLabel()
        lp = QPixmap(os.path.join(PROJECT_ROOT, "logo.png"))
        if not lp.isNull():
            logo_home.setPixmap(lp.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_home.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(logo_home)

        # Welcome message
        welcome_label = QLabel("<h1 style='color: #ffffff; text-align: center;'>Welcome to InvisiCipher</h1>")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("color: #ffffff; margin: 20px 0;")
        self.main_layout.addWidget(welcome_label)

        # Description
        desc_label = QLabel("<p style='color: #cccccc; text-align: center; font-size: 16px;'>Advanced Image Steganography and Encryption Platform</p>")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #cccccc; margin: 10px 0;")
        self.main_layout.addWidget(desc_label)

        # Features section
        features_title = QLabel("<h2 style='color: #ffffff; text-align: center;'>Available Features</h2>")
        features_title.setAlignment(Qt.AlignCenter)
        features_title.setStyleSheet("color: #ffffff; margin: 30px 0 20px 0;")
        self.main_layout.addWidget(features_title)

        # Create horizontal scrollable features row
        features_scroll = QScrollArea()
        features_row_container = QWidget()
        features_row_layout = QHBoxLayout(features_row_container)
        features_row_layout.setSpacing(20)
        features_row_layout.setContentsMargins(10, 10, 10, 10)

        # Feature cards
        features = [
            ("Image Hide", "Hide secret images within cover images using deep learning", self.show_image_hide_page),
            ("Image Reveal", "Extract hidden images from steganographic containers", self.show_reveal_page),
            ("Encryption", "Encrypt images with AES or Blowfish algorithms", self.show_image_hide_page),
            ("Decryption", "Decrypt protected images back to original form", self.show_decryption_page),
            ("Super Resolution", "Enhance image quality using ESRGAN technology", self.show_super_resolution_page)
        ]

        for title, description, handler in features:
            feature_card = QWidget()
            feature_card.setFixedSize(200, 150)
            feature_card.setStyleSheet("""
                QWidget {
                    background-color: rgba(40, 40, 40, 0.8);
                    border-radius: 10px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                QWidget:hover {
                    background-color: rgba(60, 60, 60, 0.9);
                    border: 1px solid rgba(220, 53, 69, 0.5);
                }
            """)
            
            card_layout = QVBoxLayout(feature_card)
            card_layout.setContentsMargins(15, 15, 15, 15)
            
            title_label = QLabel(f"<h3 style='color: #ffffff; margin: 0;'>{title}</h3>")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("color: #ffffff; background: transparent; border: none;")
            
            desc_label = QLabel(f"<p style='color: #cccccc; font-size: 12px; margin: 0;'>{description}</p>")
            desc_label.setAlignment(Qt.AlignCenter)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #cccccc; background: transparent; border: none;")
            
            card_layout.addWidget(title_label)
            card_layout.addWidget(desc_label)
            card_layout.addStretch()
            
            # Make card clickable
            feature_card.mousePressEvent = lambda event, h=handler: h()
            
            features_row_layout.addWidget(feature_card)

        features_row_layout.addStretch()
        
        # Configure scroll area
        features_scroll.setWidget(features_row_container)
        features_scroll.setWidgetResizable(True)
        features_scroll.setFrameShape(QScrollArea.NoFrame)
        features_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        features_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # make features scroll area transparent
        features_scroll.setStyleSheet("QScrollArea{background:transparent;} QScrollArea>Viewport{background:transparent;} QWidget{background:transparent;}")
        features_scroll.setMaximumHeight(180)
        self.main_layout.addWidget(features_scroll)

    def update_sidebar_auth_state(self):
        """Update sidebar buttons based on authentication state"""
        # Find the logout button and update it
        side_navigation = self.findChild(QWidget, "side_navigation")
        if side_navigation:
            logout_button = side_navigation.findChild(QPushButton, "logout_button")
            if logout_button:
                if self.is_authenticated:
                    logout_button.setText("Logout")
                    logout_button.clicked.disconnect()
                    logout_button.clicked.connect(self.handle_logout)
                else:
                    logout_button.setText("Exit")
                    logout_button.clicked.disconnect()
                    logout_button.clicked.connect(self.close)

    def load_stylesheet(self):
        """Load application stylesheet"""
        stylesheet_path = os.path.join(BASE_DIR, "styles", "style.qss")
        if os.path.exists(stylesheet_path):
            with open(stylesheet_path, 'r') as f:
                self.setStyleSheet(f.read())
        else:
            # Default dark theme if stylesheet not found
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QLabel {
                    color: #ffffff;
                }
            """)

    def set_label_placeholder(self, label, width, height, text):
        """Set placeholder image for label"""
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.gray)
        label.setPixmap(pixmap)
        label.setText(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("border: 2px dashed #666; color: #ccc;")

    def set_label_image_box(self, label, image_path, width, height):
        """Set image in label with proper scaling"""
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(scaled_pixmap)
                label.setStyleSheet("border: 1px solid #444;")
        except Exception as e:
            print(f"Error loading image: {e}")
            self.set_label_placeholder(label, width, height, "Error loading image")

    def select_image(self, label):
        """Select image file and display in label"""
        file_dialog = QFileDialog()
        filepath, _ = file_dialog.getOpenFileName(
            self, 
            "Select Image", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        if filepath:
            self.set_label_image_box(label, filepath, 256, 256)
            return filepath
        return None

    def select_cover_image(self, label):
        """Select cover image for steganography"""
        filepath = self.select_image(label)
        if filepath:
            self.cover_image_filepath = filepath

    def select_secret_image(self, label):
        """Select secret image for steganography"""
        filepath = self.select_image(label)
        if filepath:
            self.secret_image_filepath = filepath

    def select_container_image(self, label):
        """Select container image for reveal"""
        filepath = self.select_image(label)
        if filepath:
            self.container_image_filepath = filepath

    def select_dec_image(self, label):
        """Select encrypted image for decryption"""
        filepath = self.select_image(label)
        if filepath:
            self.enc_filepath = filepath

    def select_low_res_image(self, label):
        """Select low resolution image for super resolution"""
        filepath = self.select_image(label)
        if filepath:
            self.low_res_image_filepath = filepath

    def download_image(self):
        """Download the last processed image"""
        if hasattr(self, 'last_download_path') and self.last_download_path:
            file_dialog = QFileDialog()
            save_path, _ = file_dialog.getSaveFileName(
                self,
                "Save Image",
                "",
                "Image Files (*.png *.jpg *.jpeg)"
            )
            if save_path:
                try:
                    shutil.copy2(self.last_download_path, save_path)
                    QMessageBox.information(self, "Success", f"Image saved to {save_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save image: {e}")
        else:
            QMessageBox.warning(self, "No Image", "No image available for download")

    def hide_sidebar(self):
        """Hide the sidebar during authentication"""
        side_navigation = self.findChild(QWidget, "side_navigation")
        if side_navigation:
            side_navigation.hide()

    def show_sidebar(self):
        """Show the sidebar after authentication"""
        side_navigation = self.findChild(QWidget, "side_navigation")
        if side_navigation:
            side_navigation.show()


# Create the application
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
app = QApplication(sys.argv)
window = MainAppWindow()
window.load_stylesheet()
window.show()
sys.exit(app.exec_())
