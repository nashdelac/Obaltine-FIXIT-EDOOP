import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import os
from datetime import datetime

#import MySQL connector
try:
    import mysql.connector

    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("mysql-connector-python not found. Please run: pip install mysql-connector-python")


#establish database connection
def get_db_connection():
    if not DB_AVAILABLE:
        return None
    try:
        return mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="",
            database="edoop_fixit_db"
        )
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        return None


#custom UI widget for a rounded button using canvas
class CanvasRoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, width=200, height=45, radius=12,
                 bg_color="#2C2C2C", hover_color="#404040", text_color="#ffffff",
                 border_color=None, border_width=0, font=("SF Pro", 11, "bold"),
                 canvas_bg="#ffffff", **kwargs):
        super().__init__(parent, width=width, height=height, bg=canvas_bg, bd=0, highlightthickness=0, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color

        outline_col = border_color if border_color else bg_color

        #draw the rounded background
        self.rect = self.draw_rounded_rect(
            border_width, border_width, width - border_width - 1, height - border_width - 1,
            radius, fill=bg_color, outline=outline_col, width=border_width
        )

        #add text to the button
        self.text_item = self.create_text(width // 2, height // 2, text=text, fill=text_color, font=font)

        #mouse events for hover effects and clicking
        for tag in (self.rect, self.text_item):
            self.tag_bind(tag, "<Enter>", self._on_enter)
            self.tag_bind(tag, "<Leave>", self._on_leave)
            self.tag_bind(tag, "<Button-1>", lambda e: self.command() if self.command else None)

    #mathematical logic to draw a polygon that looks like a rounded rectangle
    def draw_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    #hover state
    def _on_enter(self, event):
        self.itemconfig(self.rect, fill=self.hover_color)
        self.config(cursor="hand2")

    # default state
    def _on_leave(self, event):
        self.itemconfig(self.rect, fill=self.bg_color)
        self.config(cursor="")


#custom UI widget for rounded text entry (single line)
class RoundedEntry:
    def __init__(self, parent, canvas, x, y, width, height, radius=12, placeholder="", is_password=False,
                 bg_color="#ffffff", outline_color="#cccccc", validate_cmd=None):
        self.canvas = canvas
        self.placeholder = placeholder
        self.is_password = is_password
        self.placeholder_color = "#999999"
        self.default_fg = "#000000"
        self.current_show_char = "*" if is_password else ""

        #draw the rounded background shape
        points = [
            x + radius, y, x + width - radius, y, x + width, y, x + width, y + radius,
            x + width, y + height - radius, x + width, y + height, x + width - radius, y + height, x + radius,
            y + height,
            x, y + height, x, y + height - radius, x, y + radius, x, y
        ]
        self.bg_id = self.canvas.create_polygon(points, smooth=True, fill=bg_color, outline=outline_color, width=1.5)

        #configure the actual entry widget
        entry_kwargs = {"bd": 0, "highlightthickness": 0, "font": ("SF Pro", 12), "bg": bg_color, "fg": self.default_fg}
        if validate_cmd:
            entry_kwargs["validate"] = "key"
            entry_kwargs["validatecommand"] = validate_cmd

        self.entry = tk.Entry(parent, **entry_kwargs)

        # inset the entry slightly so its rectangular corners don't overlap the canvas curve
        inset_x = max(12, int(radius * 0.7))
        inset_y = max(8, int(radius * 0.3))
        self.entry.place(x=x + inset_x, y=y + inset_y, width=width - (inset_x * 2), height=height - (inset_y * 2))

        # bind focus events to handle placeholder text
        self.entry.bind("<FocusIn>", self.foc_in)
        self.entry.bind("<FocusOut>", self.foc_out)
        self.put_placeholder()

    #insert the grey placeholder text
    def put_placeholder(self):
        self.entry.delete(0, 'end')
        self.entry.insert(0, self.placeholder)
        self.entry.config(fg=self.placeholder_color, show="")

    #clear placeholder when user clicks in
    def foc_in(self, *args):
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, 'end')
            self.entry.config(fg=self.default_fg)
            if self.is_password:
                self.entry.config(show=self.current_show_char)

    #restore placeholder if user leaves it empty
    def foc_out(self, *args):
        if not self.entry.get():
            self.put_placeholder()

    #get the actual value, ignoring the placeholder
    def get_value(self):
        val = self.entry.get().strip()
        return "" if val == self.placeholder else val

    #show or hide password characters
    def toggle_password_visibility(self, is_visible):
        if not self.is_password:
            return
        self.current_show_char = "" if is_visible else "*"
        if self.entry.get() != self.placeholder and self.entry.get() != "":
            self.entry.config(show=self.current_show_char)


# ustom UI widget for multiline text areas
class RoundedText:
    def __init__(self, parent, canvas, x, y, width, height, radius=12, bg_color="#ffffff", outline_color="#cccccc"):
        self.canvas = canvas

        #draw rounded background
        points = [
            x + radius, y, x + width - radius, y, x + width, y, x + width, y + radius,
            x + width, y + height - radius, x + width, y + height, x + width - radius, y + height, x + radius,
            y + height,
            x, y + height, x, y + height - radius, x, y + radius, x, y
        ]
        self.bg_id = self.canvas.create_polygon(points, smooth=True, fill=bg_color, outline=outline_color, width=1.5)

        #configure the text widget
        self.text = tk.Text(parent, font=("SF Pro", 12), bd=0, highlightthickness=0, bg=bg_color)

        inset_x = max(12, int(radius * 0.7))
        inset_y = max(8, int(radius * 0.3))
        self.text.place(x=x + inset_x, y=y + inset_y, width=width - (inset_x * 2), height=height - (inset_y * 2))

    def get(self, *args, **kwargs):
        return self.text.get(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.text.delete(*args, **kwargs)


#main application controller that manages all screens
class FixitApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # lock the window to fullscreen
        self.attributes("-fullscreen", True)
        self.configure(bg="#222222")
        self.title("FIXIT - Pambayang Dalubhasaan Ng Marilao")

        self.current_user = None

        # configure global styles for tables and dropdowns
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("SF Pro", 11), rowheight=35, background="#ffffff", fieldbackground="#ffffff",
                        borderwidth=0)
        style.configure("Treeview.Heading", font=("SF Pro", 11, "bold"), background="#f8f9fa", foreground="#333333",
                        borderwidth=0)
        style.map("Treeview", background=[("selected", "#e0e0e0")], foreground=[("selected", "#000000")])
        style.configure("TCombobox", padding=5, font=("SF Pro", 12))

        # create a fixed-size main container centered on the screen
        self.container = tk.Frame(self, width=1536, height=864, bg="#ffffff")
        self.container.place(relx=0.5, rely=0.5, anchor="center")
        self.container.pack_propagate(False)

        self.frames = {}
        self.assets = {}

        #load all the screens into memory
        for F in (LoginScreen, RegisterScreen, HomeScreen, DashboardScreen, SubmitTicketScreen, MyTicketsScreen,
                  TicketManagementScreen, TicketArchiveScreen, MyAccountScreen):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.place(relwidth=1, relheight=1)

        #start at the login screen
        self.show_frame("LoginScreen")

    #switch to a different screen and refresh its data
    def show_frame(self, page_name):
        frame = self.frames[page_name]
        if hasattr(frame, "refresh_data"):
            frame.refresh_data()
        frame.tkraise()

    #show a custom popup to confirm logging out or exiting
    def confirm_logout(self):
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.geometry("430x200")

        #center the popup window dynamically
        popup.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (430 // 2)
        y = (screen_height // 2) - (200 // 2)
        popup.geometry(f"+{x}+{y}")

        popup.configure(bg="#ffffff", highlightthickness=2, highlightbackground="#cccccc")

        lbl = tk.Label(popup, text="Logout / Exit Application", font=("SF Pro", 14, "bold"), bg="#ffffff", fg="#1e1e1e")
        lbl.pack(pady=(25, 5))

        sub_lbl = tk.Label(popup, text="What would you like to do?", font=("SF Pro", 11), bg="#ffffff", fg="#555555")
        sub_lbl.pack(pady=(0, 20))

        btn_frame = tk.Frame(popup, bg="#ffffff", height=50)
        btn_frame.pack(fill="x", padx=15, pady=10)

        #button actions
        def do_logout():
            popup.destroy()
            self.current_user = None
            self.show_frame("LoginScreen")

        def do_exit():
            popup.destroy()
            self.destroy()

        def do_cancel():
            popup.destroy()

        self.create_rounded_button(btn_frame, "Log Out", do_logout, 10, 0, 120, 40, radius=8, bg_color="#2C2C2C",
                                   hover_color="#404040", text_color="#ffffff")
        self.create_rounded_button(btn_frame, "Exit App", do_exit, 140, 0, 120, 40, radius=8, bg_color="#EC221F",
                                   hover_color="#D01B18", text_color="#ffffff")
        self.create_rounded_button(btn_frame, "Cancel", do_cancel, 270, 0, 120, 40, radius=8, bg_color="#2C2C2C",
                                   hover_color="#404040", text_color="#ffffff")

    #load an image and save it so it doesn't get garbage collected
    def load_bg(self, filename):
        if filename not in self.assets:
            if os.path.exists(filename):
                img = Image.open(filename).resize((1536, 864), Image.LANCZOS)
                self.assets[filename] = ImageTk.PhotoImage(img)
            else:
                self.assets[filename] = ""
        return self.assets[filename]

    #factory method to create rounded buttons
    def create_rounded_button(self, parent, text, command, x, y, width, height, **kwargs):
        # clean up legacy kwargs if passed
        canvas_bg = kwargs.pop("canvas_bg", "#ffffff")

        #if drawing directly onto a canvas for transparency
        if hasattr(parent, 'canvas') and isinstance(parent.canvas, tk.Canvas):
            radius = kwargs.get('radius', 12)
            bg_color = kwargs.get('bg_color', "#2C2C2C")
            hover_color = kwargs.get('hover_color', "#404040")
            text_color = kwargs.get('text_color', "#ffffff")
            border_color = kwargs.get('border_color', None)
            border_width = kwargs.get('border_width', 0)
            font = kwargs.get('font', ("SF Pro", 11, "bold"))

            outline_col = border_color if border_color else bg_color

            x1 = x + border_width
            y1 = y + border_width
            x2 = x + width - border_width - 1
            y2 = y + height - border_width - 1
            r = radius

            points = [
                x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
                x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
                x1, y2, x1, y2 - r, x1, y1 + r, x1, y1
            ]

            rect = parent.canvas.create_polygon(points, smooth=True, fill=bg_color, outline=outline_col,
                                                width=border_width)
            text_item = parent.canvas.create_text(x + width // 2, y + height // 2, text=text, fill=text_color,
                                                  font=font)

            def on_enter(event, r=rect, hc=hover_color):
                parent.canvas.itemconfig(r, fill=hc)
                parent.canvas.config(cursor="hand2")

            def on_leave(event, r=rect, bc=bg_color):
                parent.canvas.itemconfig(r, fill=bc)
                parent.canvas.config(cursor="")

            def on_click(event, cmd=command):
                if cmd:
                    cmd()

            for tag in (rect, text_item):
                parent.canvas.tag_bind(tag, "<Enter>", on_enter)
                parent.canvas.tag_bind(tag, "<Leave>", on_leave)
                parent.canvas.tag_bind(tag, "<Button-1>", on_click)

            return rect, text_item
        else:
            # fallback for standard frames
            kwargs["canvas_bg"] = canvas_bg
            btn = CanvasRoundedButton(parent, text=text, command=command, width=width, height=height, **kwargs)
            btn.place(x=x, y=y)
            return btn

    #helper to make simple text clickable like a link
    def create_clickable_text(self, canvas, x, y, text, font, color, command, anchor="nw"):
        text_id = canvas.create_text(x, y, text=text, font=font, fill=color, anchor=anchor)
        canvas.tag_bind(text_id, "<Button-1>", lambda e: command())
        canvas.tag_bind(text_id, "<Enter>", lambda e: canvas.config(cursor="hand2"))
        canvas.tag_bind(text_id, "<Leave>", lambda e: canvas.config(cursor=""))
        return text_id

    #custom checkbox design drawn on a canvas
    def create_transparent_checkbox(self, canvas, text, x, y, variable, command=None, font=("SF Pro", 11),
                                    text_color="#333333"):
        box_size = 15

        # outline box
        box_id = canvas.create_rectangle(x, y, x + box_size, y + box_size, outline="#777777", fill="", width=1.5)

        # checkmark (hidden by default)
        check_id = canvas.create_line(x + 3, y + 8, x + 6, y + 12, x + 12, y + 4, fill="#1e1e1e", width=2,
                                      state="hidden")

        text_id = canvas.create_text(x + box_size + 8, y + box_size // 2 + 1, text=text, font=font, fill=text_color,
                                     anchor="w")

        #click logic to show/hide checkmark
        def toggle(event=None):
            current = variable.get()
            variable.set(not current)
            if variable.get():
                canvas.itemconfigure(check_id, state="normal")
            else:
                canvas.itemconfigure(check_id, state="hidden")
            if command:
                command()

        #initial state
        if variable.get():
            canvas.itemconfigure(check_id, state="normal")

        #bind clicks to all elements of the checkbox
        for item in (box_id, check_id, text_id):
            canvas.tag_bind(item, "<Button-1>", toggle)
            canvas.tag_bind(item, "<Enter>", lambda e: canvas.config(cursor="hand2"))
            canvas.tag_bind(item, "<Leave>", lambda e: canvas.config(cursor=""))

        return box_id, check_id, text_id


#Login
class LoginScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.canvas = tk.Canvas(self, width=1536, height=864, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        bg_image = self.controller.load_bg("Log In Page BG.png")
        if bg_image:
            self.canvas.create_image(0, 0, anchor="nw", image=bg_image)

        self.canvas.create_text(383, 305, text="Email", font=("SF Pro", 12, "bold"), fill="#333333", anchor="nw")
        self.email_entry = RoundedEntry(self, self.canvas, 368, 330, 800, 45, placeholder="Enter Your Email")

        self.canvas.create_text(383, 395, text="Password", font=("SF Pro", 12, "bold"), fill="#333333", anchor="nw")
        self.pwd_entry = RoundedEntry(self, self.canvas, 368, 416, 800, 45, placeholder="Enter Your Password",
                                      is_password=True)

        self.show_pwd_var = tk.BooleanVar()
        self.controller.create_transparent_checkbox(
            self.canvas, "Show Password", 383, 466, self.show_pwd_var,
            command=lambda: self.pwd_entry.toggle_password_visibility(self.show_pwd_var.get())
        )

        self.controller.create_rounded_button(self, "Sign In", self.attempt_login, 368, 517, 800, 40, radius=12,
                                              bg_color="#2C2C2C", hover_color="#404040", text_color="#ffffff")

        #add exit application link directly on login screen for convenience when fullscreen
        self.controller.create_clickable_text(self.canvas, 470, 592, "Don't Have an Account?",
                                              ("SF Pro", 12, "underline", "bold"),
                                              "#333333", lambda: controller.show_frame("RegisterScreen"),
                                              anchor="center")
        self.controller.create_clickable_text(self.canvas, 768, 847, "Exit Application",
                                              ("SF Pro", 11, "bold"),
                                              "#EC221F", lambda: self.controller.destroy(),
                                              anchor="center")

    #verify credentials against the database
    def attempt_login(self):
        email = self.email_entry.get_value()
        password = self.pwd_entry.get_value()

        if not email or not password:
            messagebox.showwarning("Input Error", "Please fill in both Email and Password fields.")
            return

        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error",
                                 "Cannot connect to MySQL database. Please ensure XAMPP MySQL is running.")
            return

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
            user = cursor.fetchone()
            conn.close()

            #navigate to correct screen based on user role
            if user:
                self.controller.current_user = user
                self.email_entry.put_placeholder()
                self.pwd_entry.put_placeholder()

                if user['role'] == 'admin':
                    self.controller.show_frame("TicketManagementScreen")
                else:
                    self.controller.show_frame("HomeScreen")
            else:
                messagebox.showerror("Login Failed", "Invalid Email or Password. Please try again.")
        except Exception as e:
            messagebox.showerror("Database Query Error", f"An error occurred: {e}")


#screen for new users to create an account
class RegisterScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.canvas = tk.Canvas(self, width=1536, height=864, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        bg_image = self.controller.load_bg("Create an Account BG.png")
        if bg_image:
            self.canvas.create_image(0, 0, anchor="nw", image=bg_image)

        #validation callback to restrict contact number to digits only & max 11 chars
        vcmd = (self.register(self.validate_contact), '%P')

        self.canvas.create_text(368, 255, text="First Name", font=("SF Pro", 12, "bold"), fill="#333333", anchor="nw")
        self.fn_entry = RoundedEntry(self, self.canvas, 368, 285, 380, 45, placeholder="Enter Your First Name")

        self.canvas.create_text(788, 255, text="Last name", font=("SF Pro", 12, "bold"), fill="#333333", anchor="nw")
        self.ln_entry = RoundedEntry(self, self.canvas, 788, 285, 380, 45, placeholder="Enter Your Last Name")

        self.canvas.create_text(368, 342, text="Contact Number", font=("SF Pro", 12, "bold"), fill="#333333",
                                anchor="nw")
        self.contact_entry = RoundedEntry(self, self.canvas, 368, 371, 380, 45, placeholder="Enter Your Contact Number",
                                          validate_cmd=vcmd)

        self.canvas.create_text(788, 342, text="Email", font=("SF Pro", 12, "bold"), fill="#333333", anchor="nw")
        self.email_entry = RoundedEntry(self, self.canvas, 788, 371, 380, 45, placeholder="Enter Your Email")

        self.canvas.create_text(368, 434, text="Password", font=("SF Pro", 12, "bold"), fill="#333333", anchor="nw")
        self.pwd_entry_1 = RoundedEntry(self, self.canvas, 368, 462, 800, 45, placeholder="Enter Your Password",
                                        is_password=True)

        self.canvas.create_text(368, 523, text="Confirm Password", font=("SF Pro", 12, "bold"), fill="#333333",
                                anchor="nw")
        self.pwd_entry_2 = RoundedEntry(self, self.canvas, 368, 551, 800, 45, placeholder="Confirm Password",
                                        is_password=True)

        self.show_pwd_var = tk.BooleanVar()

        def toggle_pwds():
            self.pwd_entry_1.toggle_password_visibility(self.show_pwd_var.get())
            self.pwd_entry_2.toggle_password_visibility(self.show_pwd_var.get())

        self.controller.create_transparent_checkbox(
            self.canvas, "Show Password", 368, 610, self.show_pwd_var, command=toggle_pwds
        )

        self.controller.create_rounded_button(self, "Register", self.process_registration, 368, 666, 800, 50, radius=12,
                                              bg_color="#2C2C2C", hover_color="#404040", text_color="#ffffff")
        self.controller.create_clickable_text(self.canvas, 768, 735, "← Back to Login", ("SF Pro", 12, "bold"),
                                              "#333333", lambda: controller.show_frame("LoginScreen"), anchor="center")

    #allows only digits and caps the entry length to 11 characters
    def validate_contact(self, P):
        if P == "" or P == "Enter Your Contact Number":
            return True
        return P.isdigit() and len(P) <= 11

    #check form details and insert new user into database
    def process_registration(self):
        first_name = self.fn_entry.get_value()
        last_name = self.ln_entry.get_value()
        contact = self.contact_entry.get_value()
        email = self.email_entry.get_value()
        pwd1 = self.pwd_entry_1.get_value()
        pwd2 = self.pwd_entry_2.get_value()

        if not first_name or not last_name or not contact or not email or not pwd1 or not pwd2:
            messagebox.showwarning("Validation Error", "All fields are required.")
            return

        if len(contact) != 11 or not contact.isdigit():
            messagebox.showwarning("Validation Error", "Contact Number must be exactly 11 digits.")
            return

        if pwd1 != pwd2:
            messagebox.showerror("Validation Error", "Passwords do not match.")
            return

        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Cannot connect to MySQL database.")
            return

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                messagebox.showerror("Duplicate Error", "An account with this email already exists.")
                conn.close()
                return

            cursor.execute(
                "INSERT INTO users (first_name, last_name, contact, email, password, role) VALUES (%s, %s, %s, %s, %s, 'user')",
                (first_name, last_name, contact, email, pwd1)
            )
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Account created successfully! You can now log in.")

            #reset inputs
            self.fn_entry.put_placeholder()
            self.ln_entry.put_placeholder()
            self.contact_entry.put_placeholder()
            self.email_entry.put_placeholder()
            self.pwd_entry_1.put_placeholder()
            self.pwd_entry_2.put_placeholder()

            self.controller.show_frame("LoginScreen")

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to register account: {e}")


#class for screens that need the top navigation bar
class NavScreen(tk.Frame):
    def __init__(self, parent, controller, bg_filename):
        super().__init__(parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=1536, height=864, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        bg_image = self.controller.load_bg(bg_filename)
        if bg_image:
            self.canvas.create_image(0, 0, anchor="nw", image=bg_image)

    #render the common top menu buttons
    def draw_top_nav(self):
        nav_style = {"radius": 16, "bg_color": "#FAF5EF", "hover_color": "#EAE5DF", "text_color": "#2C2C2C",
                     "font": ("SF Pro", 8, "bold"), "border_color": "#4A2F1D", "border_width": 1}
        self.controller.create_rounded_button(self, "DASHBOARD", lambda: self.controller.show_frame("DashboardScreen"),
                                              840, 70, 120, 33, **nav_style)
        self.controller.create_rounded_button(self, "SUBMIT A TICKET",
                                              lambda: self.controller.show_frame("SubmitTicketScreen"), 970, 70, 120,
                                              33, **nav_style)
        self.controller.create_rounded_button(self, "MY TICKETS", lambda: self.controller.show_frame("MyTicketsScreen"),
                                              1100, 70, 120, 33, **nav_style)
        self.controller.create_rounded_button(self, "MY ACCOUNT", lambda: self.controller.show_frame("MyAccountScreen"),
                                              1230, 70, 120, 33, **nav_style)
        self.controller.create_rounded_button(self, "LOG OUT", self.controller.confirm_logout, 1360, 70, 120, 33,
                                              **nav_style)

    #back button to return to home
    def draw_back_btn(self):
        self.controller.create_rounded_button(self, "←", lambda: self.controller.show_frame("HomeScreen"), 15, 810,
                                              40, 40, radius=8, bg_color="#2C2C2C", hover_color="#404040",
                                              text_color="#ffffff", border_color="#4A2F1D", border_width=2)


#standard user landing screen
class HomeScreen(NavScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Home BG.png")

        self.time_text = self.canvas.create_text(980, 552, text="", font=("SF Pro", 22, "bold"), fill="#1e1e1e",
                                                 anchor="center")
        self.date_text = self.canvas.create_text(984, 575, text="", font=("SF Pro", 14), fill="#555555",
                                                 anchor="center")
        self.update_clock()

        #menu buttons for the home screen
        btn_style = {"width": 250, "height": 100, "radius": 16, "bg_color": "#FAF5EF", "hover_color": "#EAE5DF",
                     "text_color": "#2C2C2C", "border_color": "#4A2F1D", "border_width": 1}
        self.controller.create_rounded_button(self, "DASHBOARD", lambda: controller.show_frame("DashboardScreen"), 317,
                                              152, **btn_style)
        self.controller.create_rounded_button(self, "SUBMIT A TICKET",
                                              lambda: controller.show_frame("SubmitTicketScreen"), 317, 267,
                                              **btn_style)
        self.controller.create_rounded_button(self, "MY TICKETS", lambda: controller.show_frame("MyTicketsScreen"), 317,
                                              382, **btn_style)
        self.controller.create_rounded_button(self, "MY ACCOUNT", lambda: controller.show_frame("MyAccountScreen"), 317,
                                              497, **btn_style)
        self.controller.create_rounded_button(self, "LOG OUT", self.controller.confirm_logout, 317, 612, **btn_style)

    #loop to keep time updating
    def update_clock(self):
        self.canvas.itemconfig(self.time_text, text=datetime.now().strftime("%I:%M:%S %p"))
        self.canvas.itemconfig(self.date_text, text=datetime.now().strftime("%A, %B %d, %Y"))
        self.controller.after(1000, self.update_clock)


#screen displaying user ticket statistics and recent activity
class DashboardScreen(NavScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Dashboard BG.png")
        self.draw_top_nav()
        self.draw_back_btn()

        #setup big counters
        self.canvas.create_text(338, 170, text="In Progress", font=("SF Pro", 16, "bold"), fill="#1e1e1e",
                                anchor="center")
        self.canvas.create_text(768, 170, text="Pending", font=("SF Pro", 16, "bold"), fill="#1e1e1e", anchor="center")
        self.canvas.create_text(1200, 170, text="Resolved", font=("SF Pro", 16, "bold"), fill="#1e1e1e",
                                anchor="center")

        self.in_prog_text = self.canvas.create_text(340, 255, text="00", font=("SF Pro", 48, "bold"), fill="#1e1e1e")
        self.pending_text = self.canvas.create_text(768, 255, text="00", font=("SF Pro", 48, "bold"), fill="#1e1e1e")
        self.resolved_text = self.canvas.create_text(1200, 255, text="00", font=("SF Pro", 48, "bold"), fill="#1e1e1e")

        self.canvas.create_text(120, 460, text="Recent Tickets", font=("SF Pro", 18, "bold"), fill="#1e1e1e",
                                anchor="nw")

        #build the table
        self.tree = ttk.Treeview(self, columns=("ID", "Issue", "Status", "Date"), show="headings", height=8)
        self.tree.heading("ID", text="Ticket #")
        self.tree.heading("Issue", text="Issue / Problem")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Date", text="Date Created")
        self.tree.column("ID", width=100, anchor="center")
        self.tree.column("Issue", width=635, anchor="center")
        self.tree.column("Status", width=200, anchor="center")
        self.tree.column("Date", width=200, anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.place(x=120, y=490, width=1288, height=310)
        scrollbar.place(x=1408, y=490, width=18, height=310)

    #fetch the latest counts and populate the table
    def refresh_data(self):
        user = self.controller.current_user
        if not user:
            return

        conn = get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT status, COUNT(*) AS cnt FROM tickets WHERE user_id = %s GROUP BY status",
                           (user['id'],))
            rows = cursor.fetchall()

            counts = {"In Progress": 0, "Pending": 0, "Resolved": 0}
            for row in rows:
                if row['status'] in counts:
                    counts[row['status']] = row['cnt']

            self.canvas.itemconfig(self.in_prog_text, text=f"{counts['In Progress']:02d}")
            self.canvas.itemconfig(self.pending_text, text=f"{counts['Pending']:02d}")
            self.canvas.itemconfig(self.resolved_text, text=f"{counts['Resolved']:02d}")

            for item in self.tree.get_children():
                self.tree.delete(item)

            cursor.execute(
                "SELECT id, title, status, DATE_FORMAT(date_created, '%m/%d/%Y %h:%i %p') AS dt FROM tickets WHERE user_id = %s ORDER BY date_created ASC",
                (user['id'],))
            all_user_tickets = cursor.fetchall()

            #assign a sequential number to user's tickets to hide database ID
            seq_map = {t['id']: f"#{idx + 1:03d}" for idx, t in enumerate(all_user_tickets)}

            for t in list(reversed(all_user_tickets))[:10]:
                self.tree.insert("", "end", iid=t['id'], values=(seq_map[t['id']], t['title'], t['status'], t['dt']))

            conn.close()

        except Exception as e:
            print(f"Dashboard refresh error: {e}")


#screen where user can create a new issue ticket
class SubmitTicketScreen(NavScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Submit Ticket BG.png")
        self.draw_top_nav()
        self.draw_back_btn()

        self.canvas.create_text(768, 160, text="SUBMIT A TICKET", font=("SF Pro", 22, "bold"), fill="#1e1e1e",
                                anchor="center")

        start_y = 270
        gap = 70

        self.canvas.create_text(360, start_y + 12, text="PROBLEM TITLE:", font=("SF Pro", 12, "bold"), fill="#333333",
                                anchor="ne")
        self.title_entry = RoundedEntry(self, self.canvas, 450, start_y, 800, 45, placeholder="Enter the Problem")

        self.canvas.create_text(360, start_y + gap + 12, text="CATEGORY:", font=("SF Pro", 12, "bold"), fill="#333333",
                                anchor="ne")
        categories = ["Classroom / Comlab", "Library", "HRM Stockroom", "Security", "Hardware / IT", "Software",
                      "Maintenance", "Furniture / Facility"]
        self.cat_combo = ttk.Combobox(self, values=categories, state="readonly")
        self.cat_combo.set("Classroom / Comlab")
        self.cat_combo.place(x=450, y=start_y + gap, width=800, height=45)

        self.canvas.create_text(360, start_y + gap * 2 + 12, text="LOCATION:", font=("SF Pro", 12, "bold"),
                                fill="#333333", anchor="ne")
        self.loc_entry = RoundedEntry(self, self.canvas, 450, start_y + gap * 2, 800, 45,
                                      placeholder="Enter the location, e.g., Room 103")

        self.canvas.create_text(360, start_y + gap * 3 + 12, text="DESCRIPTION:", font=("SF Pro", 12, "bold"),
                                fill="#333333", anchor="ne")
        self.desc_text = RoundedText(self, self.canvas, 450, start_y + gap * 3, 800, 130)

        self.canvas.create_text(360, start_y + gap * 3 + 150 + 12, text="PRIORITY:", font=("SF Pro", 12, "bold"),
                                fill="#333333", anchor="ne")
        self.prio_combo = ttk.Combobox(self, values=["Low", "Medium", "High"], state="readonly")
        self.prio_combo.set("Medium")
        self.prio_combo.place(x=450, y=start_y + gap * 3 + 150, width=300, height=45)

        # form action buttons
        self.controller.create_rounded_button(self, "CLEAR", self.clear_form, 930,
                                              start_y + gap * 3 + 150,
                                              130, 45, radius=10, bg_color="#EC221F", hover_color="#D01B18",
                                              text_color="#ffffff")
        self.controller.create_rounded_button(self, "SUBMIT TICKET", self.process_ticket_submission, 1090,
                                              start_y + gap * 3 + 150,
                                              140, 45, radius=10, bg_color="#2C2C2C", hover_color="#404040",
                                              text_color="#ffffff")

    #reset fields to empty
    def clear_form(self):
        self.title_entry.put_placeholder()
        self.loc_entry.put_placeholder()
        self.desc_text.delete("1.0", "end")
        self.cat_combo.set("Classroom / Comlab")
        self.prio_combo.set("Medium")

    #save ticket data into MySQL
    def process_ticket_submission(self):
        user = self.controller.current_user
        if not user:
            messagebox.showerror("Error", "No user logged in.")
            return

        title = self.title_entry.get_value()
        category = self.cat_combo.get()
        location = self.loc_entry.get_value()
        description = self.desc_text.get("1.0", "end-1c").strip()
        priority = self.prio_combo.get()

        if not title or not category or not location or not description:
            messagebox.showwarning("Validation Error", "Please fill in all ticket details.")
            return

        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Cannot connect to MySQL database.")
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tickets (title, category, location, description, priority, status, user_id) VALUES (%s, %s, %s, %s, %s, 'Pending', %s)",
                (title, category, location, description, priority, user['id'])
            )
            conn.commit()
            conn.close()

            messagebox.showinfo("Ticket Submitted", "Your ticket has been submitted successfully!")

            self.clear_form()

            self.controller.show_frame("MyTicketsScreen")

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to submit ticket: {e}")


#My Tickets displaying a list of all tickets submitted by the user
class MyTicketsScreen(NavScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "My Tickets BG.png")
        self.draw_top_nav()
        self.draw_back_btn()

        self.canvas.create_text(768, 160, text="MY TICKETS", font=("SF Pro", 22, "bold"), fill="#1e1e1e",
                                anchor="center")

        self.search_entry = RoundedEntry(self, self.canvas, 490, 210, 450, 45,
                                         placeholder="Search tickets by title, category", radius=20)

        self.controller.create_rounded_button(self, "search", self.refresh_data, 950, 210, 80, 45, radius=20,
                                              bg_color="#2C2C2C", hover_color="#404040", text_color="#ffffff")

        # table setup
        self.tree = ttk.Treeview(self, columns=("ID", "Issue", "Category", "Priority", "Status", "Assigned", "Date"),
                                 show="headings", height=10)
        self.tree.heading("ID", text="Ticket #")
        self.tree.heading("Issue", text="Issue Title")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Priority", text="Priority")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Assigned", text="Assigned To")
        self.tree.heading("Date", text="Date Created")

        self.tree.column("ID", width=80, anchor="center")
        self.tree.column("Issue", width=315, anchor="center")
        self.tree.column("Category", width=180, anchor="center")
        self.tree.column("Priority", width=110, anchor="center")
        self.tree.column("Status", width=130, anchor="center")
        self.tree.column("Assigned", width=160, anchor="center")
        self.tree.column("Date", width=180, anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.place(x=113, y=280, width=1278, height=400)
        scrollbar.place(x=1391, y=280, width=18, height=400)

        self.controller.create_rounded_button(self, "View Selected Ticket", self.view_selected_ticket, 668, 700, 200,
                                              45, radius=12, bg_color="#2C2C2C", hover_color="#404040",
                                              text_color="#ffffff")

    #query database for user tickets (supports search filtering)
    def refresh_data(self):
        user = self.controller.current_user
        if not user:
            return

        conn = get_db_connection()
        if not conn:
            return

        try:
            for item in self.tree.get_children():
                self.tree.delete(item)

            search_query = self.search_entry.get_value()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id FROM tickets WHERE user_id = %s ORDER BY date_created ASC", (user['id'],))
            seq_map = {row['id']: f"#{idx + 1:03d}" for idx, row in enumerate(cursor.fetchall())}

            if search_query:
                query = """
                    SELECT id, title, category, priority, status, assigned_to, DATE_FORMAT(date_created, '%m/%d/%Y %h:%i %p') AS dt
                    FROM tickets 
                    WHERE user_id = %s AND (title LIKE %s OR category LIKE %s OR status LIKE %s)
                    ORDER BY date_created DESC
                """
                like_str = f"%{search_query}%"
                cursor.execute(query, (user['id'], like_str, like_str, like_str))
            else:
                query = """
                    SELECT id, title, category, priority, status, assigned_to, DATE_FORMAT(date_created, '%m/%d/%Y %h:%i %p') AS dt
                    FROM tickets 
                    WHERE user_id = %s 
                    ORDER BY date_created DESC
                """
                cursor.execute(query, (user['id'],))

            tickets = cursor.fetchall()
            conn.close()

            for t in tickets:
                user_seq = seq_map.get(t['id'], f"#{t['id']:03d}")
                self.tree.insert("", "end", iid=t['id'], values=(
                    user_seq, t['title'], t['category'], t['priority'], t['status'], t['assigned_to'], t['dt']
                ))

        except Exception as e:
            print(f"Error fetching user tickets: {e}")

    #pop up a full view of the ticket details
    def view_selected_ticket(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a ticket from the table first.")
            return

        db_id = selected[0]
        conn = get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT *, DATE_FORMAT(resolved_at, '%m/%d/%Y %h:%i %p') AS resolved_dt FROM tickets WHERE id = %s",
                (db_id,))
            t = cursor.fetchone()

            cursor.execute("SELECT id FROM tickets WHERE user_id = %s ORDER BY date_created ASC", (t['user_id'],))
            seq_map = {row['id']: f"#{idx + 1:03d}" for idx, row in enumerate(cursor.fetchall())}
            conn.close()

            if t:
                user_num = seq_map.get(t['id'], f"#{t['id']:03d}")
                resolved_info = f"\nResolved Date & Time: {t['resolved_dt']}" if t['resolved_dt'] else ""
                details = (
                    f"User Ticket Number: {user_num}\n"
                    f"Global System ID: #{t['id']:03d}\n\n"
                    f"Title: {t['title']}\n"
                    f"Category: {t['category']}\n"
                    f"Location: {t['location']}\n"
                    f"Priority: {t['priority']}\n"
                    f"Status: {t['status']}\n"
                    f"Assigned Personnel: {t['assigned_to']}\n"
                    f"Date Created: {t['date_created']}{resolved_info}\n\n"
                    f"Description:\n{t['description']}"
                )
                messagebox.showinfo(f"Ticket {user_num} Details", details)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve details: {e}")


#screen displaying personal user details and history
class MyAccountScreen(NavScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "My Tickets BG.png")
        self.draw_top_nav()
        self.draw_back_btn()

        self.canvas.create_text(768, 160, text="ACCOUNT DETAILS", font=("SF Pro", 22, "bold"), fill="#1e1e1e",
                                anchor="center")

        self.canvas.create_text(480, 280, text="First Name:", font=("SF Pro", 15, "bold"), fill="#1e1e1e", anchor="nw")
        self.fn_val = self.canvas.create_text(720, 280, text="", font=("SF Pro", 15), fill="#555555", anchor="nw")

        self.canvas.create_text(480, 350, text="Last Name:", font=("SF Pro", 15, "bold"), fill="#1e1e1e", anchor="nw")
        self.ln_val = self.canvas.create_text(720, 350, text="", font=("SF Pro", 15), fill="#555555", anchor="nw")

        self.canvas.create_text(480, 420, text="Email Address:", font=("SF Pro", 15, "bold"), fill="#1e1e1e",
                                anchor="nw")
        self.em_val = self.canvas.create_text(720, 420, text="", font=("SF Pro", 15), fill="#555555", anchor="nw")

        self.canvas.create_text(480, 490, text="Contact Number:", font=("SF Pro", 15, "bold"), fill="#1e1e1e",
                                anchor="nw")
        self.cn_val = self.canvas.create_text(720, 490, text="", font=("SF Pro", 15), fill="#555555", anchor="nw")

        self.canvas.create_text(480, 560, text="Account Role:", font=("SF Pro", 15, "bold"), fill="#1e1e1e",
                                anchor="nw")
        self.role_val = self.canvas.create_text(720, 560, text="", font=("SF Pro", 15), fill="#555555", anchor="nw")

        self.canvas.create_text(480, 630, text="Total Submitted Tickets:", font=("SF Pro", 15, "bold"), fill="#1e1e1e",
                                anchor="nw")
        self.total_tickets_val = self.canvas.create_text(720, 630, text="0", font=("SF Pro", 15, "bold"),
                                                         fill="#1e1e1e", anchor="nw")

    #populate the text elements with current user session info
    def refresh_data(self):
        user = self.controller.current_user
        if user:
            self.canvas.itemconfig(self.fn_val, text=user.get('first_name', 'N/A'))
            self.canvas.itemconfig(self.ln_val, text=user.get('last_name', 'N/A'))
            self.canvas.itemconfig(self.em_val, text=user.get('email', 'N/A'))
            self.canvas.itemconfig(self.cn_val, text=user.get('contact', 'N/A'))
            self.canvas.itemconfig(self.role_val, text=user.get('role', 'user').upper())

            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM tickets WHERE user_id = %s", (user['id'],))
                    count = cursor.fetchone()[0]
                    conn.close()
                    self.canvas.itemconfig(self.total_tickets_val, text=str(count))
                except Exception as e:
                    print(f"Account count query error: {e}")


#screen for admins to manage unresolved tickets globally
class TicketManagementScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.canvas = tk.Canvas(self, width=1536, height=864, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        bg_image = self.controller.load_bg("Ticket Management BG.png")
        if bg_image:
            self.canvas.create_image(0, 0, anchor="nw", image=bg_image)

        self.time_text = self.canvas.create_text(1420, 80, text="", font=("SF Pro", 18, "bold"), fill="#1e1e1e",
                                                 anchor="ne")
        self.date_text = self.canvas.create_text(1420, 105, text="", font=("SF Pro", 13), fill="#555555", anchor="ne")
        self.update_clock()

        self.canvas.create_text(768, 140, text="TICKET MANAGEMENT", font=("SF Pro", 22, "bold"), fill="#1e1e1e",
                                anchor="center")

        self.search_entry = RoundedEntry(self, self.canvas, 490, 210, 450, 45,
                                         placeholder="Search problems, or categories...", radius=20)

        self.controller.create_rounded_button(self, "search", self.refresh_data, 950, 210, 80, 45, radius=20,
                                              bg_color="#2C2C2C", hover_color="#404040", text_color="#ffffff")

        #table setup
        self.tree = ttk.Treeview(self, columns=("ID", "Problem", "Category", "User", "Status", "Assigned", "Date"),
                                 show="headings", height=10)
        self.tree.heading("ID", text="Global ID")
        self.tree.heading("Problem", text="Problem")
        self.tree.heading("Category", text="Category")
        self.tree.heading("User", text="Submitted By")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Assigned", text="Assigned To")
        self.tree.heading("Date", text="Date Created")

        self.tree.column("ID", width=80, anchor="center")
        self.tree.column("Problem", width=305, anchor="center")
        self.tree.column("Category", width=180, anchor="center")
        self.tree.column("User", width=200, anchor="center")
        self.tree.column("Status", width=130, anchor="center")
        self.tree.column("Assigned", width=180, anchor="center")
        self.tree.column("Date", width=180, anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.place(x=120, y=280, width=1278, height=400)
        scrollbar.place(x=1398, y=280, width=18, height=400)

        #admin action buttons
        btn_style = {"radius": 8, "bg_color": "#2C2C2C", "hover_color": "#404040", "text_color": "#ffffff"}
        self.controller.create_rounded_button(self, "View Details", self.view_selected_ticket, 310, 700, 150, 45,
                                              **btn_style)
        self.controller.create_rounded_button(self, "Update Status", self.update_ticket_status, 480, 700, 150, 45,
                                              **btn_style)
        self.controller.create_rounded_button(self, "Assign", self.assign_personnel, 650, 700, 150, 45, **btn_style)
        self.controller.create_rounded_button(self, "Resolve Ticket", self.resolve_ticket, 820, 700, 150, 45,
                                              **btn_style)
        self.controller.create_rounded_button(self, "Resolved Archive →",
                                              lambda: controller.show_frame("TicketArchiveScreen"), 990, 700, 180, 45,
                                              **btn_style)

        self.controller.create_rounded_button(self, "LOG OUT", self.controller.confirm_logout, 1350, 800, 120, 35,
                                              radius=10, bg_color="#FAF5EF", hover_color="#EAE5DF",
                                              text_color="#2C2C2C")

    #update clock label
    def update_clock(self):
        self.canvas.itemconfig(self.time_text, text=datetime.now().strftime("%I:%M:%S %p"))
        self.canvas.itemconfig(self.date_text, text=datetime.now().strftime("%A, %B %d, %Y"))
        self.controller.after(1000, self.update_clock)

    #fetch all active tickets from the database
    def refresh_data(self):
        conn = get_db_connection()
        if not conn:
            return

        try:
            for item in self.tree.get_children():
                self.tree.delete(item)

            search_query = self.search_entry.get_value()
            cursor = conn.cursor(dictionary=True)

            if search_query:
                query = """
                    SELECT t.id, t.title, t.category, CONCAT(u.first_name, ' ', u.last_name) AS user_fullname, 
                           t.status, t.assigned_to, DATE_FORMAT(t.date_created, '%m/%d/%Y %h:%i %p') AS dt
                    FROM tickets t
                    JOIN users u ON t.user_id = u.id
                    WHERE t.status != 'Resolved' AND (t.title LIKE %s OR t.category LIKE %s OR u.first_name LIKE %s OR u.last_name LIKE %s OR t.status LIKE %s)
                    ORDER BY t.date_created DESC
                """
                like_str = f"%{search_query}%"
                cursor.execute(query, (like_str, like_str, like_str, like_str, like_str))
            else:
                query = """
                    SELECT t.id, t.title, t.category, CONCAT(u.first_name, ' ', u.last_name) AS user_fullname, 
                           t.status, t.assigned_to, DATE_FORMAT(t.date_created, '%m/%d/%Y %h:%i %p') AS dt
                    FROM tickets t
                    JOIN users u ON t.user_id = u.id
                    WHERE t.status != 'Resolved'
                    ORDER BY t.date_created DESC
                """
                cursor.execute(query)

            tickets = cursor.fetchall()
            conn.close()

            for t in tickets:
                self.tree.insert("", "end", iid=t['id'], values=(
                    f"#{t['id']:03d}", t['title'], t['category'], t['user_fullname'], t['status'], t['assigned_to'],
                    t['dt']
                ))

        except Exception as e:
            print(f"Admin fetch error: {e}")

    #admin view showing contact info of the user who submitted the ticket
    def view_selected_ticket(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a ticket from the management table first.")
            return

        ticket_id = selected[0]
        conn = get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT t.*, CONCAT(u.first_name, ' ', u.last_name) AS user_fullname, u.email, u.contact,
                       DATE_FORMAT(t.date_created, '%m/%d/%Y %h:%i %p') AS created_dt,
                       DATE_FORMAT(t.resolved_at, '%m/%d/%Y %h:%i %p') AS resolved_dt
                FROM tickets t
                JOIN users u ON t.user_id = u.id
                WHERE t.id = %s
            """
            cursor.execute(query, (ticket_id,))
            t = cursor.fetchone()
            conn.close()

            if t:
                resolved_info = f"\nResolved Date & Time: {t['resolved_dt']}" if t['resolved_dt'] else ""
                details = (
                    f"Global System ID: #{t['id']:03d}\n"
                    f"Submitted By: {t['user_fullname']}\n"
                    f"Contact: {t['contact']} | Email: {t['email']}\n\n"
                    f"Problem Title: {t['title']}\n"
                    f"Category: {t['category']}\n"
                    f"Location: {t['location']}\n"
                    f"Priority: {t['priority']}\n"
                    f"Status: {t['status']}\n"
                    f"Assigned To: {t['assigned_to']}\n"
                    f"Date Created: {t['created_dt']}{resolved_info}\n\n"
                    f"Description:\n{t['description']}"
                )
                messagebox.showinfo(f"Admin Ticket #{t['id']:03d} Full Details", details)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve ticket details: {e}")

    #prompt admin to change status manually
    def update_ticket_status(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a ticket to update.")
            return

        ticket_id = selected[0]
        new_status = simpledialog.askstring("Update Status", "Enter new status (Pending, In Progress, Resolved):")
        if new_status and new_status.strip().title() in ["Pending", "In Progress", "Resolved"]:
            formatted_status = new_status.strip().title()
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                if formatted_status == "Resolved":
                    cursor.execute("UPDATE tickets SET status = %s, resolved_at = NOW() WHERE id = %s",
                                   (formatted_status, ticket_id))
                else:
                    cursor.execute("UPDATE tickets SET status = %s, resolved_at = NULL WHERE id = %s",
                                   (formatted_status, ticket_id))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", f"Ticket #{int(ticket_id):03d} status updated to {formatted_status}.")
                self.refresh_data()
        elif new_status:
            messagebox.showerror("Invalid Status", "Status must be 'Pending', 'In Progress', or 'Resolved'.")

    #prompt admin to type in a name for ticket assignment
    def assign_personnel(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a ticket to assign.")
            return

        ticket_id = selected[0]
        personnel = simpledialog.askstring("Assign Ticket", "Enter personnel or department name:")
        if personnel and personnel.strip():
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE tickets SET assigned_to = %s WHERE id = %s", (personnel.strip(), ticket_id))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", f"Ticket #{int(ticket_id):03d} assigned to '{personnel.strip()}'.")
                self.refresh_data()

    #quick action to resolve and timestamp an active ticket
    def resolve_ticket(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a ticket to resolve.")
            return

        ticket_id = selected[0]
        if messagebox.askyesno("Confirm Resolve",
                               f"Mark Ticket #{int(ticket_id):03d} as Resolved and move to Archive?"):
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE tickets SET status = 'Resolved', resolved_at = NOW() WHERE id = %s",
                               (ticket_id,))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", f"Ticket #{int(ticket_id):03d} marked as Resolved and moved to Archive.")
                self.refresh_data()


#screen for admins to view resolved tickets
class TicketArchiveScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.canvas = tk.Canvas(self, width=1536, height=864, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        bg_image = self.controller.load_bg("Ticket Management BG.png")
        if bg_image:
            self.canvas.create_image(0, 0, anchor="nw", image=bg_image)

        self.time_text = self.canvas.create_text(1420, 80, text="", font=("SF Pro", 18, "bold"), fill="#1e1e1e",
                                                 anchor="ne")
        self.date_text = self.canvas.create_text(1420, 105, text="", font=("SF Pro", 13), fill="#555555", anchor="ne")
        self.update_clock()

        self.canvas.create_text(768, 140, text="RESOLVED TICKETS ARCHIVE", font=("SF Pro", 22, "bold"), fill="#1e1e1e",
                                anchor="center")

        self.search_entry = RoundedEntry(self, self.canvas, 490, 210, 450, 45, placeholder="Search resolved tickets...",
                                         radius=20)

        self.controller.create_rounded_button(self, "search", self.refresh_data, 950, 210, 80, 45, radius=20,
                                              bg_color="#2C2C2C", hover_color="#404040", text_color="#ffffff")

        self.tree = ttk.Treeview(self,
                                 columns=("ID", "Problem", "Category", "User", "Status", "Assigned", "ResolvedDate"),
                                 show="headings", height=10)
        self.tree.heading("ID", text="Global ID")
        self.tree.heading("Problem", text="Problem")
        self.tree.heading("Category", text="Category")
        self.tree.heading("User", text="Submitted By")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Assigned", text="Assigned To")
        self.tree.heading("ResolvedDate", text="Date & Time Resolved")

        self.tree.column("ID", width=80, anchor="center")
        self.tree.column("Problem", width=285, anchor="center")
        self.tree.column("Category", width=170, anchor="center")
        self.tree.column("User", width=190, anchor="center")
        self.tree.column("Status", width=120, anchor="center")
        self.tree.column("Assigned", width=170, anchor="center")
        self.tree.column("ResolvedDate", width=220, anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.place(x=120, y=280, width=1278, height=400)
        scrollbar.place(x=1398, y=280, width=18, height=400)

        self.controller.create_rounded_button(self, "View Selected Ticket", self.view_selected_ticket, 560, 700, 200,
                                              45, radius=8, bg_color="#2C2C2C", hover_color="#404040",
                                              text_color="#ffffff")
        self.controller.create_rounded_button(self, "← Back to Active Tickets",
                                              lambda: controller.show_frame("TicketManagementScreen"), 780, 700, 220,
                                              45, radius=8, bg_color="#2C2C2C", hover_color="#404040",
                                              text_color="#ffffff")

        self.controller.create_rounded_button(self, "LOG OUT", self.controller.confirm_logout, 1350, 800, 120, 35,
                                              radius=10, bg_color="#FAF5EF", hover_color="#EAE5DF",
                                              text_color="#2C2C2C")

    #loop to keep time updating
    def update_clock(self):
        self.canvas.itemconfig(self.time_text, text=datetime.now().strftime("%I:%M:%S %p"))
        self.canvas.itemconfig(self.date_text, text=datetime.now().strftime("%A, %B %d, %Y"))
        self.controller.after(1000, self.update_clock)

    #query only tickets with resolved status
    def refresh_data(self):
        conn = get_db_connection()
        if not conn:
            return

        try:
            for item in self.tree.get_children():
                self.tree.delete(item)

            search_query = self.search_entry.get_value()
            cursor = conn.cursor(dictionary=True)

            if search_query:
                query = """
                    SELECT t.id, t.title, t.category, CONCAT(u.first_name, ' ', u.last_name) AS user_fullname, 
                           t.status, t.assigned_to, DATE_FORMAT(t.resolved_at, '%m/%d/%Y %h:%i %p') AS resolved_dt
                    FROM tickets t
                    JOIN users u ON t.user_id = u.id
                    WHERE t.status = 'Resolved' AND (t.title LIKE %s OR t.category LIKE %s OR u.first_name LIKE %s OR u.last_name LIKE %s)
                    ORDER BY t.resolved_at DESC
                """
                like_str = f"%{search_query}%"
                cursor.execute(query, (like_str, like_str, like_str, like_str))
            else:
                query = """
                    SELECT t.id, t.title, t.category, CONCAT(u.first_name, ' ', u.last_name) AS user_fullname, 
                           t.status, t.assigned_to, DATE_FORMAT(t.resolved_at, '%m/%d/%Y %h:%i %p') AS resolved_dt
                    FROM tickets t
                    JOIN users u ON t.user_id = u.id
                    WHERE t.status = 'Resolved'
                    ORDER BY t.resolved_at DESC
                """
                cursor.execute(query)

            tickets = cursor.fetchall()
            conn.close()

            for t in tickets:
                res_time = t['resolved_dt'] if t['resolved_dt'] else "N/A"
                self.tree.insert("", "end", iid=t['id'], values=(
                    f"#{t['id']:03d}", t['title'], t['category'], t['user_fullname'], t['status'], t['assigned_to'],
                    res_time
                ))

        except Exception as e:
            print(f"Archive fetch error: {e}")

    #pop up showing completed ticket details
    def view_selected_ticket(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a ticket from the archive table first.")
            return

        ticket_id = selected[0]
        conn = get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT t.*, CONCAT(u.first_name, ' ', u.last_name) AS user_fullname, u.email, u.contact,
                       DATE_FORMAT(t.date_created, '%m/%d/%Y %h:%i %p') AS created_dt,
                       DATE_FORMAT(t.resolved_at, '%m/%d/%Y %h:%i %p') AS resolved_dt
                FROM tickets t
                JOIN users u ON t.user_id = u.id
                WHERE t.id = %s
            """
            cursor.execute(query, (ticket_id,))
            t = cursor.fetchone()
            conn.close()

            if t:
                details = (
                    f"Resolved Ticket Global ID: #{t['id']:03d}\n"
                    f"Submitted By: {t['user_fullname']}\n"
                    f"Contact: {t['contact']} | Email: {t['email']}\n\n"
                    f"Problem Title: {t['title']}\n"
                    f"Category: {t['category']}\n"
                    f"Location: {t['location']}\n"
                    f"Priority: {t['priority']}\n"
                    f"Status: {t['status']}\n"
                    f"Assigned Personnel: {t['assigned_to']}\n"
                    f"Date Created: {t['created_dt']}\n"
                    f"Date & Time Resolved: {t['resolved_dt']}\n\n"
                    f"Description:\n{t['description']}"
                )
                messagebox.showinfo(f"Archive Ticket #{t['id']:03d} Details", details)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve archive ticket details: {e}")


# boot up the application
if __name__ == "__main__":
    app = FixitApp()
    app.mainloop()