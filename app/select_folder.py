import tkinter as tk
from tkinter import filedialog, messagebox
import os

def select_folders():
    """
    Opens file dialogs to select two different folders: input and output.
    Ensures that the selected folders are not the same.
    Returns the full paths for both input and output folders.
    """
    root = tk.Tk()
    root.withdraw()  

    # Select input folder
    input_folder = filedialog.askdirectory(title="Select Input Folder")
    if not input_folder:
        messagebox.showerror("Error", "Input folder not selected.")
        return None, None

    # Select output folder
    while True:
        output_folder = filedialog.askdirectory(title="Select Output Folder")
        if not output_folder:
            messagebox.showerror("Error", "Output folder not selected.")
            return None, None

        # Ensure that input and output folders are not the same
        if input_folder == output_folder:
            messagebox.showerror("Error", "Input and Output folders cannot be the same.")
        else:
            break

    return os.path.abspath(input_folder), os.path.abspath(output_folder)

if __name__ == "__main__":
    input_folder, output_folder = select_folders()
    if input_folder and output_folder:
        print(f"Selected input folder: {input_folder}")
        print(f"Selected output folder: {output_folder}")
