import pandas as pd
from sql_api.SQL_API import SQL_Writer
import datetime as dt
import time


class Data:
    def __init__(self, connection=None):

        #database connection
        self.connection = SQL_Writer()
        # camera settings
        self.camera_setting = None

        # gui data
        self.input_qr_img_path = None
        self.output_path = None
        self.save_qr_data = None
        self.generated_qr_data = None
        self.loaded_qr_data = None
        self.decoded_qr_data = None
        self.filepath = None
        self.processing = None

        #database data
        self.benefit_df = self.connection.get_df_select_benefits()
        self.gesch_bene_df = self.connection.get_df_select_gesch_bene()
        self.qr_code_df = self.connection.get_df_select_qr_code()
        self.bi_light_df = self.connection.get_df_select_bi_light()
        self.selected_geschaeft = None
        self.selected_geschaeft_benefit = None
        self.now = dt.datetime.now()
        self.day = self.now.day
        self.month = self.now.month
        self.refresh_time = self.get_current_time()
        self.weekdaydict = {0:"Montag",
                            1:"Dienstag",
                            2:"Mittwoch",
                            3:"Donnerstag",
                            4:"Freitag",
                            5:"Samstag",
                            6:"Sonntag"}
        self.today_data = self.set_today_data()


    def get_current_time(self):
        """ Helper function to get the current time in seconds. """

        now = dt.datetime.now()
        total_time = (now.hour * 3600) + (now.minute * 60) + now.second
        return total_time

    def get_benefits_of_geschaeft(self, geschaeft):
        return self.connection.get_geschaeft(geschaeft)

    def select_benefit_of_geschaeft(self, geschaeft, benefit):
        return self.connection.get_geschaeft_benefit(geschaeft, benefit)

    def set_today_data(self):
        now = dt.datetime.now()
        hour = now.hour
        today = now.day
        weekday = int(str(now.weekday()))
        weekday = self.weekdaydict[weekday]
        month = now.month
        df = pd.DataFrame(data= {"now": [now],
                                 "hour": [hour],
                                 "today": [today],
                                 "weekday": [weekday],
                                 "month": [month]
                                 })
        return df

    def refresh_data(self):
        if (self.get_current_time() - self.refresh_time) > 120:
            self.connection.reconnect_to_Database()
            time.sleep(1)
            self.refresh_time = self.get_current_time()
            print('- {} - '.format(dt.datetime.now()))
            print('refreshed')
            try:
                self.benefit_df = self.connection.get_df_select_benefits()
                self.gesch_bene_df = self.connection.get_df_select_geschaefte()
                self.qr_code_df = self.connection.get_df_select_qr_code()
                self.bi_light_df = self.connection.get_df_select_bi_light()
                self.today_data = self.set_today_data()
            except:
                return

if __name__ == '__main__':
    data = Data()
    df_count_benefits = data.bi_light_df.groupby(['Benefit']).size().reset_index(name='counts').sort_values(by=['counts'], ascending=False)
    print(df_count_benefits)