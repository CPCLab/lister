import tkinter
import customtkinter


# https://stackoverflow.com/questions/31844173/tkinter-sticky-not-working-for-some-frames

customtkinter.set_appearance_mode("Light")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class MainGUI(customtkinter.CTk):
    WIDTH = 680
    HEIGHT = 680

    def __init__(self):
        super().__init__()

        self.title("LISTER: Life Science Metadata Parser")
        self.geometry(f"{MainGUI.WIDTH}x{MainGUI.HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # two cols, 8 rows
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
       # self.grid_columnconfigure(1, weight=1)

        self.create_widgets()

    def create_widgets(self):

        # TOP FRAME
        self.header_frame = customtkinter.CTkFrame(master=self)
        self.header_frame.grid_rowconfigure(0, weight=3)
        self.header_frame.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)


        # MID FRAME
        self.required_argument_frame = customtkinter.CTkFrame(master=self)
        self.required_argument_frame.grid_rowconfigure(1, weight=0)
        self.required_argument_frame.grid(row=1, column=0, sticky="nswe", padx=10, pady=10)
        # OUTPUT FILE NAME
        self.output_filename_label = customtkinter.CTkLabel(master=self.required_argument_frame, text="Output File Name", fg_color=("red", "gray75"), text_font=("",15))
        self.output_filename_label.grid(column=0, row=0, sticky="w", pady=5, padx=5)
        self.elabftw_filename_entry = customtkinter.CTkEntry(master=self.required_argument_frame, width=300, placeholder_text="Output File Name")
        self.elabftw_filename_entry.grid(column=0, row=1, pady=5, padx=5, sticky="w")
        # ELABFTW ID
        self.elabftw_id_label = customtkinter.CTkLabel(master=self.required_argument_frame, text="eLabFTW Experiment ID", fg_color=("white", "gray75"))
        self.elabftw_id_label.grid(column=1,row=0, pady=5, padx=25, sticky="w", columnspan=4)
        self.elabftw_id_entry = customtkinter.CTkEntry(master=self.required_argument_frame, width=200, placeholder_text="eLabFTW ID")
        self.elabftw_id_entry.grid(column=1, row=1,  pady=5, padx=25, sticky="w")
        # ELABFTW ENDPOINT
        self.elabftw_endpoint_label = customtkinter.CTkLabel(master=self.required_argument_frame, text="eLabFTW API endpoint URL", fg_color=("red", "gray75"), text_font=("",15))
        self.elabftw_endpoint_label.grid(column=0, row=2, sticky="w", pady=5, padx=5)
        self.elabftw_endpoint_entry = customtkinter.CTkEntry(master=self.required_argument_frame, width=300, placeholder_text="eLabFTW API endpoint URL")
        self.elabftw_endpoint_entry.grid(column=0, row=3, pady=5, padx=5, sticky="w")
        # BASE OUTPUT DIR
        self.base_output_label = customtkinter.CTkLabel(master=self.required_argument_frame, text="Base Output Directory", fg_color=("white", "gray75"))
        self.base_output_label.grid(column=1,row=2, pady=5, padx=25, sticky="w", columnspan=4)
        self.base_output_entry = customtkinter.CTkEntry(master=self.required_argument_frame, width=200, placeholder_text="Base output directory")
        self.base_output_entry.grid(column=1, row=3,  pady=5, padx=25, sticky="w")
        # ELABFTW TOKEN
        self.elabftw_token_label = customtkinter.CTkLabel(master=self.required_argument_frame, text="eLabFTW API Token", fg_color=("white", "gray75"))
        self.elabftw_token_label.grid(column=0,row=4, pady=5, padx=5, sticky="w", columnspan=4)
        self.elabftw_token_entry = customtkinter.CTkEntry(master=self.required_argument_frame, width=400, placeholder_text="Base output directory")
        self.elabftw_token_entry.grid(column=0, row=5,  pady=5, padx=5, sticky="w", columnspan=4)


        # BOTTOM FRAME
        self.optional_argument_frame = customtkinter.CTkFrame(master=self)
        self.optional_argument_frame.grid(row=2, column=0, sticky="nswe", padx=10, pady=10)
        # self.frame_left = customtkinter.CTkFrame(master=self)
        # 1self.frame_left.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)

        # self.frame_right = customtkinter.CTkFrame(master=self)
        # self.frame_right.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)








        # self.frame_left = customtkinter.CtkFrame(master=self, width=390, corner_radius=0)


        # self.frame_right()

        # row
        # col
        # frame_right
        # frame_left

        # self.entry = customtkinter.CTkEntry(master=self.frame_right, width=120, placeholder_text="CTkEntry")
        # self.entry.grid(row=8, column=0, column_span=1, pady=20, padx=20, sticky="we")

    def on_closing(self, event=0):
        self.destroy()

    def change_appearance_mode(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)


if __name__ == "__main__":
    app = MainGUI()
    app.mainloop()


