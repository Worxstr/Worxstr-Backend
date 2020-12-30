# Worxstr-Website
Web platform for Worxstr

## Installation

### Requirements
- [Python 3](https://www.python.org/)
- [Node.js](https://nodejs.org/en/)
- [Yarn](https://yarnpkg.com/)

1. Python virtual environment
    a. Create a new virtual environment
    `python -m venv env`

    b. Activate the environemnt
    `source env/bin/activate`

    c. Install packages
    `pip install -r requirements.txt`

2. Frontend
    a. Navigate to `/frontend`
    `cd frontend`

    b. Install packages
    `yarn install`

## Development
### Flask development server
1. Build the latest frontend code
    a. Navigate to `frontend`
    `cd frontend`

    b. Build the app
    `yarn build`

2. Run the server
    a. Navigate back to the root directory
    `cd ..`
    b. Run flask
    `FLASK_APP=main.py FLASK_ENV=development flask run`

### Vue development server
1. Navigate to `/frontend`
`cd frontend`

2. Run the dev server
`yarn serve`

## Production
Write this when we actually have something to deploy