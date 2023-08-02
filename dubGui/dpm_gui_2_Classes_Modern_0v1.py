import tkinter as tk
from tkinter import ttk
# import customtkinter as ctk
import ttkbootstrap as tb


# ctk.set_appearance_mode("system")  # default
# ctk.set_appearance_mode("dark")
# ctk.set_appearance_mode("light")
# Themes: "blue" (standard), "green", "dark-blue"
# ctk.set_default_color_theme("dark-blue")


class App(tb.Window):
    '''App inherits from tk.Tk
    '''

    def __init__(self, title, size):

        # main setup
        # Light:
        # * cosmo, flatly, journal, litera, lumen, minty, pulse, sandstone, united, yeti, morph, simplex, cerculean
        # Dark:
        # * solar, superhero, darkly, cyborg, vapor
        super().__init__(themename='darkly')  # ensures App(tk.Tk) works correctly
        self.title(title)
        self.geometry(f'{size[0]}x{size[1]}')
        self.minsize(size[0], size[1])
        self.maxsize(1024, 768)
        # self.resizable(True, True)

        # widgets
        # ******************************************
        # ******             TABS           ********
        # ******************************************
        tabsFrm = tb.Notebook(self)

        tab1 = tb.Frame(tabsFrm)
        tab2 = tb.Frame(tabsFrm)
        tab3 = tb.Frame(tabsFrm)

        tabsFrm.add(tab1, text='Measurements')
        tabsFrm.add(tab2, text='DPM Configuration')
        tabsFrm.add(tab3, text='Connection')
        tabsFrm.pack(expand=True, fill='both')

        # ***************************
        # ****** Status Bar *********
        # ***************************
        stsBar = tb.Label(self, text='Not connected', font=(
            "Helvetica", 10), anchor='w', justify='left')
        stsBar.config(border=1, relief='sunken')
        stsBar.pack(fill='x', anchor='w',
                    padx=10, pady=5, ipady=3)

        self.measFrm = MeasFrm(tab1)
        # self.stsFrm

        self.mainloop()


# class MeasFrm(tb.Frame):
class MeasFrm(tb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # tb.Label(self, text='Vshunt', background='red').pack(
        #     expand=True, fill='both')  # make Frame visible

        # Pack the Frame
        self.pack(expand=True, fill='both')
        # self.grid(row=0, column=0, sticky='nswe')
        # self.place(relx=0.05, rely=0.1, relwidth=0.7, relheight=.7)

        self.create_widgets()

    def create_widgets(self):

        # Create a 2 frames within the tab (for Measurements and the Start button)
        measFrm = tb.Frame(self)
        btnFrm = tb.Frame(self)

        # measFrm.pack(side='left', expand=True, fill='both')
        # btnFrm.pack(side='left', expand=True, fill='both')

        measFrm.place(x=0, rely=0.2, relwidth=.6, relheight=.6)
        btnFrm.place(relx=0.6, rely=0.2, relwidth=.4, relheight=.4)

        # create the grid
        measFrm.rowconfigure((0, 1, 2, 3), weight=1, uniform='a')
        measFrm.columnconfigure((0, 1, 2), weight=1)

        # Test Labels to visualize measFrm and btnFrm
        # tb.Label(measFrm, text='Test Label', background='red').pack(
        #     expand=True, fill='both')  # make Frame visible
        # tb.Label(btnFrm, text='Test Label', background='blue').pack(
        #     expand=True, fill='both')  # make Frame visible

        # create the widgets
        # ROW 1. Labels for: shunt voltage, measurement value and unit

        tb.Label(measFrm, text='Vshunt', bootstyle='primary').grid(
            row=0, column=0, padx=5, pady=5, sticky='e')
        self.vshunt_lbl = tb.Label(
            measFrm, text='0', anchor='e', bootstyle='primary-inverse')
        # self.vshunt_lbl = tb.Label(measFrm, text='0', relief='sunken', width=20,
        #                            anchor='e', font=('Calibri', 12))
        self.vshunt_lbl.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        tb.Label(measFrm, text='mV', bootstyle='primary').grid(
            row=0, column=2, padx=10, pady=5, sticky='w')

        # ROW 2. Labels for: bus voltage, measurement value  and unit
        tb.Label(measFrm, text='Vbus', bootstyle='secondary').grid(
            row=1, column=0, padx=5, pady=5, sticky='e')

        self.vbus_lbl = tb.Label(measFrm, text='0', relief='sunken', width=20,
                                 anchor='e', bootstyle='secondary-inverse')
        self.vbus_lbl.grid(row=1, column=1, padx=5,
                           pady=5, sticky='ew')
        tb.Label(measFrm, text='V', bootstyle='secondary').grid(
            row=1, column=2, padx=10, pady=5, sticky='w')

        # ROW 3. Labels for: current, value and unit
        tb.Label(measFrm, text='Current').grid(
            row=2, column=0, padx=5, pady=5, sticky='e')
        self.i_lbl = tb.Label(measFrm, text='0', relief='sunken', width=20,
                              anchor='e', font=('Calibri', 12))
        self.i_lbl.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        tb.Label(measFrm, text='A').grid(
            row=2, column=2, padx=10, pady=5, sticky='w')

        # ROW 4. Labels for: power, value and unit
        tb.Label(measFrm, text='Power').grid(
            row=3, column=0, padx=5, pady=5, sticky='e')
        self.p_lbl = tb.Label(measFrm, text='0', relief='sunken', width=20,
                              anchor='e', font=('Calibri', 12))
        self.p_lbl.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        tb.Label(measFrm, text='mW').grid(
            row=3, column=2, padx=10, pady=5, sticky='w')

        self.start_stop_btn = tb.Button(
            btnFrm, text='START', command=self.start_stop)
        self.start_stop_btn.pack(expand=True, ipadx=40, ipady=40)

    def start_stop(self):
        pass

    # class Main(tb.Frame):
    #     def __init__(self, parent):
    #         super().__init__(parent)
    #         tb.Label(self, background='red').pack(expand=True, fill='both')
    #         self.place(relx=0.3, y=0, relwidth=0.7, relheight=1)

    #         self.create_widgets()

    #     def create_widgets(self):
    #         pass


App('DPM Dashboard App', (600, 400))
