# Flask Data Cleaning Assistant

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask Version](https://img.shields.io/badge/flask-2.x-brightgreen.svg)](https://flask.palletsprojects.com/)
[![Pandas Version](https://img.shields.io/badge/pandas-1.x-blue.svg)](https://pandas.pydata.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An interactive web application designed to make the data cleaning process faster, more intuitive, and reproducible. Built with a Flask backend and a dynamic, real-time UI, this tool empowers data analysts to perform common data cleaning tasks, visualize their changes, and generate the corresponding Python code automatically.

 
*(**Action Required:** Replace this with a URL to a screenshot of your app's workspace)*

## The Problem It Solves

Data cleaning is a critical but often tedious part of any data analysis workflow. It typically involves repetitive coding tasks and requires a deep understanding of Pandas. This application abstracts away the boilerplate, allowing analysts to focus on the data and the logic of their cleaning pipeline. It provides a visual interface for operations while maintaining the rigor of a code-based workflow by generating reproducible Python scripts.

## Core Features

-   **Direct-to-Workspace Flow**: Upload a CSV or Excel file and get straight to work.
-   **Interactive Real-Time UI**: The entire workspace updates dynamically as you select different versions (checkpoints) of your data, with no page reloads.
-   **Intelligent Data Type Handling**: An intelligent "Change Data Types" operation that safely handles conversions from text-to-number (`NaN` problem) and float-to-integer (rounding problem) with clear user control.
-   **Comprehensive Cleaning Operations**:
    -   Drop unnecessary columns.
    -   Handle missing values (fill with mean, median, mode, or custom values).
    -   Convert data types with robust error handling.
    -   Explicitly convert floats to integers with user-defined rounding.
    -   Perform bulk string manipulations (change case, trim whitespace, find/replace).
-   **Checkpoint System**: After each operation, a new "checkpoint" is created. Users can view, download, or build upon any previous checkpoint in their workflow.
-   **Automatic Code Generation**: The application displays the exact Pandas code used for every operation. This code is cumulative, reproducible, and can be easily copied for use in notebooks or scripts.
-   **Professional Structure**: The application is built using a decentralized Flask application factory pattern, making it scalable and easy to maintain.

## Tech Stack

-   **Backend**: Flask
-   **Data Manipulation**: Pandas, NumPy
-   **Frontend**: HTML, Bootstrap 5, Vanilla JavaScript (Fetch API for AJAX)
-   **Server-side Sessions**: Flask-Session

## Getting Started

Follow these instructions to get a local copy up and running.

### Prerequisites

-   Python 3.8 or higher
-   pip (Python package installer)

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/YourUsername/your-repo-name.git
    cd your-repo-name
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```sh
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Execute the `run.py` script:**
    ```sh
    python run.py
    ```

2.  **Open your web browser** and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

## How to Use the App

1.  **Upload File**: On the homepage, select a CSV or Excel file and click "Upload and Go to Workspace".
2.  **Initial Profile**: You will land in the workspace. The right-hand panel shows a profile of your initially loaded data, including a preview and the data types inferred by Pandas (`df.info()`).
3.  **Perform Operations**:
    -   Use the accordion panels on the left to select an operation (e.g., "Change Data Types").
    -   Select the column(s) you want to modify.
    -   Choose the parameters for the operation (e.g., select `Int64` as the new type).
    -   If you are converting a float to an integer, a special rounding selection box will appear. You must choose a method to proceed.
4.  **Create Checkpoint**: Give your operation a descriptive name (optional) and click "Process & Create Checkpoint".
5.  **Review Results**: The page will refresh.
    -   The **Checkpoint History** will be updated.
    -   The **right-hand panel** will now show the profile, preview, and cumulative code for your newly created checkpoint.
6.  **Iterate or Download**:
    -   To perform another operation, simply select the latest checkpoint from the "Start From" dropdown and choose your next action.
    -   Click the "Download" button next to any checkpoint in the history to get a CSV of the data at that specific stage.
    -   Use the "Copy Code" button to grab the reproducible Python script.
  
## Contributing

Contributions are welcome! If you have suggestions for new features or improvements, please feel free to open an issue or submit a pull request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request
