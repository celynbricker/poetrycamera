# Policy Lab Poetry Camera

A desktop application that captures images from your webcam and generates poems about what it sees using local Llama models through Ollama. Code based on the work done by bokito studio!

## Features

- Real-time webcam feed
- Capture images and generate poems
- Save generated poems to text files
- Customizable model selection

## Prerequisites

1. Python 3.8 or higher
2. Ollama installed and running (https://ollama.ai/download)
3. A webcam connected to your computer

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/poetry-camera.git
cd poetry-camera
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Install and start Ollama:
- Download and install Ollama from https://ollama.ai/download
- Start the Ollama server:
```bash
ollama serve
```

5. Pull the required model:
```bash
ollama pull llama2-vision
```

## Usage

1. Make sure Ollama is running (`ollama serve`)

2. Run the application:
```bash
python poetry_camera.py
```

3. The application window will open with your webcam feed

4. Click the "Capture & Generate Poem" button to take a photo and generate a poem

5. The generated poem will appear in the text area below

6. Click "Save Poem" to save the poem to a text file

## Troubleshooting

- If you get a camera error, make sure your webcam is properly connected and not in use by another application
- If you get an Ollama connection error, make sure Ollama is running (`ollama serve`)
- If the model is not found, make sure you've pulled the correct model (`ollama pull llama2-vision`)
