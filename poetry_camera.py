#!/usr/bin/env python3
"""
Local Poetry Camera
A camera that captures images and generates poems about what it sees using local Llama models.
"""

import cv2
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import base64
import threading
from datetime import datetime
import os
from PIL import Image, ImageTk
import io
import time

class PoetryCameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Poetry Camera")
        self.root.geometry("800x900")
        
        # Initialize camera
        self.cap = None
        self.current_frame = None
        self.available_cameras = self.list_available_cameras()
        self.selected_camera = tk.StringVar(value="0")
        self.setup_camera()
        
        # Ollama API settings
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "llava:7b"  # Default to a smaller vision model
        
        self.setup_ui()
        self.update_camera_feed()
        
    def list_available_cameras(self):
        """List all available cameras"""
        available_cameras = []
        for i in range(10):  # Check first 10 indexes
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_cameras.append(str(i))
                cap.release()
        return available_cameras if available_cameras else ["0"]  # Return at least default camera
    
    def setup_camera(self):
        """Initialize the webcam"""
        try:
            # Try to release any existing camera
            if self.cap:
                self.cap.release()
            
            # Initialize camera with a delay
            camera_index = int(self.selected_camera.get())
            self.cap = cv2.VideoCapture(camera_index)
            
            # Add a small delay to allow camera initialization
            time.sleep(1)
            
            if not self.cap.isOpened():
                messagebox.showerror("Camera Error", "Could not open camera. Please check camera permissions in System Preferences > Security & Privacy > Privacy > Camera")
                return False
            
            # Set camera resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Test if we can actually read a frame
            ret, frame = self.cap.read()
            if not ret or frame is None:
                messagebox.showerror("Camera Error", "Could not read from camera. Please check if another application is using the camera.")
                self.cap.release()
                return False
                
            return True
        except Exception as e:
            messagebox.showerror("Camera Error", f"Error initializing camera: {str(e)}\nPlease check camera permissions in System Preferences > Security & Privacy > Privacy > Camera")
            return False
    
    def setup_ui(self):
        """Create the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="📸 Poetry Camera", font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Camera selection
        camera_frame = ttk.Frame(main_frame)
        camera_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        ttk.Label(camera_frame, text="Select Camera:").pack(side=tk.LEFT, padx=(0, 5))
        camera_dropdown = ttk.Combobox(camera_frame, textvariable=self.selected_camera, 
                                     values=self.available_cameras, state="readonly", width=5)
        camera_dropdown.pack(side=tk.LEFT)
        camera_dropdown.bind('<<ComboboxSelected>>', lambda e: self.on_camera_change())
        
        # Camera feed
        self.camera_label = ttk.Label(main_frame, text="Camera feed will appear here")
        self.camera_label.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # Capture button
        self.capture_btn = ttk.Button(main_frame, text="📷 Capture & Generate Poem", 
                                     command=self.capture_and_generate, style="Accent.TButton")
        self.capture_btn.grid(row=3, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to capture", foreground="green")
        self.status_label.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Model selection
        model_frame = ttk.LabelFrame(main_frame, text="Model Settings", padding="5")
        model_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(model_frame, text="Model:").grid(row=0, column=0, sticky=tk.W)
        self.model_var = tk.StringVar(value=self.model_name)
        model_entry = ttk.Entry(model_frame, textvariable=self.model_var, width=30)
        model_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Poem display
        poem_frame = ttk.LabelFrame(main_frame, text="Generated Poem", padding="5")
        poem_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.poem_text = scrolledtext.ScrolledText(poem_frame, wrap=tk.WORD, width=60, height=15)
        self.poem_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Button frame for Save and Print buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=(0, 10))
        
        # Save button
        self.save_btn = ttk.Button(button_frame, text="💾 Save Poem", command=self.save_poem)
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.save_btn.configure(state='disabled')
        
        # Print button
        self.print_btn = ttk.Button(button_frame, text="🖨️ Print Poem", command=self.print_poem)
        self.print_btn.pack(side=tk.LEFT)
        self.print_btn.configure(state='disabled')
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)
        poem_frame.columnconfigure(0, weight=1)
        poem_frame.rowconfigure(0, weight=1)
        model_frame.columnconfigure(1, weight=1)
    
    def update_camera_feed(self):
        """Update the camera feed display"""
        try:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.current_frame = frame.copy()
                    
                    # Convert frame for display
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_resized = cv2.resize(frame_rgb, (400, 300))
                    
                    # Convert to PhotoImage
                    image = Image.fromarray(frame_resized)
                    photo = ImageTk.PhotoImage(image=image)
                    
                    # Update label
                    self.camera_label.configure(image=photo)
                    self.camera_label.image = photo  # Keep a reference
                else:
                    # If we can't read a frame, try to reinitialize the camera
                    self.camera_label.configure(text="Camera feed lost. Attempting to reconnect...")
                    if self.setup_camera():
                        self.camera_label.configure(text="Camera reconnected!")
                    else:
                        self.camera_label.configure(text="Camera connection failed")
        except Exception as e:
            self.camera_label.configure(text=f"Camera error: {str(e)}")
            print(f"Camera error: {str(e)}")
        
        # Schedule next update
        self.root.after(30, self.update_camera_feed)
    
    def capture_and_generate(self):
        """Capture image and generate poem"""
        if self.current_frame is None:
            messagebox.showerror("Error", "No camera feed available")
            return
        
        # Disable button and start progress
        self.capture_btn.configure(state='disabled')
        self.progress.start()
        self.update_status("Capturing image...", "blue")
        
        # Run in separate thread to prevent UI freezing
        thread = threading.Thread(target=self._generate_poem_thread)
        thread.daemon = True
        thread.start()
    
    def _generate_poem_thread(self):
        """Generate poem in separate thread"""
        try:
            # Save current frame
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = f"capture_{timestamp}.jpg"
            cv2.imwrite(image_path, self.current_frame)
            
            # Update status
            self.root.after(0, lambda: self.update_status("Analyzing image with AI...", "blue"))
            
            # Generate poem
            poem = self.generate_poem_with_ollama(image_path)
            
            # Update UI in main thread
            self.root.after(0, lambda: self._update_poem_result(poem, image_path))
            
        except Exception as e:
            error_msg = f"Error generating poem: {str(e)}"
            self.root.after(0, lambda: self._handle_error(error_msg))
    
    def generate_poem_with_ollama(self, image_path):
        """Generate poem using local Ollama model"""
        try:
            # Convert image to base64
            with open(image_path, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Prepare request
            prompt = """Look at this image and write a beautiful, creative short poem about what you see. 
            The poem should be 8 lines long, capture the mood and essence of the scene, 
            and have a thoughtful, artistic quality. Focus on the visual elements, emotions, 
            and atmosphere present in the image. """
            
            payload = {
                "model": self.model_var.get(),
                "prompt": prompt,
                "images": [img_base64],
                "stream": False
            }
            
            # Make request to Ollama
            response = requests.post(self.ollama_url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', 'Failed to generate poem')
            
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to Ollama. Make sure Ollama is running (try 'ollama serve' in terminal)"
        except requests.exceptions.Timeout:
            return "Error: Request timed out. The model might be taking too long to respond."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _update_poem_result(self, poem, image_path):
        """Update UI with poem result"""
        self.progress.stop()
        self.capture_btn.configure(state='normal')
        
        if poem.startswith("Error:"):
            self.update_status(poem, "red")
        else:
            self.update_status("Poem generated successfully!", "green")
            self.poem_text.delete(1.0, tk.END)
            
            # Add timestamp and poem
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.poem_text.insert(tk.END, f"Generated on {timestamp}\n")
            self.poem_text.insert(tk.END, f"Image: {image_path}\n")
            self.poem_text.insert(tk.END, "-" * 40 + "\n\n")
            self.poem_text.insert(tk.END, poem)
            self.poem_text.insert(tk.END, "\n\n" + "=" * 40 + "\n\n")
            
            # Enable save and print buttons
            self.save_btn.configure(state='normal')
            self.print_btn.configure(state='normal')
            
        # Clean up image file
        if os.path.exists(image_path):
            os.remove(image_path)
    
    def _handle_error(self, error_msg):
        """Handle error in main thread"""
        self.progress.stop()
        self.capture_btn.configure(state='normal')
        self.update_status(error_msg, "red")
        messagebox.showerror("Error", error_msg)
    
    def update_status(self, message, color="black"):
        """Update status label"""
        self.status_label.configure(text=message, foreground=color)
    
    def save_poem(self):
        """Save the current poem to a file"""
        try:
            poem_content = self.poem_text.get(1.0, tk.END).strip()
            if not poem_content:
                messagebox.showwarning("Warning", "No poem to save")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"poem_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(poem_content)
            
            messagebox.showinfo("Success", f"Poem saved as {filename}")
            self.update_status(f"Poem saved as {filename}", "green")
            
        except Exception as e:
            error_msg = f"Error saving poem: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self.update_status(error_msg, "red")
    
    def print_poem(self):
        """Print the current poem"""
        try:
            poem_content = self.poem_text.get(1.0, tk.END).strip()
            if not poem_content:
                messagebox.showwarning("Warning", "No poem to print")
                return
            
            # Create a temporary file for printing
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = f"temp_print_{timestamp}.txt"
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(poem_content)
            
            # Use the system's default printer
            if os.name == 'nt':  # Windows
                os.startfile(temp_file, 'print')
            elif os.name == 'posix':  # macOS and Linux
                if os.path.exists('/usr/bin/lpr'):  # Linux
                    os.system(f'lpr {temp_file}')
                else:  # macOS
                    os.system(f'open -a TextEdit {temp_file}')
            
            self.update_status("Poem sent to printer", "green")
            
            # Clean up temporary file after a delay
            self.root.after(5000, lambda: os.remove(temp_file) if os.path.exists(temp_file) else None)
            
        except Exception as e:
            error_msg = f"Error printing poem: {str(e)}"
            messagebox.showerror("Error", error_msg)
            self.update_status(error_msg, "red")
    
    def __del__(self):
        """Cleanup when app is destroyed"""
        if self.cap:
            self.cap.release()

    def on_camera_change(self):
        """Handle camera selection change"""
        if self.setup_camera():
            self.update_status("Camera changed successfully", "green")
        else:
            self.update_status("Failed to change camera", "red")

def main():
    """Main function to run the Poetry Camera app"""
    # Check if Ollama is available
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("Warning: Ollama might not be running. Start it with 'ollama serve'")
    except requests.exceptions.ConnectionError:
        print("Warning: Could not connect to Ollama. Make sure it's installed and running.")
        print("Install: https://ollama.ai/download")
        print("Start: ollama serve")
    
    # Create and run the app
    root = tk.Tk()
    app = PoetryCameraApp(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if hasattr(app, 'cap') and app.cap:
            app.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 