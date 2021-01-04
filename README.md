# Worxstr-Website
Web platform for Worxstr

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

2. Frontend
    1. Navigate to `/frontend`
    ```shell
    cd frontend
    ```

    2. Install packages
    ```shell
    yarn install
    ```

## Development
### Vue development server
1. Navigate to `/frontend`
```shell
cd frontend
```

2. Run the dev server
```shell
yarn serve
```

### Flask development server

1. Ensure that the vue server is still running on port 8080

2. Run the server
    1. Open a new terminal to the root directory
    2. Run flask
    ```shell
    FLASK_APP=main.py FLASK_ENV=development flask run
    ```

## Production
Write this when we actually have something to deploy

1. Build the latest frontend code
    1. Navigate to `frontend`
    ```shell
    cd frontend
    ```

    2. Build the app
    ```shell
    yarn build
    ```
