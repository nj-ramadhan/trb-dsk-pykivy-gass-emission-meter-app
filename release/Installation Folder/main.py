from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemanddock')
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivymd.uix.datatables import MDDataTable
from kivy.uix.screenmanager import ScreenManager
from kivymd.font_definitions import theme_font_styles
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.toast import toast
from kivy.metrics import dp
from kivymd.app import MDApp
import os, sys, time, numpy as np
import configparser, hashlib, mysql.connector
import pyaudio, audioop
from math import log10
import serial.tools.list_ports as ports, serial

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
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    running_mode = 'Frozen/executable'
else:
    try:
        app_full_path = os.path.realpath(__file__)
        application_path = os.path.dirname(app_full_path)
        running_mode = "Non-interactive (e.g. 'python myapp.py')"
    except NameError:
        application_path = os.getcwd()
        running_mode = 'Interactive'

config_full_path = os.path.join(application_path, config_name)
config = configparser.ConfigParser()
config.read(config_full_path)

# SQL setting
DB_HOST = config['mysql']['DB_HOST']
DB_USER = config['mysql']['DB_USER']
DB_PASSWORD = config['mysql']['DB_PASSWORD']
DB_NAME = config['mysql']['DB_NAME']
TB_DATA = config['mysql']['TB_DATA']
TB_USER = config['mysql']['TB_USER']
TB_MERK = config['mysql']['TB_MERK']

# system setting
TIME_OUT = int(config['setting']['TIME_OUT'])
COUNT_STARTING = int(config['setting']['COUNT_STARTING'])
COUNT_ACQUISITION = int(config['setting']['COUNT_ACQUISITION'])
UPDATE_CAROUSEL_INTERVAL = float(config['setting']['UPDATE_CAROUSEL_INTERVAL'])
UPDATE_CONNECTION_INTERVAL = float(config['setting']['UPDATE_CONNECTION_INTERVAL'])
GET_DATA_INTERVAL = float(config['setting']['GET_DATA_INTERVAL'])

COM_PORT_EMISSION = config['setting']['COM_PORT_EMISSION']

# system standard
STANDARD_MAX_GAS_CO = float(config['standard']['STANDARD_MAX_GAS_CO']) # in %
STANDARD_MAX_GAS_HC = float(config['standard']['STANDARD_MAX_GAS_HC']) # in ppm
STANDARD_MAX_DIESEL_SMOKE = float(config['standard']['STANDARD_MAX_DIESEL_SMOKE']) # in ppm

dt_emission_co_value = 0
dt_emission_hc_value = 0
dt_emission_smoke_value = 0
dt_emission_type = 0
dt_emission_flag = 0
dt_emission_user = 1
dt_emission_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
dt_user = ""
dt_no_antrian = ""
dt_no_pol = ""
dt_no_uji = ""
dt_nama = ""
dt_jenis_kendaraan = ""

dt_dash_pendaftaran = 0
dt_dash_belum_uji = 0
dt_dash_sudah_uji = 0

class ScreenHome(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenHome, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)

    def delayed_init(self, dt):
        Clock.schedule_interval(self.regular_update_carousel, UPDATE_CAROUSEL_INTERVAL)

    def regular_update_carousel(self, dt):
        try:
            self.ids.carousel.index += 1
            
        except Exception as e:
            toast_msg = f'Error Update Display: {e}'
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
            toast_msg = f'Error Navigate to Login Screen: {e}'
            toast(toast_msg)     

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Error Navigate to Main Screen: {e}'
            toast(toast_msg)    

class ScreenLogin(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenLogin, self).__init__(**kwargs)

    def exec_cancel(self):
        try:
            self.ids.tx_username.text = ""
            self.ids.tx_password.text = ""    

        except Exception as e:
            toast_msg = f'error Login: {e}'

    def exec_login(self):
        global mydb, db_users
        global dt_emission_user, dt_user

        try:
            input_username = self.ids.tx_username.text
            input_password = self.ids.tx_password.text        
            # Adding salt at the last of the password
            dataBase_password = input_password
            # Encoding the password
            hashed_password = hashlib.md5(dataBase_password.encode())

            mycursor = mydb.cursor()
            mycursor.execute(f"SELECT id_user, nama, username, password, nama FROM {TB_USER} WHERE username = '{input_username}' and password = '{hashed_password.hexdigest()}'")
            myresult = mycursor.fetchone()
            db_users = np.array(myresult).T
            #if invalid
            if myresult == 0:
                toast('Gagal Masuk, Nama Pengguna atau Password Salah')
            #else, if valid
            else:
                toast_msg = f'Berhasil Masuk, Selamat Datang {myresult[1]}'
                toast(toast_msg)
                dt_check_user = myresult[0]
                dt_user = myresult[1]
                self.ids.tx_username.text = ""
                self.ids.tx_password.text = "" 
                self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'error Login: {e}'
            toast(toast_msg)        
            toast('Gagal Masuk, Nama Pengguna atau Password Salah')

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
            toast_msg = f'Error Navigate to Login Screen: {e}'
            toast(toast_msg)     

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Error Navigate to Main Screen: {e}'
            toast(toast_msg)   

class ScreenMain(MDScreen):   
    def __init__(self, **kwargs):
        super(ScreenMain, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 1)                 

    def delayed_init(self, dt):
        global flag_conn_stat, flag_play
        global count_starting, count_get_data

        flag_conn_stat = False
        flag_play = False

        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        
        Clock.schedule_interval(self.regular_update_display, 1)
        Clock.schedule_interval(self.regular_update_connection, UPDATE_CONNECTION_INTERVAL)
        self.exec_reload_database()
        self.exec_reload_table()

    def on_antrian_row_press(self, instance):
        global dt_no_antrian, dt_no_pol, dt_no_uji, dt_nama, dt_emission_flag
        global dt_merk, dt_type, dt_jenis_kendaraan, dt_jbb, dt_bahan_bakar, dt_warna, dt_emission_type
        global db_antrian, db_merk

        try:
            row = int(str(instance.id).replace("card_antrian",""))
            dt_no_antrian           = f"{db_antrian[0, row]}"
            dt_no_pol               = f"{db_antrian[1, row]}"
            dt_no_uji               = f"{db_antrian[2, row]}"
            dt_emission_flag        = 'Lulus' if (int(db_antrian[3, row]) == 2) else 'Tidak Lulus' if (int(db_antrian[3, row]) == 1) else 'Belum Tes'
            dt_nama                 = f"{db_antrian[4, row]}"
            dt_merk                 = f"{db_merk[np.where(db_merk == db_antrian[5, row])[0][0],1]}"
            dt_type                 = f"{db_antrian[6, row]}"
            dt_jenis_kendaraan      = f"{db_antrian[7, row]}"
            dt_jbb                  = f"{db_antrian[8, row]}"
            dt_bahan_bakar          = f"{db_antrian[9, row]}"
            dt_warna                = f"{db_antrian[10, row]}"

            dt_emission_type = 1 if dt_bahan_bakar == "Diesel" else 0
                        
            self.exec_start()

        except Exception as e:
            toast_msg = f'Error Execute Command from Table Row: {e}'
            toast(toast_msg)   


    def regular_update_display(self, dt):
        global flag_conn_stat
        global count_starting, count_get_data
        global dt_user, dt_no_antrian, dt_no_pol, dt_no_uji, dt_nama, dt_jenis_kendaraan
        global dt_emission_flag, dt_emission_co_value, dt_emission_hc_value, dt_emission_smoke_value, dt_emission_user, dt_emission_post
        
        try:
            screen_home = self.screen_manager.get_screen('screen_home')
            screen_login = self.screen_manager.get_screen('screen_login')
            screen_gass_emission = self.screen_manager.get_screen('screen_gass_emission')
            screen_diesel_emission = self.screen_manager.get_screen('screen_diesel_emission')

            self.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            self.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_home.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_home.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_login.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_login.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_gass_emission.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_gass_emission.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))
            screen_diesel_emission.ids.lb_time.text = str(time.strftime("%H:%M:%S", time.localtime()))
            screen_diesel_emission.ids.lb_date.text = str(time.strftime("%d/%m/%Y", time.localtime()))

            self.ids.lb_dash_pendaftaran.text = str(dt_dash_pendaftaran)
            self.ids.lb_dash_belum_uji.text = str(dt_dash_belum_uji)
            self.ids.lb_dash_sudah_uji.text = str(dt_dash_sudah_uji)

            screen_gass_emission.ids.lb_no_antrian.text = str(dt_no_antrian)
            screen_gass_emission.ids.lb_no_pol.text = str(dt_no_pol)
            screen_gass_emission.ids.lb_no_uji.text = str(dt_no_uji)
            screen_gass_emission.ids.lb_nama.text = str(dt_nama)
            screen_gass_emission.ids.lb_jenis_kendaraan.text = str(dt_jenis_kendaraan)

            screen_diesel_emission.ids.lb_no_antrian.text = str(dt_no_antrian)
            screen_diesel_emission.ids.lb_no_pol.text = str(dt_no_pol)
            screen_diesel_emission.ids.lb_no_uji.text = str(dt_no_uji)
            screen_diesel_emission.ids.lb_nama.text = str(dt_nama)
            screen_diesel_emission.ids.lb_jenis_kendaraan.text = str(dt_jenis_kendaraan)

            if(not flag_play):
                screen_gass_emission.ids.bt_save.md_bg_color = colors['Green']['200']
                screen_gass_emission.ids.bt_save.disabled = False
                screen_gass_emission.ids.bt_reload.md_bg_color = colors['Red']['A200']
                screen_gass_emission.ids.bt_reload.disabled = False
                screen_diesel_emission.ids.bt_save.md_bg_color = colors['Green']['200']
                screen_diesel_emission.ids.bt_save.disabled = False
                screen_diesel_emission.ids.bt_reload.md_bg_color = colors['Red']['A200']
                screen_diesel_emission.ids.bt_reload.disabled = False
            else:
                screen_gass_emission.ids.bt_reload.disabled = True
                screen_gass_emission.ids.bt_save.disabled = True
                screen_diesel_emission.ids.bt_reload.disabled = True
                screen_diesel_emission.ids.bt_save.disabled = True

            if(not flag_conn_stat):
                self.ids.lb_comm.color = colors['Red']['A200']
                self.ids.lb_comm.text = 'Alat Tidak Terhubung'
                screen_home.ids.lb_comm.color = colors['Red']['A200']
                screen_home.ids.lb_comm.text = 'Alat Tidak Terhubung'
                screen_login.ids.lb_comm.color = colors['Red']['A200']
                screen_login.ids.lb_comm.text = 'Alat Tidak Terhubung'
                screen_gass_emission.ids.lb_comm.color = colors['Red']['A200']
                screen_gass_emission.ids.lb_comm.text = 'Alat Tidak Terhubung'                
                screen_diesel_emission.ids.lb_comm.color = colors['Red']['A200']
                screen_diesel_emission.ids.lb_comm.text = 'Alat Tidak Terhubung'
            else:
                self.ids.lb_comm.color = colors['Blue']['200']
                self.ids.lb_comm.text = 'Alat Terhubung'
                screen_home.ids.lb_comm.color = colors['Blue']['200']
                screen_home.ids.lb_comm.text = 'Alat Terhubung'
                screen_login.ids.lb_comm.color = colors['Blue']['200']
                screen_login.ids.lb_comm.text = 'Alat Terhubung'
                screen_gass_emission.ids.lb_comm.color = colors['Blue']['200']
                screen_gass_emission.ids.lb_comm.text = 'Alat Terhubung'
                screen_diesel_emission.ids.lb_comm.color = colors['Blue']['200']
                screen_diesel_emission.ids.lb_comm.text = 'Alat Terhubung'

            if(count_starting <= 0):
                screen_gass_emission.ids.lb_test_subtitle.text = "HASIL PENGUKURAN"
                screen_gass_emission.ids.lb_emission_co.text = str(np.round(dt_emission_co_value, 2))
                screen_gass_emission.ids.lb_emission_hc.text = str(np.round(dt_emission_hc_value, 2))
                screen_diesel_emission.ids.lb_test_subtitle.text = "HASIL PENGUKURAN"
                screen_diesel_emission.ids.lb_emission_smoke.text = str(np.round(dt_emission_smoke_value, 2))

                if((dt_emission_co_value <= STANDARD_MAX_GAS_CO) and (dt_emission_hc_value <= STANDARD_MAX_GAS_HC)):
                    screen_gass_emission.ids.lb_info.text = f"Ambang Batas Emisi CO {STANDARD_MAX_GAS_CO} %, HC {STANDARD_MAX_GAS_HC} ppm.\nEmisi Gas Buang Kendaraan Dalam Range Ambang Batas"
                else:
                    screen_gass_emission.ids.lb_info.text = f"Ambang Batas Emisi CO {STANDARD_MAX_GAS_CO} %, HC {STANDARD_MAX_GAS_HC} ppm.\nEmisi Gas Buang Kendaraan Diluar Ambang Batas"
                if(dt_emission_smoke_value <= STANDARD_MAX_DIESEL_SMOKE):
                    screen_diesel_emission.ids.lb_info.text = f"Ambang Batas Emisi Asap {STANDARD_MAX_DIESEL_SMOKE} ppm.\nEmisi Gas Buang Kendaraan Dalam Range Ambang Batas"
                else:
                    screen_diesel_emission.ids.lb_info.text = f"Ambang Batas Emisi Asap {STANDARD_MAX_DIESEL_SMOKE} ppm.\nEmisi Gas Buang Kendaraan Diluar Ambang Batas"
                                                                
            elif(count_starting > 0):
                if(flag_play):
                    screen_gass_emission.ids.lb_test_subtitle.text = "MEMULAI PENGUKURAN"
                    screen_gass_emission.ids.lb_emission_co.text = str(count_starting)
                    screen_gass_emission.ids.lb_info.text = "Silahkan Nyalakan Mesin Kendaraan dan Masukan Alat Ukur ke Knalpot"                    
                    screen_diesel_emission.ids.lb_test_subtitle.text = "MEMULAI PENGUKURAN"
                    screen_diesel_emission.ids.lb_emission_smoke.text = str(count_starting)
                    screen_diesel_emission.ids.lb_info.text = "Silahkan Nyalakan Mesin Kendaraan dan Masukan Alat Ukur ke Knalpot"

            if(count_get_data <= 0):
                if(not flag_play):
                    if(dt_emission_type == 0):
                        if((dt_emission_co_value <= STANDARD_MAX_GAS_CO) and (dt_emission_hc_value <= STANDARD_MAX_GAS_HC)):
                            screen_gass_emission.ids.lb_test_result.md_bg_color = colors['Green']['200']
                            screen_gass_emission.ids.lb_test_result.text = "LULUS"
                            dt_emission_flag = "Lulus"
                            screen_gass_emission.ids.lb_test_result.text_color = colors['Green']['700']
                        else:
                            screen_gass_emission.ids.lb_test_result.md_bg_color = colors['Red']['A200']
                            screen_gass_emission.ids.lb_test_result.text = "TIDAK LULUS"
                            dt_emission_flag = "Tidak Lulus"
                            screen_gass_emission.ids.lb_test_result.text_color = colors['Red']['A700']
                    else:
                        if(dt_emission_smoke_value <= STANDARD_MAX_DIESEL_SMOKE):
                            screen_diesel_emission.ids.lb_test_result.md_bg_color = colors['Green']['200']
                            screen_diesel_emission.ids.lb_test_result.text = "LULUS"
                            dt_emission_flag = "Lulus"
                            screen_diesel_emission.ids.lb_test_result.text_color = colors['Green']['700']
                        else:
                            screen_diesel_emission.ids.lb_test_result.md_bg_color = colors['Red']['A200']
                            screen_diesel_emission.ids.lb_test_result.text = "TIDAK LULUS"
                            dt_emission_flag = "Tidak Lulus"
                            screen_diesel_emission.ids.lb_test_result.text_color = colors['Red']['A700']

            elif(count_get_data > 0):
                    screen_gass_emission.ids.lb_test_result.md_bg_color = colors['Gray']['500']
                    screen_gass_emission.ids.lb_test_result.text = ""
                    screen_diesel_emission.ids.lb_test_result.md_bg_color = colors['Gray']['500']
                    screen_diesel_emission.ids.lb_test_result.text = ""
            
            self.ids.bt_logout.disabled = False if dt_user != '' else True

            self.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_home.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_login.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_gass_emission.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'
            screen_diesel_emission.ids.lb_operator.text = f'Login Sebagai: {dt_user}' if dt_user != '' else 'Silahkan Login'

        except Exception as e:
            toast_msg = f'Error Update Display: {e}'
            toast(toast_msg)       

    def regular_update_connection(self, dt):
        global flag_conn_stat
        global emission_device

        try:
            com_ports = list(ports.comports()) # create a list of com ['COM1','COM2'] 
            for i in com_ports:
                if i.name == COM_PORT_EMISSION:
                    flag_conn_stat = True

            emission_device = serial.Serial()
            emission_device.baudrate = 115200
            emission_device.port = COM_PORT_EMISSION
            emission_device.parity=serial.PARITY_NONE,
            emission_device.stopbits=serial.STOPBITS_ONE,
            emission_device.bytesize=serial.EIGHTBITS 

            emission_device.open()       
            
        except Exception as e:
            toast_msg = f'error initiate Emission Test Device'
            toast(toast_msg)   
            flag_conn_stat = False

    def exec_reload_database(self):
        global mydb
        try:
            mydb = mysql.connector.connect(host = DB_HOST, user = DB_USER, password = DB_PASSWORD, database = DB_NAME)
        except Exception as e:
            toast_msg = f'Error Initiate Database: {e}'
            toast(toast_msg)   

    def exec_reload_table(self):
        global mydb, db_antrian, db_merk
        global dt_dash_pendaftaran, dt_dash_belum_uji, dt_dash_sudah_uji

        try:
            tb_antrian = mydb.cursor()
            tb_antrian.execute(f"SELECT noantrian, nopol, nouji, emission_flag, user, merk, type, idjeniskendaraan, jbb, bahan_bakar, warna FROM {TB_DATA}")
            result_tb_antrian = tb_antrian.fetchall()
            mydb.commit()
            db_antrian = np.array(result_tb_antrian).T
            db_pendaftaran = np.array(result_tb_antrian)
            dt_dash_pendaftaran = db_pendaftaran[:,3].size
            dt_dash_belum_uji = np.where(db_pendaftaran[:,3] == 0)[0].size
            dt_dash_sudah_uji = np.where(db_pendaftaran[:,3] == 1)[0].size

            tb_merk = mydb.cursor()
            tb_merk.execute(f"SELECT ID, DESCRIPTION FROM {TB_MERK}")
            result_tb_merk = tb_merk.fetchall()
            mydb.commit()
            db_merk = np.array(result_tb_merk)
        except Exception as e:
            toast_msg = f'Error Fetch Database: {e}'
            print(toast_msg)

        try:
            layout_list = self.ids.layout_list
            layout_list.clear_widgets(children=None)
        except Exception as e:
            toast_msg = f'Error Remove Widget: {e}'
            print(toast_msg)
        
        try:           
            layout_list = self.ids.layout_list
            for i in range(db_antrian[0,:].size):
                layout_list.add_widget(
                    MDCard(
                        MDLabel(text=f"{db_antrian[0, i]}", size_hint_x= 0.05),
                        MDLabel(text=f"{db_antrian[1, i]}", size_hint_x= 0.08),
                        MDLabel(text=f"{db_antrian[2, i]}", size_hint_x= 0.08),
                        MDLabel(text='Lulus' if (int(db_antrian[3, i]) == 2) else 'Tidak Lulus' if (int(db_antrian[3, i]) == 1) else 'Belum Tes', size_hint_x= 0.08),
                        MDLabel(text=f"{db_antrian[4, i]}", size_hint_x= 0.12),
                        MDLabel(text=f"{db_merk[np.where(db_merk == db_antrian[5, i])[0][0],1]}", size_hint_x= 0.08),
                        MDLabel(text=f"{db_antrian[6, i]}", size_hint_x= 0.05),
                        MDLabel(text=f"{db_antrian[7, i]}", size_hint_x= 0.13),
                        MDLabel(text=f"{db_antrian[8, i]}", size_hint_x= 0.05),
                        MDLabel(text=f"{db_antrian[9, i]}", size_hint_x= 0.08),
                        MDLabel(text=f"{db_antrian[10, i]}", size_hint_x= 0.08),

                        ripple_behavior = True,
                        on_press = self.on_antrian_row_press,
                        padding = 20,
                        id=f"card_antrian{i}",
                        size_hint_y=None,
                        height="60dp",
                        )
                    )
        except Exception as e:
            toast_msg = f'Error Reload Table: {e}'
            print(toast_msg)

    def reset_data(self):
        global dt_emission_co_value, dt_emission_hc_value, dt_emission_smoke_value
        global count_starting, count_get_data
              
        count_starting = COUNT_STARTING
        count_get_data = COUNT_ACQUISITION
        dt_emission_co_value = 0.0
        dt_emission_hc_value = 0.0
        dt_emission_smoke_value = 0.0

    def regular_get_data_gass(self, dt):
        global flag_play
        global dt_emission_co_value, dt_emission_hc_value, dt_emission_smoke_value
        global count_starting, count_get_data
        global emission_device
        try:
            if flag_play:
                if(count_starting > 0):
                    count_starting -= 1              
                if(count_get_data > 0):
                    count_get_data -= 1
                    data_byte = emission_device.readline().decode("utf-8").strip()  # read the incoming data and remove newline character
                    if data_byte != "":
                        arr_data_byte = np.array(data_byte.split())
                        dt_emission_co_value = float(arr_data_byte[0])
                        dt_emission_hc_value = float(arr_data_byte[1])
                        dt_emission_smoke_value = float(arr_data_byte[2])

                elif(count_get_data <= 0):
                    flag_play = False
                    Clock.unschedule(self.regular_get_data_gass)
        except Exception as e:
            toast_msg = f'error get data: {e}'
            print(toast_msg) 

    def regular_get_data_diesel(self, dt):
        global flag_play
        global dt_emission_co_value, dt_emission_hc_value, dt_emission_smoke_value
        global count_starting, count_get_data
        global emission_device
        try:
            if flag_play:
                if(count_starting > 0):
                    count_starting -= 1              
                if(count_get_data > 0):
                    count_get_data -= 1
                    data_byte = emission_device.readline().decode("utf-8").strip()  # read the incoming data and remove newline character
                    if data_byte != "":
                        arr_data_byte = np.array(data_byte.split())
                        dt_emission_co_value = float(arr_data_byte[0])
                        dt_emission_hc_value = float(arr_data_byte[1])
                        dt_emission_smoke_value = float(arr_data_byte[2])
                elif(count_get_data <= 0):
                    flag_play = False
                    Clock.unschedule(self.regular_get_data_diesel)
        except Exception as e:
            toast_msg = f'error get data: {e}'
            print(toast_msg) 

    def exec_start(self):
        global dt_emission_flag, dt_no_antrian, dt_user, dt_emission_type
        global flag_play

        if (dt_user != ''):
            if (dt_emission_flag == 'Belum Tes'):
                if(not flag_play):
                    if(dt_emission_type == 0):
                        Clock.schedule_interval(self.regular_get_data_gass, GET_DATA_INTERVAL)
                        self.exec_start_gass_emission()
                        flag_play = True
                    else:
                        Clock.schedule_interval(self.regular_get_data_diesel, GET_DATA_INTERVAL)
                        self.exec_start_gass_diesel()
                        flag_play = True
            else:
                toast(f'No. Antrian {dt_no_antrian} Sudah Tes')
        else:
            toast(f'Silahkan Login Untuk Melakukan Pengujian')   

    def exec_start_gass_emission(self):
        global flag_play

        if(not flag_play):
            Clock.schedule_interval(self.regular_get_data_gass, GET_DATA_INTERVAL)
            self.open_screen_gass_emission()
            flag_play = True

    def exec_start_gass_diesel(self):
        global flag_play

        if(not flag_play):
            Clock.schedule_interval(self.regular_get_data_diesel, GET_DATA_INTERVAL)
            self.open_screen_diesel_emission()
            flag_play = True

    def open_screen_gass_emission(self):
        self.screen_manager.current = 'screen_gass_emission'

    def open_screen_diesel_emission(self):
        self.screen_manager.current = 'screen_diesel_emission'

    def exec_logout(self):
        global dt_user

        dt_user = ""
        self.screen_manager.current = 'screen_login'

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
            toast_msg = f'Error Navigate to Login Screen: {e}'
            toast(toast_msg)    

    def exec_navigate_main(self):
        try:
            self.screen_manager.current = 'screen_main'

        except Exception as e:
            toast_msg = f'Error Navigate to Main Screen: {e}'
            toast(toast_msg)   

class ScreenGassEmission(MDScreen):        
    def __init__(self, **kwargs):
        super(ScreenGassEmission, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 2)
        
    def delayed_init(self, dt):
        pass

    def exec_reload(self):
        global flag_play

        try:
            screen_main = self.screen_manager.get_screen('screen_main')
            screen_main.reset_data()
            self.ids.bt_reload.disabled = True
            if(not flag_play):
                Clock.schedule_interval(screen_main.regular_get_data_gass, GET_DATA_INTERVAL)
                flag_play = True
        except Exception as e:
            toast_msg = f'Error Reload: {e}'
            toast(toast_msg) 
        
    def exec_save(self):
        global mydb
        global dt_no_antrian
        global dt_emission_flag, dt_emission_co_value, dt_emission_hc_value, dt_emission_user, dt_emission_post

        try:
            self.ids.bt_save.disabled = True
            mycursor = mydb.cursor()
            sql = f"UPDATE {TB_DATA} SET emission_flag = %s, emission_co_value = %s, emission_hc_value = %s, emission_user = %s, emission_post = %s WHERE noantrian = %s"
            sql_emission_flag = (1 if dt_emission_flag == "Lulus" else 2)
            dt_emission_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
            sql_val = (sql_emission_flag, dt_emission_co_value, dt_emission_hc_value, dt_emission_user, dt_emission_post, dt_no_antrian)
            mycursor.execute(sql, sql_val)
            mydb.commit()
            self.exec_navigate_main()
        except Exception as e:
            toast_msg = f'Error Save Data: {e}'
            toast(toast_msg) 
        
    def exec_navigate_main(self):
        screen_main = self.screen_manager.get_screen('screen_main')
        screen_main.exec_reload_table()
        self.screen_manager.current = 'screen_main'

class ScreenDieselEmission(MDScreen):        
    def __init__(self, **kwargs):
        super(ScreenDieselEmission, self).__init__(**kwargs)
        Clock.schedule_once(self.delayed_init, 2)
        
    def delayed_init(self, dt):
        pass

    def exec_reload(self):
        global flag_play

        try:
            screen_main = self.screen_manager.get_screen('screen_main')
            screen_main.reset_data()
            self.ids.bt_reload.disabled = True
            if(not flag_play):
                Clock.schedule_interval(screen_main.regular_get_data_diesel, GET_DATA_INTERVAL)
                flag_play = True
        except Exception as e:
            toast_msg = f'Error Reload: {e}'
            toast(toast_msg) 
        
    def exec_save(self):
        global mydb
        global dt_no_antrian
        global dt_emission_flag, dt_emission_smoke_value, dt_emission_user, dt_emission_post

        try:
            self.ids.bt_save.disabled = True
            mycursor = mydb.cursor()
            sql = f"UPDATE {TB_DATA} SET emission_flag = %s, emission_smoke_value = %s, emission_user = %s, emission_post = %s WHERE noantrian = %s"
            sql_emission_flag = (1 if dt_emission_flag == "Lulus" else 2)
            dt_emission_post = str(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
            sql_val = (sql_emission_flag, dt_emission_smoke_value, dt_emission_user, dt_emission_post, dt_no_antrian)
            mycursor.execute(sql, sql_val)
            mydb.commit()
            self.exec_navigate_main()
        except Exception as e:
            toast_msg = f'Error Save Data: {e}'
            toast(toast_msg) 

    def exec_navigate_main(self):
        screen_main = self.screen_manager.get_screen('screen_main')
        screen_main.exec_reload_table()
        self.screen_manager.current = 'screen_main'

class RootScreen(ScreenManager):
    pass             

class GassEmissionApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.accent_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.icon = 'assets/images/logo-app.png'

        LabelBase.register(
            name="Orbitron-Regular",
            fn_regular="assets/fonts/Orbitron-Regular.ttf")
        
        LabelBase.register(
            name="Draco",
            fn_regular="assets/fonts/Draco.otf")        

        LabelBase.register(
            name="Recharge",
            fn_regular="assets/fonts/Recharge.otf") 
        
        theme_font_styles.append('Display')
        self.theme_cls.font_styles["Display"] = [
            "Orbitron-Regular", 72, False, 0.15]       

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
            "Recharge", 12, False, 0.15] 

        theme_font_styles.append('Body1')
        self.theme_cls.font_styles["Body1"] = [
            "Recharge", 12, False, 0.15] 
        
        theme_font_styles.append('Button')
        self.theme_cls.font_styles["Button"] = [
            "Recharge", 10, False, 0.15] 

        theme_font_styles.append('Caption')
        self.theme_cls.font_styles["Caption"] = [
            "Recharge", 8, False, 0.15]              
        
        Window.fullscreen = 'auto'
        Builder.load_file('main.kv')
        return RootScreen()
    
if __name__ == '__main__':
   GassEmissionApp().run()