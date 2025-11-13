import datetime
import os, sys, time
import ssl
from attr import s
import serial
from serial.tools import list_ports
import random
ssl._create_default_https_context = ssl._create_unverified_context

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    running_mode = 'Frozen/executable'
else:
    try:
        app_full_path = os.path.realpath(__file__)
        application_path = os.path.dirname(app_full_path)
        running_mode = "Non-interactive"
    except NameError:
        application_path = os.getcwd()
        running_mode = 'Interactive'
logger_name = f'app.log'
logger_dir = os.path.join(application_path, "logs")

from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemanddock')

from kivy.logger import Logger
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager
from kivymd.font_definitions import theme_font_styles
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivy.metrics import dp
from kivymd.toast import toast
from kivymd.app import MDApp
import numpy as np
import configparser, hashlib, mysql.connector
from pymodbus.client import ModbusTcpClient
from fpdf import FPDF

colors = {
    "Red"   : {"A200": "#FF2A2A","A500": "#FF8080","A700": "#FFD5D5",},
    "Gray"  : {"200": "#CCCCCC","500": "#ECECEC","700": "#F9F9F9",},
    "Blue"  : {"200": "#4471C4","500": "#5885D8","700": "#6C99EC",},
    "Green" : {"200": "#2CA02C","500": "#2DB97F", "700": "#D5FFD5",},
    "Yellow": {"200": "#ffD42A","500": "#ffE680","700": "#fff6D5",},
    "Light" : {"StatusBar": "E0E0E0","AppBar": "#202020","Background": "#EEEEEE","CardsDialogs": "#FFFFFF","FlatButtonDown": "#CCCCCC",},
    "Dark"  : {"StatusBar": "101010","AppBar": "#E0E0E0","Background": "#111111","CardsDialogs": "#222222","FlatButtonDown": "#DDDDDD",},
}

config_name = 'config.ini'
config_full_path = os.path.join(application_path, config_name)
config = configparser.ConfigParser()
config.read(config_full_path)

## App Setting
APP_TITLE = config['app']['APP_TITLE']
APP_SUBTITLE = config['app']['APP_SUBTITLE']
IMG_LOGO_PEMKAB = config['app']['IMG_LOGO_PEMKAB']
IMG_LOGO_DISHUB = config['app']['IMG_LOGO_DISHUB']
LB_PEMKAB = config['app']['LB_PEMKAB']
LB_DISHUB = config['app']['LB_DISHUB']
LB_UNIT = config['app']['LB_UNIT']
LB_UNIT_ADDRESS = config['app']['LB_UNIT_ADDRESS']

# SQL setting
DB_HOST = "156.67.217.60"
DB_USER = "pkbsorong2024!"
DB_PASSWORD = "@Sorongpkb2024"
DB_NAME = "dishub"

TB_DATA = "tb_cekident"
TB_USER = "users"
TB_MERK = "merk"
TB_BAHAN_BAKAR = "bahanbakar"
TB_WARNA = "warna"
TB_DATA_MASTER = "identkendaraan"

FTP_HOST = "194.31.53.37"
FTP_USER = "root"
FTP_PASS = "@D15HUBp2022!"

## System Setting
COUNT_STARTING_GASS = int(config['setting']['COUNT_STARTING_GASS'])
COUNT_STARTING_DIESEL = int(config['setting']['COUNT_STARTING_DIESEL'])
COM_PORT = config['setting']['SERIAL_COM_GASS']
BAUD_RATE = int(config['setting']['SERIAL_BAUD_GASS'])
TIMEOUT = float(config['setting']['SERIAL_TIMEOUT_GASS'])

CMD_STATUS = b'\x1bST\r\n'
CMD_START_MEASURE = b'\x1b\x1bK5\r\n'
CMD_STOP_MEASURE = b'\x1b\x1bK2\r\n'
CMD_GET_DATA = b'\x1bCA\r\n'

PRINTER_THERM_COM = str(config['setting']['PRINTER_THERM_COM'])
PRINTER_THERM_BAUD = int(config['setting']['PRINTER_THERM_BAUD'])
PRINTER_THERM_BYTESIZE = int(config['setting']['PRINTER_THERM_BYTESIZE'])
PRINTER_THERM_PARITY = str(config['setting']['PRINTER_THERM_PARITY'])
PRINTER_THERM_STOPBITS = int(config['setting']['PRINTER_THERM_STOPBITS'])
PRINTER_THERM_TIMEOUT = float(config['setting']['PRINTER_THERM_TIMEOUT'])
PRINTER_THERM_DSRDTR = bool(config['setting']['PRINTER_THERM_DSRDTR'])

## system standard
STANDARD_MAX_HC = float(config['standard']['STANDARD_MAX_HC']) 
STANDARD_MAX_CO = float(config['standard']['STANDARD_MAX_CO'])
STANDARD_MAX_SMOKE = float(config['standard']['STANDARD_MAX_SMOKE'])

class ScreenHome(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenHome, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)
    
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE        
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        Clock.schedule_interval(self.regular_update_carousel, 3)

    def on_leave(self):
        Clock.unschedule(self.regular_update_carousel)

    def regular_update_carousel(self, dt):
        try:
            self.ids.carousel.index += 1

        except Exception as e:
            toast_msg = f'Gagal Memperbaharui Tampilan Carousel'
            toast_msg = f'Error Update Carousel: {e}'
            toast(toast_msg)                

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Error Navigate to Home Screen: {e}'
            toast(toast_msg)        

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast(f"Anda sudah login sebagai {dt_user}")

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Login'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

class ScreenLogin(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenLogin, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)
    
    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE  
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def exec_cancel(self):
        try:
            self.ids.tx_username.text = ""
            self.ids.tx_password.text = ""    
        except Exception as e:
            toast_msg = f'error Login: {e}'

    def exec_login(self):
        global mydb, db_users
        global dt_id_user, dt_user, dt_foto_user
        screen_main = self.screen_manager.get_screen('screen_main')

        try:
            screen_main.exec_reload_database()
            input_username = self.ids.tx_username.text
            input_password = self.ids.tx_password.text        
            dataBase_password = input_password
            hashed_password = hashlib.md5(dataBase_password.encode())
            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT id_user, nama, username, password, image FROM {TB_USER} WHERE username = '{input_username}' and password = '{hashed_password.hexdigest()}'")
            myresult = mycursor.fetchone()
            db_users = np.array(myresult).T
            
            if myresult is None:
                toast_msg = f'Gagal Masuk, Nama Pengguna atau Password Salah'
                toast(toast_msg) 
                Logger.warning(f"{self.name}: {toast_msg}") 
            else:
                toast_msg = f'Berhasil Masuk, Selamat Datang {myresult[1]}'
                toast(toast_msg)
                Logger.info(f"{self.name}: {toast_msg}")  
                dt_id_user = myresult[0]
                dt_user = myresult[1]
                dt_foto_user = myresult[4]
                self.ids.tx_username.text = ""
                self.ids.tx_password.text = "" 
                self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Gagal masuk, silahkan isi nama user dan password yang sesuai'
            toast(toast_msg)  
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Awal'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast_msg = f"Anda sudah login sebagai {dt_user}"
                toast(toast_msg)
                Logger.info(f"{self.name}: {toast_msg}")  

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Login'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")  

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Gagal Berpindah ke Halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

class ScreenMain(MDScreen):   
    def __init__(self, **kwargs):
        super(ScreenMain, self).__init__(**kwargs)
        global dt_user, dt_foto_user, dt_no_antri, dt_no_pol, dt_no_uji, dt_sts_uji, dt_nama
        global dt_merk, dt_type, dt_jns_kend, dt_jbb, dt_brt_ksg, dt_bhn_bkr, dt_warna, dt_chasis, dt_no_mesin
        global dt_id_user
        global emission_hc_value, emission_hc_flag
        global emission_co_value, emission_co_flag
        global emission_smoke_value, emission_smoke_flag
        global dt_dash_pendaftaran, dt_dash_belum_uji, dt_dash_sudah_uji

        dt_user = dt_foto_user = dt_no_antri = dt_no_pol = dt_no_uji = dt_sts_uji = dt_nama = ""
        dt_merk = dt_type = dt_jns_kend = dt_jbb = dt_brt_ksg = dt_bhn_bkr = dt_warna = dt_chasis = dt_no_mesin = ""
        dt_id_user = 1
        dt_dash_pendaftaran = dt_dash_belum_uji = dt_dash_sudah_uji = 0
        
        emission_hc_value = emission_hc_flag = 0
        emission_co_value = emission_co_flag = 0
        emission_smoke_value = emission_smoke_flag = 0

        Clock.schedule_once(self.delayed_init, 1)

    def delayed_init(self, dt):   
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE              
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS
        
        Clock.schedule_interval(self.regular_update_display, 1)

    def on_enter(self):
        self.exec_reload_database()
        self.exec_reload_table()

    def regular_update_display(self, dt):
        try:
            current_time = str(time.strftime("%H:%M:%S", time.localtime()))
            current_date = str(time.strftime("%d/%m/%Y", time.localtime()))
            
            screens_to_update = ['screen_home', 'screen_login', 'screen_gass_emission', 'screen_diesel_emission']
            for screen_name in screens_to_update:
                screen = self.screen_manager.get_screen(screen_name)
                screen.ids.lb_time.text = current_time
                screen.ids.lb_date.text = current_date

            self.ids.lb_time.text = current_time
            self.ids.lb_date.text = current_date
            self.ids.lb_dash_pendaftaran.text = str(dt_dash_pendaftaran)
            self.ids.lb_dash_belum_uji.text = str(dt_dash_belum_uji)
            self.ids.lb_dash_sudah_uji.text = str(dt_dash_sudah_uji)
            
            login_text = f'Login Sebagai: \n{dt_user}' if dt_user else 'Silahkan Login'
            user_image = f'https://{FTP_HOST}/ujikir/foto_user/{dt_foto_user}' if dt_user else 'assets/images/icon-login.png'

            for screen_name in ['screen_home', 'screen_login', 'screen_gass_emission', 'screen_diesel_emission']:
                try:
                    screen = self.screen_manager.get_screen(screen_name)
                    screen.ids.lb_operator.text = login_text
                    if hasattr(screen.ids, 'img_user'):
                        screen.ids.img_user.source = user_image
                except (KeyError, AttributeError):
                    pass
            
            self.ids.lb_operator.text = login_text
            self.ids.img_user.source = user_image
            self.ids.bt_logout.disabled = not dt_user

        except Exception as e:
            toast('Gagal Memperbaharui Tampilan')
            Logger.error(f"{self.name}: Update Display Error, {e}")

    def exec_reload_database(self):
        global mydb
        try:
            mydb = mysql.connector.connect(host = DB_HOST,user = DB_USER,password = DB_PASSWORD, database = DB_NAME)
        except Exception as e:
            toast_msg = f'Gagal Menginisiasi Database'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}") 

    def exec_reload_table(self):
        print("\n--- FUNGSI exec_reload_table DIPANGGIL ---")
        global mydb, db_antrian, db_merk, db_bahan_bakar, db_warna
        global dt_dash_pendaftaran, dt_dash_belum_uji, dt_dash_sudah_uji

        try:
            cursor = mydb.cursor()
            today = str(time.strftime("%Y-%m-%d", time.localtime()))

            cursor.execute(f"SELECT ID, DESCRIPTION FROM {TB_MERK}")
            db_merk = np.array(cursor.fetchall())
            cursor.execute(f"SELECT ID, DESCRIPTION FROM {TB_BAHAN_BAKAR}")
            db_bahan_bakar = np.array(cursor.fetchall())
            cursor.execute(f"SELECT id_warna, nama FROM {TB_WARNA}")
            db_warna = np.array(cursor.fetchall())

            query_pendaftaran = f"SELECT COUNT(*) FROM {TB_DATA} WHERE DATE(tgl_daftar) = %s"
            cursor.execute(query_pendaftaran, (today,))
            dt_dash_pendaftaran = cursor.fetchone()[0] or 0

            query_sudah_uji = f"""
                SELECT COUNT(*) FROM {TB_DATA}
                WHERE DATE(tgl_daftar) = %s AND (
                    (bahan_bakar = 'B' AND emission_hc_flag IN (0, 1) AND emission_co_flag IN (0, 1))
                    OR
                    (bahan_bakar = 'S' AND emission_smoke_flag IN (0, 1))
                )
            """
            cursor.execute(query_sudah_uji, (today,))
            dt_dash_sudah_uji = cursor.fetchone()[0] or 0
            
            dt_dash_belum_uji = dt_dash_pendaftaran - dt_dash_sudah_uji

            belum_uji_logic = """
                (
                    (bahan_bakar = 'B' AND (emission_hc_flag NOT IN (0, 1) OR emission_co_flag NOT IN (0, 1)))
                    OR
                    (bahan_bakar = 'S' AND (emission_smoke_flag NOT IN (0, 1)))
                )
            """
            query_table = f"""
                SELECT noantrian, nopol, nouji, statusuji, merk, type, idjeniskendaraan, 
                    jbb, berat_kosong, bahan_bakar, warna, th_buat,
                    emission_hc_flag, emission_co_flag, emission_smoke_flag 
                FROM {TB_DATA} 
                WHERE {belum_uji_logic} AND DATE(tgl_daftar) = %s
            """
            cursor.execute(query_table, (today,))
            result_tb_antrian = cursor.fetchall()
            
            db_antrian = np.array(result_tb_antrian).T if result_tb_antrian else np.array([])
            cursor.close()

        except Exception as e:
            toast('Gagal mengambil data antrian harian')
            Logger.error(f"{self.name}: Reload Table Error, {e}")
            return
        
        try:
            layout_list = self.ids.layout_list
            layout_list.clear_widgets()
            if db_antrian.size == 0:
                layout_list.add_widget(MDLabel(text="Semua kendaraan sudah diuji.", halign="center", theme_text_color="Secondary"))
                return

            for i in range(db_antrian.shape[1]):
                hc_db_val = db_antrian[12, i]
                co_db_val = db_antrian[13, i]
                smoke_db_val = db_antrian[14, i]

                hc_stat_val = 2 if hc_db_val is None else int(hc_db_val)
                co_stat_val = 2 if co_db_val is None else int(co_db_val)
                smoke_stat_val = 2 if smoke_db_val is None else int(smoke_db_val)

                hc_stat = 'Lulus' if hc_stat_val == 1 else 'Tidak Lulus' if hc_stat_val == 0 else 'Belum Uji'
                co_stat = 'Lulus' if co_stat_val == 1 else 'Tidak Lulus' if co_stat_val == 0 else 'Belum Uji'
                smoke_stat = 'Lulus' if smoke_stat_val == 1 else 'Tidak Lulus' if smoke_stat_val == 0 else 'Belum Uji'
                
                fuel_id = db_antrian[9, i]
                fuel_name_row = db_bahan_bakar[db_bahan_bakar[:, 0] == fuel_id]
                fuel_text = fuel_name_row[0, 1] if fuel_name_row.size > 0 else 'Tak Dikenal'
                is_diesel = 'SOLAR' in fuel_text.upper()

                merk_id = db_antrian[4, i]
                merk_name_row = db_merk[db_merk[:, 0] == merk_id]
                merk_text = merk_name_row[0, 1] if merk_name_row.size > 0 else '-'

                warna_id = db_antrian[10, i]
                warna_name_row = db_warna[db_warna[:, 0] == warna_id]
                warna_text = warna_name_row[0, 1] if warna_name_row.size > 0 else '-'
                layout_list.add_widget(
                    MDCard(
                        MDLabel(text=f"{db_antrian[0, i]}", halign="center", size_hint_x=0.06),  
                        MDLabel(text=f"{db_antrian[1, i]}", halign="center", size_hint_x=0.08),  
                        MDLabel(text=f"{db_antrian[2, i]}", halign="center", size_hint_x=0.09),  
                        MDLabel(text='Berkala' if db_antrian[3, i] == 'B' else 'Uji Ulang' if (db_antrian[3, i]) == 'U' else 'Baru' if (db_antrian[3, i]) == 'BR' else 'Numpang Uji' if (db_antrian[3, i]) == 'NB' else 'Mutasi', halign="center", size_hint_x= 0.07),
                        MDLabel(text=merk_text, halign="center", size_hint_x=0.08),            
                        MDLabel(text=f"{db_antrian[5, i]}", halign="center", size_hint_x=0.10),  
                        MDLabel(text=f"{db_antrian[6, i]}", halign="center", size_hint_x=0.10),  
                        MDLabel(text=f"{db_antrian[7, i]}", halign="center", size_hint_x=0.05),  
                        MDLabel(text=f"{db_antrian[8, i]}", halign="center", size_hint_x=0.06),  
                        MDLabel(text=fuel_text, halign="center", size_hint_x=0.08),            
                        MDLabel(text=warna_text, halign="center", size_hint_x=0.07),            
                        MDLabel(text=(hc_stat if not is_diesel else '-'), halign="center", size_hint_x=0.05), 
                        MDLabel(text=(co_stat if not is_diesel else '-'), halign="center", size_hint_x=0.05), 
                        MDLabel(text=(smoke_stat if is_diesel else '-'), halign="center", size_hint_x=0.05),
                        ripple_behavior=True,
                        on_press=self.on_antrian_row_press,
                        padding="10dp", id=f"card_antrian{i}",
                        size_hint_y=None, height=dp(40)
                    )
                )
        except Exception as e:
            toast('Gagal memuat ulang tabel antrian')
            Logger.error(f"{self.name}: Gagal render tabel, {e}")
        
        self.exec_reload_database()

    def on_antrian_row_press(self, instance):
        global dt_user, dt_no_antri, dt_no_pol, dt_no_uji, dt_sts_uji, dt_merk, dt_type
        global dt_jns_kend, dt_jbb, dt_brt_ksg, dt_bhn_bkr, dt_warna, dt_nama, dt_thn_buat 

        try:
            if not dt_user:
                toast("Silakan login terlebih dahulu.")
                return

            row = int(str(instance.id).replace("card_antrian", ""))
            dt_no_antri = db_antrian[0, row]
            dt_no_pol = db_antrian[1, row]
            dt_no_uji = db_antrian[2, row]
            dt_sts_uji = db_antrian[3, row]
            dt_merk = db_antrian[4, row]
            dt_type = db_antrian[5, row]
            dt_jns_kend = db_antrian[6, row]
            dt_jbb = db_antrian[7, row]
            dt_brt_ksg = db_antrian[8, row]
            dt_bhn_bkr = db_antrian[9, row]
            dt_warna = db_antrian[10, row]
            dt_thn_buat = db_antrian[11, row]
            emission_hc_flag = db_antrian[12, row]
            emission_co_flag = db_antrian[13, row]
            emission_smoke_flag = db_antrian[14, row]
            
            fuel_name_row = db_bahan_bakar[db_bahan_bakar[:, 0] == dt_bhn_bkr]
            fuel_text = fuel_name_row[0, 1] if fuel_name_row.size > 0 else 'Tak Dikenal'

            if 'SOLAR' in fuel_text.upper():
                if emission_smoke_flag == 1 or emission_smoke_flag == 0:
                    toast(f"Kendaraan {dt_no_pol} sudah selesai diuji emisi.")
                    return 
                else:
                    self.screen_manager.current = 'screen_diesel_emission'
            elif 'BENSIN' in fuel_text.upper():
                if (emission_hc_flag == 1 or emission_hc_flag == 0) and (emission_co_flag == 1 or emission_co_flag == 0):
                    toast(f"Kendaraan {dt_no_pol} sudah selesai diuji emisi.")
                    return 
                else:
                    self.screen_manager.current = 'screen_gass_emission'
            else:
                toast("Jenis bahan bakar tidak sesuai untuk pengujian emisi.")
                return

        except Exception as e:
            toast('Gagal memproses data antrian')
            Logger.error(f"{self.name}: Row Press Error, {e}")

    def exec_logout(self):
        global dt_user
        dt_user = ""
        self.screen_manager.current = 'screen_login'

    def exec_navigate_home(self):
        try:
            self.screen_manager.current = 'screen_home'
        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Beranda'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")   

    def exec_navigate_login(self):
        global dt_user
        try:
            if (dt_user == ""):
                self.screen_manager.current = 'screen_login'
            else:
                toast_msg = f"Anda sudah login sebagai {dt_user}"
                toast(toast_msg)
                Logger.info(f"{self.name}: {toast_msg}")
        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Login'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")      

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Terjadi kesalahan saat berpindah ke halaman Utama'
            toast(toast_msg)
            Logger.error(f"{self.name}: {toast_msg}, {e}")    


class ScreenGassEmission(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenGassEmission, self).__init__(**kwargs)
        self.ser = None 
        self.measurement_event = None 
        self.latest_hc = 0 
        self.latest_co = 0.0 
        self.port_check_event = None
        self.toast_shown = False
        Clock.schedule_once(self.delayed_init, 1)

    def delayed_init(self, dt):   
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE              
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        try:
            self.ids.lb_no_antrian.text = str(dt_no_antri)
            self.ids.lb_no_pol.text = str(dt_no_pol)
            self.ids.lb_no_uji.text = str(dt_no_uji)
            self.ids.lb_no_jbb.text = str(dt_jbb)
            self.ids.lb_no_brtkosong.text = str(dt_brt_ksg)
            self.ids.lb_no_tahunbuat.text = str(dt_thn_buat)
            fuel_name_row = db_bahan_bakar[db_bahan_bakar[:, 0] == dt_bhn_bkr]
            self.ids.lb_no_bahanbakar.text = fuel_name_row[0, 1] if fuel_name_row.size > 0 else 'Tak Dikenal'
        except Exception as e:
            Logger.error(f"{self.name}: Gagal mengisi label identitas - {e}")  
            
        if not self.port_check_event:
            self.port_check_event = Clock.schedule_interval(self.check_device_presence, 5)
        self.check_device_presence(0)

        self.ids.lb_test_result.text = ""
        self.ids.lb_test_result.md_bg_color = (0,0,0,0)
        self.ids.lb_emission_hc.text = "....."
        self.ids.lb_emission_co.text = "....."
        self.ids.lb_test_subtitle.text = "Tekan MULAI untuk memulai"
        self.ids.bt_mulai.disabled = False
        self.ids.bt_save.disabled = True

    def on_leave(self):
        if self.port_check_event:
            self.port_check_event.cancel()
            self.port_check_event = None
        
        if self.ser and self.ser.is_open:
            self.ser.close()

    def check_device_presence(self, dt):
        available_ports = [port.device for port in list_ports.comports()]
        
        if COM_PORT in available_ports:
            self.update_connection_status(True)
            self.toast_shown = False 
        else:
            self.update_connection_status(False)
            if not self.toast_shown:
                toast(f"Port {COM_PORT} tidak terhubung ke PC.")
                self.toast_shown = True

    def update_connection_status(self, is_connected):
        if is_connected:
            self.ids.lb_comm.text = "Com: Terhubung"
            self.ids.lb_comm.text_color = self.theme_cls.colors["Green"]["200"]
        else:
            self.ids.lb_comm.text = "Com: Tidak Terhubung"
            self.ids.lb_comm.text_color = self.theme_cls.colors["Red"]["A200"]
    
    def exec_start_test(self):
        if "Tidak Terhubung" in self.ids.lb_comm.text:
            toast(f"Tidak bisa memulai, alat di {COM_PORT} tidak terhubung.")
            return
        
        try:
            self.ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=TIMEOUT)
            toast(f"Berhasil terhubung ke alat di {COM_PORT}")
        except serial.SerialException as e:
            toast(f"Gagal terhubung ke alat di {COM_PORT}")
            self.update_connection_status(False)
            Logger.error(f"Serial Connection Error: {e}")
            return

        self.ser.write(CMD_START_MEASURE)
        time.sleep(1)

        self.ids.bt_mulai.disabled = True
        self.ids.lb_test_subtitle.text = "Pengukuran berlangsung..."
        self.ids.bt_save.disabled = False
        self.measurement_event = Clock.schedule_interval(self.read_serial_data, 0.5)
        duration = COUNT_STARTING_GASS
        Clock.schedule_once(self.finish_test, duration)

    def read_serial_data(self, dt):
            if not self.ser or not self.ser.is_open:
                return
            
            try:
                self.ser.write(CMD_GET_DATA)
                response_bytes = self.ser.readline()
                
                if response_bytes:
                    response_str = response_bytes.decode('ascii', errors='ignore').strip()
                    
                    parsed_data = self.parse_data_string_baru(response_str)
                    
                    if parsed_data:
                        self.latest_hc = parsed_data.get('HC', self.latest_hc)
                        self.latest_co = parsed_data.get('CO', self.latest_co)

                        self.ids.lb_emission_hc.text = str(self.latest_hc)
                        self.ids.lb_emission_co.text = f"{self.latest_co:.2f}"
                    
                    elif response_str:
                        Logger.info(f"Respons lain diterima: {response_str}")

            except serial.SerialException as e:
                toast("Koneksi serial terputus!")
                Logger.error(f"Serial Read Error: {e}")
                self.finish_test(0) 

    # SIMULASI DUMMY    
    # def exec_start_test(self):
    #     toast("Memulai mode simulasi...")

    #     self.ids.bt_mulai.disabled = True
    #     self.ids.lb_test_subtitle.text = "Simulasi pengukuran berlangsung..."
    #     self.ids.lb_comm.text = "Status: SIMULASI AKTIF" # Menandakan mode simulasi
    #     self.ids.lb_comm.text_color = self.theme_cls.colors["Green"]["200"] # Warna hijau untuk simulasi
    #     self.measurement_event = Clock.schedule_interval(self.read_serial_data, 0.5)
    #     duration = COUNT_STARTING_GASS
    #     Clock.schedule_once(self.finish_test, duration)

    # def read_serial_data(self, dt):
    #     try:
    #         fake_co_val = random.randint(10, 50) 
    #         fake_hc_val = random.randint(50, 60)
    #         fake_data_string = f"{fake_co_val:03d}  {fake_hc_val}  {random.randint(100,999)}A 00"

    #         parsed_data = self.parse_data_string_baru(fake_data_string)
    #         if parsed_data:
    #             self.latest_hc = parsed_data.get('HC', self.latest_hc)
    #             self.latest_co = parsed_data.get('CO', self.latest_co)
                
    #             self.ids.lb_emission_hc.text = str(self.latest_hc)
    #             self.ids.lb_emission_co.text = f"{self.latest_co:.2f}"

    #     except Exception as e:
    #         Logger.error(f"Error di simulasi read_serial_data: {e}")

    def parse_data_string_baru(self, data_string: str):
            try:
                parts = data_string.split()
                if not parts:
                    return None

                start_index = -1
                for i, part in enumerate(parts):
                    if part.isdigit():
                        start_index = i
                        break
                
                if start_index == -1 or len(parts) < start_index + 2:
                    return None
                    
                co_value = float(parts[start_index]) / 100.0
                hc_value = int(parts[start_index + 1])

                return {
                    'HC': hc_value,
                    'CO': co_value,
                }

            except (ValueError, IndexError) as e:
                Logger.error(f"Gagal parsing data: '{data_string}', error: {e}")
                return None

    def finish_test(self, dt):
        if self.measurement_event:
            Clock.unschedule(self.measurement_event)
            self.measurement_event = None
        
        if self.ser and self.ser.is_open:
            self.ser.write(CMD_STOP_MEASURE)
            time.sleep(1)
            self.ser.close()
        
        toast("Pengukuran Selesai...")
        self.ids.lb_test_subtitle.text = "Siap untuk uji ulang atau simpan."
        self.ids.bt_mulai.disabled = False
        self.evaluate_results()

    def evaluate_results(self):
        global emission_hc_flag, emission_co_flag
        try:
            hc_val = self.latest_hc
            co_val = self.latest_co
            tahun = int(dt_thn_buat)

            max_co, max_hc = 0, 0
            if tahun < 2007:
                max_co, max_hc = 4.0, 1000
            elif 2007 <= tahun <= 2018:
                max_co, max_hc = 1.0, 150
            else:  # tahun > 2018
                max_co, max_hc = 0.5, 100
            
            emission_hc_flag = 1 if hc_val <= max_hc else 0
            emission_co_flag = 1 if co_val <= max_co else 0
            
            if emission_hc_flag == 1 and emission_co_flag == 1:
                self.ids.lb_test_result.text = "LULUS"
                self.ids.lb_test_result.md_bg_color = "green"
            else:
                self.ids.lb_test_result.text = "TIDAK LULUS"
                self.ids.lb_test_result.md_bg_color = "red"

        except Exception as e:
            toast("Gagal mengevaluasi hasil, periksa tahun pembuatan kendaraan.")
            Logger.error(f"{self.name}: Gagal evaluasi hasil - {e}")

    def exec_save(self):
        global emission_hc_flag, emission_co_flag, dt_id_user 
        
        try:
            self.evaluate_results()
            
            current_save_time = time.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor = mydb.cursor()
            
            sql = f"""UPDATE {TB_DATA} SET 
                          emission_hc_value = %s, 
                          emission_hc_flag = %s, 
                          emission_co_value = %s, 
                          emission_co_flag = %s,
                          emission_user = %s,
                          emission_post = %s
                      WHERE noantrian = %s"""
            
            val = (self.latest_hc, emission_hc_flag, self.latest_co, emission_co_flag, dt_id_user, current_save_time, dt_no_antri)
            
            cursor.execute(sql, val)
            mydb.commit()
            
            toast(f"Data berhasil disimpan!")
            self.ids.lb_test_subtitle.text = f"Data disimpan: HC={self.latest_hc}, CO={self.latest_co}, Waktu={current_save_time}"

        except Exception as e:
            toast("Gagal menyimpan data ke database.")
            Logger.error(f"{self.name}: Save Gas Error, {e}")

    def exec_print(self):
        toast("Fungsi Print Belum Diimplementasikan")

    def exec_navigate_main(self):
        if hasattr(self, 'measurement_event') and self.measurement_event:
            Clock.unschedule(self.measurement_event)
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.screen_manager.current = 'screen_main'

class ScreenDieselEmission(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenDieselEmission, self).__init__(**kwargs)
        self.ser = None 
        self.measurement_event = None
        self.latest_smoke = 0.0
        self.port_check_event = None
        self.toast_shown = False
        Clock.schedule_once(self.delayed_init, 1)

    def delayed_init(self, dt):
        self.ids.lb_title.text = APP_TITLE
        self.ids.lb_subtitle.text = APP_SUBTITLE              
        self.ids.img_pemkab.source = f'assets/images/{IMG_LOGO_PEMKAB}'
        self.ids.img_dishub.source = f'assets/images/{IMG_LOGO_DISHUB}'
        self.ids.lb_pemkab.text = LB_PEMKAB
        self.ids.lb_dishub.text = LB_DISHUB
        self.ids.lb_unit.text = LB_UNIT
        self.ids.lb_unit_address.text = LB_UNIT_ADDRESS

    def on_enter(self):
        try:
            self.ids.lb_no_antrian.text = str(dt_no_antri)
            self.ids.lb_no_pol.text = str(dt_no_pol)
            self.ids.lb_no_uji.text = str(dt_no_uji)
            self.ids.lb_no_jbb.text = str(dt_jbb)
            self.ids.lb_no_brtkosong.text = str(dt_brt_ksg)
            self.ids.lb_no_tahunbuat.text = str(dt_thn_buat)
            fuel_name_row = db_bahan_bakar[db_bahan_bakar[:, 0] == dt_bhn_bkr]
            self.ids.lb_no_bahanbakar.text = fuel_name_row[0, 1] if fuel_name_row.size > 0 else 'Tak Dikenal'
        except Exception as e:
            Logger.error(f"{self.name}: Gagal mengisi label identitas - {e}")  
            
        if not self.port_check_event:
            self.port_check_event = Clock.schedule_interval(self.check_device_presence, 2)
        self.check_device_presence(0)

        self.ids.lb_test_result.text = ""
        self.ids.lb_test_result.md_bg_color = (0,0,0,0)
        self.ids.lb_emission_smoke.text = "0.00"
        self.ids.lb_test_subtitle.text = "Tekan MULAI untuk memulai"
        self.ids.bt_mulai.disabled = False
        self.ids.bt_save.disabled = True

    def on_leave(self):
        if self.port_check_event:
            self.port_check_event.cancel()
            self.port_check_event = None

        if self.ser and self.ser.is_open:
            self.ser.close()

    def check_device_presence(self, dt):
        available_ports = [port.device for port in list_ports.comports()]
        if COM_PORT in available_ports:
            self.update_connection_status(True)
            self.toast_shown = False 
        else:
            self.update_connection_status(False)
            if not self.toast_shown:
                toast(f"Port {COM_PORT} tidak terhubung ke PC.")
                self.toast_shown = True

    def update_connection_status(self, is_connected):
        if is_connected:
            self.ids.lb_comm.text = "Status: Connected"
            self.ids.lb_comm.text_color = self.theme_cls.colors["Green"]["200"]
        else:
            self.ids.lb_comm.text = "Status: Disconnected"
            self.ids.lb_comm.text_color = self.theme_cls.colors["Red"]["A200"]
    
    def exec_start_test(self):
        toast("Memulai mode simulasi (Diesel)...")
        self.ids.bt_mulai.disabled = True
        self.ids.lb_test_subtitle.text = "Simulasi pengukuran berlangsung..."
        self.ids.bt_save.disabled = False
        self.measurement_event = Clock.schedule_interval(self.read_dummy_data, 0.5)
        duration = COUNT_STARTING_DIESEL
        Clock.schedule_once(self.finish_test, duration)

    def read_dummy_data(self, dt):
        self.latest_smoke = round(random.uniform(10, 80), 2)
        self.ids.lb_emission_smoke.text = f"{self.latest_smoke:.2f}"

    def finish_test(self, dt):
        if self.measurement_event:
            Clock.unschedule(self.measurement_event)
            self.measurement_event = None
        
        toast("Pengukuran Otomatis Selesai.")
        self.ids.lb_test_subtitle.text = "Siap untuk uji ulang atau simpan."
        self.ids.bt_mulai.disabled = False
        self.evaluate_results()

    def evaluate_results(self):
        """Evaluasi Lulus/Tidak Lulus khusus untuk asap diesel."""
        global emission_smoke_flag
        try:
            smoke_val = self.latest_smoke
            tahun = int(dt_thn_buat)
            jbb = int(dt_jbb)

            max_smoke = 0
            if jbb <= 3500:
                if tahun < 2010: max_smoke = 70 
                else: max_smoke = 40 
            else: 
                if tahun < 2010: max_smoke = 70
                else: max_smoke = 50

            emission_smoke_flag = 1 if smoke_val <= max_smoke else 0
            
            if emission_smoke_flag == 1:
                self.ids.lb_test_result.text = "LULUS"
                self.ids.lb_test_result.md_bg_color = "green"
            else:
                self.ids.lb_test_result.text = "TIDAK LULUS"
                self.ids.lb_test_result.md_bg_color = "red"
        except Exception as e:
            toast("Gagal evaluasi, periksa Tahun dan JBB.")
            Logger.error(f"{self.name}: Gagal evaluasi diesel - {e}")

    def exec_save(self):
        global emission_smoke_flag, dt_id_user
        
        try:
            self.evaluate_results()
            
            current_save_time = time.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor = mydb.cursor()
            
            sql = f"""UPDATE {TB_DATA} SET 
                        emission_smoke_value = %s, 
                        emission_smoke_flag = %s,
                        emission_user = %s,
                        emission_post = %s
                      WHERE noantrian = %s"""
            
            val = (self.latest_smoke, emission_smoke_flag, dt_id_user, current_save_time, dt_no_antri)
            
            cursor.execute(sql, val)
            mydb.commit()
            
            toast("Hasil Uji Diesel Berhasil Disimpan.")
            self.ids.lb_test_subtitle.text = f"Data disimpan: Asap={self.latest_smoke}%, Waktu={current_save_time}"

        except Exception as e:
            toast("Gagal menyimpan data ke database.")
            Logger.error(f"{self.name}: Save Diesel Error, {e}")

    def exec_navigate_main(self):
        if hasattr(self, 'measurement_event') and self.measurement_event:
            Clock.unschedule(self.measurement_event)
        self.screen_manager.current = 'screen_main'

class RootScreen(ScreenManager):
    pass

class EmissionmeterApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_resize=self.on_window_resize)

    def build(self):
        global window_size_x, window_size_y
        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.accent_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.icon = 'assets/images/logo-load-app.png'
        window_size_y = Window.size[0]
        window_size_x = Window.size[1]
        self.set_dynamic_fonts(Window.size)

        LabelBase.register(
            name="Orbitron-Regular",
            fn_regular="assets/fonts/Orbitron-Regular.ttf")
        
        LabelBase.register(
            name="Draco",
            fn_regular="assets/fonts/Draco.otf")        

        LabelBase.register(
            name="Recharge",
            fn_regular="assets/fonts/Recharge.otf") 
        
        theme_font_styles.append('H1')
        self.theme_cls.font_styles["H1"] = [
            "Orbitron-Regular", 64, False, 0.15]       

        theme_font_styles.append('H2')
        self.theme_cls.font_styles["H2"] = [
            "Orbitron-Regular", 32, False, 0.15] 
        
        theme_font_styles.append('H4')
        self.theme_cls.font_styles["H4"] = [
            "Recharge", 30, False, 0.15] 

        theme_font_styles.append('H5')
        self.theme_cls.font_styles["H5"] = [
            "Recharge", 20, False, 0.15] 

        theme_font_styles.append('H6')
        self.theme_cls.font_styles["H6"] = [
            "Recharge", 16, False, 0.15] 

        theme_font_styles.append('Subtitle1')
        self.theme_cls.font_styles["Subtitle1"] = [
            "Recharge", 11, False, 0.15] 

        theme_font_styles.append('Body1')
        self.theme_cls.font_styles["Body1"] = [
            "Recharge", 10, False, 0.15] 
        
        theme_font_styles.append('Button')
        self.theme_cls.font_styles["Button"] = [
            "Recharge", 9, False, 0.15] 

        theme_font_styles.append('Caption')
        self.theme_cls.font_styles["Caption"] = [
            "Recharge", 8, False, 0.15]       
        
        Window.fullscreen = 'auto'
        Builder.load_file('main.kv')
        return RootScreen()

    def on_window_resize(self, window, width, height):
        Logger.info(f"Window size: {width}x{height}")
        self.set_dynamic_fonts((width, height))
        self.refresh_all_fonts()

    def refresh_all_fonts(self):
        if hasattr(self, 'root') and hasattr(self.root, 'screens'):
            for screen in self.root.screens:
                self.refresh_fonts(screen)

    def refresh_fonts(self, widget):
        from kivymd.uix.label import MDLabel
        if isinstance(widget, MDLabel):
            original_style = widget.font_style
            temp_style = "Body1" if original_style != "Body1" else "H6"
            widget.font_style = temp_style
            widget.font_style = original_style
        if hasattr(widget, 'children'):
            for child in widget.children:
                self.refresh_fonts(child)

    def set_dynamic_fonts(self, size):
        try:
            screen_size_x = Window.system_size[0]
            screen_size_y = Window.system_size[1]
        except AttributeError:
            screen_size_x = Window._get_system_size()[0]
            screen_size_y = Window._get_system_size()[1]
        font_size_l = np.array([64, 32, 30, 20, 16, 11, 10, 9, 8])
        scale = min(screen_size_x / 1920, screen_size_y / 1080)
        font_size = np.round(font_size_l * scale, 0)
        Logger.info(f"Font resized: {font_size_l} to {font_size}")
        self.theme_cls.font_styles["H1"] = [
            "Orbitron-Regular", font_size[0], False, 0.15]
        self.theme_cls.font_styles["H2"] = [
            "Orbitron-Regular", font_size[1], False, 0.15]
        self.theme_cls.font_styles["H4"] = [
            "Recharge", font_size[2], False, 0.15]
        self.theme_cls.font_styles["H5"] = [
            "Recharge", font_size[3], False, 0.15]
        self.theme_cls.font_styles["H6"] = [
            "Recharge", font_size[4], False, 0.15]
        self.theme_cls.font_styles["Subtitle1"] = [
            "Recharge", font_size[5], False, 0.15]
        self.theme_cls.font_styles["Body1"] = [
            "Recharge", font_size[6], False, 0.15]
        self.theme_cls.font_styles["Button"] = [
            "Recharge", font_size[7], False, 0.15]
        self.theme_cls.font_styles["Caption"] = [
            "Recharge", font_size[8], False, 0.15]       

        if hasattr(self, 'root'):
            self.refresh_fonts(self.root)

if __name__ == '__main__':
    EmissionmeterApp().run()