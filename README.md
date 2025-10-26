# Project: Cooperative Online Quiz System (ISEF01)

Welcome to the project repository! This is the source code for our prototype of a cooperative online quiz system for the IU Software Engineering project.

This document explains how to set up the project on your own computer for testing purposes or (later) to collaborate on the user manual.

## 1. Prerequisites

Before you begin, please ensure you have the following software installed on your system.

### Python (Version 3.10+):

Check: Open a terminal (CMD or PowerShell on Windows, "Terminal" on macOS) and type 
```shell
python --version or python3 --version.
```
Install: If it's missing, download it from python.org. IMPORTANT: When installing on Windows, check the box "Add Python to PATH".

### Git:

Check: In the terminal, type 
```shell
git --version.
```
Install: If it's missing, download it from git-scm.com.

## 2. Local Setup Instructions

Follow these steps to set up the project locally.

### Step 1: Clone the Project (Download Code)

Open your terminal, navigate to the folder where you store your projects (e.g., cd Documents/Projects), and clone the repository.

```shell
git clone git@gitlab.com:projekt-software-engineering/Quizduell.git
```
Change into the newly created project folder

```shell
cd iubh-quizprojekt
```

### Step 2: Virtual Environment (The "Project Bubble")

We will create an "isolated bubble" (Virtual Environment) so that the project's libraries do not conflict with your system.

 1. Create the virtual environment named 'venv'
    ```shell
    python -m venv .venv
    ```

2. Activate the environment (Choose the command for your system)

    Windows (CMD / PowerShell):
    ```shell
    .\venv\Scripts\activate
    ```
    macOS / Linux:
    ```shell
    source venv/bin/activate
    ```

(Your terminal prompt should now show (.venv) at the beginning.)

### Step 3: Install Dependencies (The "Shopping List")

Now we install all the packages the project needs (Django, HTMX, etc.) from the requirements.txt file.

#### Make sure (.venv) is active
```shell
pip install -r requirements.txt
```

### Step 4: Set Up the Database

This command creates the local db.sqlite3 database file and sets up all the tables Django needs (for users, questions, etc.).

#### Make sure (.venv) is active
```shell
python manage.py migrate
```

### Step 5: Create Your Own Admin User

To log into the admin panel (e.g., to approve questions), you need a superuser.

#### Make sure (.venv) is active
```shell
python manage.py createsuperuser
```

(Follow the prompts: Choose a username, an email (optional), and a password you can remember.)

## 3. Start the Project

Your setup is now complete! Here's how to start the local development server:

#### Make sure (.venv) is active
```shell
python manage.py runserver
```

Now, open your web browser and go to:

```
http://127.0.0.1:8000/
```
You should see the Django welcome page or (later) our project homepage.

#### Logging in as Admin

To see the admin backend (Feature 2.3), go to:
```
http://127.0.0.1:8000/admin/
```

Log in here with the username and password you created in Step 5.

## Code Formatting (For Developers)

We use black to keep our code style consistent. Before you check in code via git commit, please run the following command:

#### Make sure (venv) is active

```shell
black .
```