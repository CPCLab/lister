import tkinter
import customtkinter
from tkinter import ttk

customtkinter.set_appearance_mode("Light")  # Modes: "System" (standard), "Dark", "Light"
# note: while customtkinter provides a light/dark/system theme, in this code ttkinter is also used to support LabelFrame
# widget, and ttk does not provide this theming by default.
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class GeneralGUI(customtkinter.CTk):

    WIDTH = 920
    HEIGHT = 650
    def __init__(self):
        super().__init__()
        self.title("LISTER: Life Science Metadata Parser")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.resizable(False,False) # disable window resizing as it is not designed to be responsive design
        self.create_header_widgets()

    def on_closing(self, event=0):
        self.destroy()

    def create_header_widgets(self):

        # TOP FRAME
        self.header_frame = customtkinter.CTkFrame(master=self,height=70, fg_color="white")
        self.header_frame.grid_rowconfigure(0, weight=3)
        self.header_frame.grid(row=0, column=0, sticky="nswe", padx=0, pady=0)
        self.header_label = customtkinter.CTkLabel(
            master=self.header_frame, text="LISTER: Life Science Metadata Parser", text_font=("",18,'bold'))
        self.header_label.grid(column=0, row=1, sticky="w", pady=(10,0), padx=20)
        self.header_desc = customtkinter.CTkLabel(
            master=self.header_frame,
            text="LISTER utilizes API to fetch annotated experiments entry on eLabFTW and extract metadata on it.\n"
                "Please headover to https://github.com/fathoni/lister for more details.",
            text_font=("",10), justify="left", anchor=customtkinter.W)
        self.header_desc.grid(column=0, row=2, sticky="w", pady=(0,15), padx=20)


class InitialGUI(GeneralGUI):
    def __init__(self):
        super().__init__()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.switch_var = customtkinter.StringVar(value="off")
        self.create_widgets()


    def switch_event(self):
        print("switch toggled, current value:", self.switch_var.get())


    def create_widgets(self):

        # REQUIRED ARGUMENT FRAME
        self.req_label_frame = ttk.LabelFrame(master=self, text="Required arguments")
        self.req_label_frame.grid(row=1, column=0, sticky="nswe", padx=10, pady=(30,10))
        self.required_argument_frame = customtkinter.CTkFrame(master=self.req_label_frame)
        self.required_argument_frame.grid_rowconfigure(1, weight=0)
        self.required_argument_frame.grid(row=1, column=0, sticky="nswe", padx=10, pady=10)

        # OUTPUT FILE NAME
        self.output_filename_label = customtkinter.CTkLabel(
            master=self.required_argument_frame, text="Output File Name:", justify="right", anchor=customtkinter.W)
        self.output_filename_label.grid(column=0, row=0, sticky="w", pady=(20,0), padx=5)
        self.output_filename_info = customtkinter.CTkLabel(
            master=self.required_argument_frame, text="Filename for your metadata and outputs, without extension.",
            text_font=("",11))
        self.output_filename_info.grid(column=0, row=1, sticky="w", pady=0, padx=5)
        self.elabftw_filename_entry = customtkinter.CTkEntry(
            master=self.required_argument_frame, width=300, placeholder_text="Output File Name", border_width=1)
        self.elabftw_filename_entry.grid(column=0, row=2, pady=0, padx=5, sticky="w")

        # ELABFTW ID
        self.elabftw_id_label = customtkinter.CTkLabel(
            master=self.required_argument_frame, text="eLabFTW Experiment ID:")
        self.elabftw_id_label.grid(column=1,row=0, pady=(20,0), padx=25, sticky="w", columnspan=4)
        self.elabftw_id_info = customtkinter.CTkLabel(
            master=self.required_argument_frame,
            text="Integer indicated in the URL of the experiment.",  text_font=("",11))
        self.elabftw_id_info.grid(column=1,row=1, pady=0, padx=25, sticky="w", columnspan=4)
        self.elabftw_id_entry = customtkinter.CTkEntry(
            master=self.required_argument_frame, width=200, placeholder_text="eLabFTW ID", border_width=1)
        self.elabftw_id_entry.grid(column=1, row=2,  pady=0, padx=25, sticky="w")

        # ELABFTW ENDPOINT
        self.elabftw_endpoint_label = customtkinter.CTkLabel(
            master=self.required_argument_frame, text="eLabFTW API endpoint URL:")
        self.elabftw_endpoint_label.grid(column=0, row=3, sticky="w", pady=(20,0), padx=5)
        self.elabftw_endpoint_info = customtkinter.CTkLabel(
            master=self.required_argument_frame,
            text="This would look like [your eLabFTW URL]/api/v1, or please ask your administrator.",
            text_font=("",11))
        self.elabftw_endpoint_info.grid(column=0, row=4, sticky="w", pady=0, padx=5)
        self.elabftw_endpoint_entry = customtkinter.CTkEntry(
            master=self.required_argument_frame, width=300, placeholder_text="eLabFTW API endpoint URL", border_width=1)
        self.elabftw_endpoint_entry.grid(column=0, row=5, pady=0, padx=5, sticky="w")

        # BASE OUTPUT DIR
        self.base_output_label = customtkinter.CTkLabel(
            master=self.required_argument_frame, text="Base Output Directory:")
        self.base_output_label.grid(column=1,row=3, pady=(20,0), padx=25, sticky="w", columnspan=4)
        self.base_output_info = customtkinter.CTkLabel(
            master=self.required_argument_frame, text="Local directory to save the outputs.", text_font=("",11))
        self.base_output_info.grid(column=1,row=4, pady=0, padx=25, sticky="w", columnspan=4)
        self.base_output_entry = customtkinter.CTkEntry(
            master=self.required_argument_frame,
            width=200, placeholder_text="Base output directory", border_width=1)
        self.base_output_entry.grid(column=1, row=5,  pady=0, padx=25, sticky="w")
        self.output_dir_browse_button = customtkinter.CTkButton(
            master=self.required_argument_frame, text="Browse...", command=self.button_event)
        self.output_dir_browse_button.grid(column=2, row=5,  pady=0, padx=25, sticky="w")

        # ELABFTW TOKEN
        self.elabftw_token_label = customtkinter.CTkLabel(
            master=self.required_argument_frame, text="eLabFTW API Token:", anchor=customtkinter.W)
        self.elabftw_token_label.grid(column=0,row=6, pady=(20,0), padx=5, sticky="w", columnspan=4)
        self.elabftw_token_label = customtkinter.CTkLabel(
            master=self.required_argument_frame, text="Please ask your admin to generate an eLabFTW API token for you.",
            text_font=("",11))
        self.elabftw_token_label.grid(column=0,row=7, pady=0, padx=5, sticky="w", columnspan=4)
        self.elabftw_token_entry = customtkinter.CTkEntry(
            master=self.required_argument_frame, width=600, placeholder_text="eLabFTW API Token", border_width=1)
        self.elabftw_token_entry.grid(column=0, row=8,  pady=(0,20), padx=5, sticky="w", columnspan=4)

        # OPTIONAL ARGS FRAME
        self.optional_label_frame = ttk.LabelFrame(master=self, text="Optional arguments")
        self.optional_label_frame.grid(row=2, column=0, sticky="nswe", padx=10, pady=(20,10))
        self.optional_argument_frame = customtkinter.CTkFrame(master=self.optional_label_frame)
        self.optional_argument_frame.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
        self.upl_to_elab_switch = customtkinter.CTkSwitch(
            master=self.optional_argument_frame, text="Upload extracted output to the corresponding eLabFTW entry",
            command=self.switch_event, variable=self.switch_var, onvalue="on", offvalue="off")
        self.upl_to_elab_switch.grid(row=1, column=0)

        # FINISHING STEP
        self.run_frame = customtkinter.CTkFrame(master=self, fg_color="#EBEBEC")
        self.run_frame.grid(row=3, column=0, sticky="e", padx=5, pady=(10,10))
        self.run_btn = customtkinter.CTkButton(
            master=self.run_frame, text="   Run   ", command=self.run_button_event)
        self.run_btn.grid(column=3, row=0, padx=(30,30), pady=10)


    def button_event(self):
        # dummy function for now
        print("button clicked")

    def back_button(self):
        self.output_txtbox.destroy()
        self.back_to_lister_frame.destroy()
        self.create_widgets()


    def run_button_event(self):
        self.req_label_frame.destroy()
        self.optional_label_frame.destroy()
        self.run_frame.destroy()

        # CREATE NEW FRAME FOR TEXTBOX
        self.mytext ='Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ' \
                     'ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo ' \
                     'duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum ' \
                     'dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod ' \
                     'tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et ' \
                     'accusam et justo duo dolores et ea rebum Stet clita kasd gubergren, no sea takimata sanctus ' \
                     'est Lorem ipsum dolor sit amet.'
        self.output_txtbox = tkinter.Text(master=self, state="normal", width=122, height=37)
        self.output_txtbox.insert(tkinter.END, self.mytext)
        self.output_txtbox.configure(state='disabled')
        self.output_txtbox.grid(row=1, column=0, sticky="w", padx=25, pady=10)

        # CREATE NEW FRAME FOR BACK BUTTON
        self.back_to_lister_frame = customtkinter.CTkFrame(master=self, fg_color="#EBEBEC")
        self.back_to_lister_frame.grid(row=3, column=0, sticky="e", padx=5, pady=(10, 10))
        self.lister_back_btn = customtkinter.CTkButton(
            master=self.back_to_lister_frame, text="   Back   ", command=self.back_button)
        self.lister_back_btn.grid(column=3, row=0, padx=(30,30), pady=10)


if __name__ == "__main__":
    app = InitialGUI()
    app.mainloop()