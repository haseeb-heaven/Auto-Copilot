import os
import time
from libs.keybindings_parser import KeybindingsParser
import libs.logger
from watchdog.events import FileSystemEventHandler
from libs.code_runner import CodeRunner
import pyautogui
import pyperclip

class FileMonitor(FileSystemEventHandler):
    keybindings_parser = None
    keybindings_keys = None
    max_retry_attempts = 5
    retry_attempts = 0
    
    def __init__(self, filename, compiler,monitor_time=15):
        self.monitor_time = monitor_time
        self.last_modified = os.path.getmtime(filename)
        self.filename = filename
        self.compiler = compiler
        self.logger = libs.logger.Logger.setup_logger()
        
        # Initialize the parser
        self.keybindings_parser = KeybindingsParser()
        self.keybindings_parser.load_keybindings()
        keybingings_commands = ["inlineChat.start","interactive.acceptChanges"]
        self.keybindings_keys = self.keybindings_parser.get_keybindings_keys(keybingings_commands)
        self.logger.info(f"Keybindings commands: {keybingings_commands}")
        self.logger.info(f"Keybindings keys: {self.keybindings_keys}")

    def self_fix_error(self,code_error):

        # show the UI error window 
        print("Fixing the auto error")

        self.logger.info("Trying to copy the error to the clipboard")
        
        result = "This is the error in the code \n" + code_error + "\n Please try to fix it and only give relevant code and dont change anything else beside this code snippet\n"
        if result:
            pyperclip.copy(code_error)
        else:
            self.logger.info("Error is empty")
            print("Error is empty")
            return False
        
        self.logger.info("Copied the error to the clipboard")
        print("Copied the error to the clipboard")
        
        # selecting all code
        self.logger.info("Trying to select all code")
        print("Trying to select all code")
        pyautogui.hotkey('command', 'a')
        time.sleep(1)
        
        # Opening the interactive window
        self.logger.info("Trying to open the interactive window")
        print("Trying to open the interactive window")
        # using pyautgui click these keys to open the interactive window
        pyautogui.hotkey(self.keybindings_keys[0]) # inlineChat.start
        self.logger.info("Opened the interactive window")
        time.sleep(3)
        
        # Setting error in the interactive window
        pyautogui.hotkey('command', 'v')
        self.logger.info("Pasted the error in the interactive window")
        print("Pasted the error in the interactive window")
        
        # Starting the request and waiting for the response
        pyautogui.press('enter')
        
        # Waiting for the response
        time.sleep(self.monitor_time)
        print("Trying accepting the solution")
        
        # Accepting the solution.
        pyautogui.hotkey(self.keybindings_keys[1]) # interactive.acceptChanges
        print("Fixed the error with the solution")
        
        # Saving the file
        self.logger.info("Trying to save the file")
        print("Trying to save the file")
        pyautogui.hotkey('command', 's')
        self.logger.info("Saved the file")
        
        return True
                    
    def on_modified(self, event):
        self.logger.info(f"Event: {event} src_path: {event.src_path} filename: {self.filename}")
        if self.filename in event.src_path:
            self.logger.info(f"File {self.filename} modified.")
            current_modified = os.path.getmtime(self.filename)
            if current_modified != self.last_modified:
                self.last_modified = current_modified
                self.logger.info(f"File {self.filename} modified. Compiling and running.")
                runner = CodeRunner()
                self.logger.info(f"Running code: {open(self.filename).read()}")
                code_output,code_error = runner.run_code(open(self.filename).read(), self.compiler)
                
                # clear the previous output
                print("\033c")
                
                # Print the compiler output to the console
                print(f"Output: {code_output}")
                print(f"Error: {code_error}")

                try:
                    # check if result is an error
                    if code_error:
                        result = self.self_fix_error(code_error)
                        # Check if output contains error.
                        if code_output:
                            if "error" in code_output.lower():
                                result += "\n" + code_output
                        if result:
                            print("The error has been fixed successfully")
                            code_error = None # Clear the error
                        else:
                            print(f"Trying to fix error {self.retry_attempts} time")
                            self.logger.info(f"Trying to fix error {self.retry_attempts} time")
                            self.retry_attempts += 1
                            if self.retry_attempts > self.max_retry_attempts:
                                print("The error could not be fixed")
                                self.retry_attempts = 0
                        
                except Exception as exception:
                    raise exception