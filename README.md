# Privacy Guard AI

### Privacy-Preserving Multi-Agent System Analysis

**Privacy Guard AI** is a Python-based project designed to explore privacy preservation in multi-agent systems. It provides an interactive interface for analyzing datasets, applying privacy-related processing, and examining the relationship between coordination overhead and system performance.

## Key Features

* **Dataset Upload:** Upload supported datasets for analysis.
* **Privacy Processing:** Apply the privacy-processing techniques implemented in the backend.
* **Performance Analysis:** Examine system performance and coordination overhead.
* **Performance Comparison:** Compare experimental results using a performance matrix.
* **Interactive Dashboard:** Explore results through a Streamlit interface.
* **Data Visualization:** Present analytical results using interactive charts and tables.

## Technologies Used

* Python
* Streamlit
* Pandas
* Plotly
* Data Analysis and Visualization

## Project Structure

```text
Privacy-Guard-AI/
├── app.py
├── backend.py
├── requirements.txt
├── README.md
├── .gitignore
└── privacy_guard_sample_data_no_phone.csv
```

The sample CSV is optional. Include it only if you have created it and verified that it contains synthetic, non-sensitive data.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/Privacy-Guard-AI.git
cd Privacy-Guard-AI
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Run the application

```bash
python -m streamlit run app.py
```

The application will open in your browser.

## Deployment

The application can be deployed using Streamlit Community Cloud after the source code and dependency files have been uploaded to GitHub.

Deployment guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

## Research Objective

The project explores the relationship between privacy-preserving data processing, coordination overhead, and performance in multi-agent systems.

Experimental conclusions should be based on measured results from the implemented system rather than assumed improvements.

## Disclaimer

Use synthetic or appropriately authorized datasets for testing. Do not upload confidential or personally identifiable information to a public repository or an unapproved deployment environment.

## Author

Developed as an academic project exploring privacy preservation, multi-agent systems, and performance analysis.
