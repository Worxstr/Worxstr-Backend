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
### Flask development server
1. Build the latest frontend code
    1. Navigate to `frontend`
    ```shell
    cd frontend
    ```

    2. Build the app
    ```shell
    yarn build
    ```

2. Run the server
    1. Navigate back to the root directory
    ```shell
    cd ..
    ```
    2. Run flask
    ```shell
    FLASK_APP=main.py FLASK_ENV=development flask run
    ```

### Vue development server
1. Navigate to `/frontend`
```shell
cd frontend
```

2. Run the dev server
```shell
yarn serve
```

## Production
Write this when we actually have something to deploy