# 💰 Finance Tracker

A robust and user-friendly personal finance management application built with Python and Flask. Track your income, expenses, and visualize your financial health with ease.

## ✨ Features

- **📊 Interactive Dashboard**: Real-time overview of total income, expenses, and current balance.
- **💸 Transaction Management**: Easily add, edit, and delete income and expense transactions.
- **📎 File Attachments**: Upload receipts, invoices, or documents (PDF, Images) for each transaction.
- **🏷️ Category Management**: Organize transactions with customizable categories (Admin only).
- **📈 Visual Analytics**: View spending breakdowns by category and monthly trends.
- **📥 Data Export**: Export your transaction history to CSV for external analysis.
- **🔐 User Authentication**: Secure login and registration system with role-based access (User/Admin).
- **📱 Responsive Design**: Works seamlessly on desktop and mobile devices.

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Data Processing**: Pandas, NumPy

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd finance-tracker
    ```

2.  **Create a virtual environment**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    Create a `.env` file in the root directory:
    ```bash
    FLASK_SECRET_KEY=your_secret_key_here
    ADMIN_KEY=admin_secret_key
    USER_KEY=user_secret_key
    ```

### Running the Application

1.  **Start the server**
    ```bash
    python run.py
    ```

2.  **Access the application**
    Open your browser and navigate to: `http://localhost:8080`

## 📂 Project Structure

```
finance-tracker/
├── app/                 # Application package
│   ├── __init__.py      # App factory
│   ├── routes/          # Route blueprints
│   ├── models/          # Database models
│   ├── static/          # CSS, JS, Images
│   └── templates/       # HTML Templates
├── uploads/             # User uploaded files
├── instance/            # SQLite database location
├── run.py               # Entry point
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## 🍓 Deployment (Raspberry Pi)

This project includes configuration for deploying on a Raspberry Pi using Gunicorn and Systemd. See `deploy_pi.md` for detailed instructions.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).