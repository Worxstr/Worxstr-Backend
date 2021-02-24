# Worxstr-Backend
Web API for Worxstr

## Installation

### Requirements
- [Python 3](https://www.python.org/)
- [Node.js](https://nodejs.org/en/)
- [Yarn](https://yarnpkg.com/)

1. Python virtual environment
    1. Create a new virtual environment
    ```shell
    python -m venv env
    ```

    2. Activate the environemnt
    ```shell
    source env/bin/activate
    ```

    3. Install packages
    ```shell
    pip install -r requirements.txt
    ```

### Flask development server

1. Ensure that the vue server is still running on port 8080

2. Run the server
    1. Open a new terminal to the root directory
    2. Run flask
    ```shell
    FLASK_APP=main.py FLASK_ENV=development flask run
    ```
    
