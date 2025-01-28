# ProjectX

## Description

ProjectX

## Screenshot
> The screenshot of the app goes here vey soon.

## Live demo
[No live link yet]

## Built with

### Front-End
    - Bootstrap
    - HTML
    - CSS
    - Javascript
### Backend
    - Django
    - Python
    - PostgreSQL

## Running the Project Locally
### prerequisites
    - [Python]("#")
    - [pip]("#")
    
### Setup
1. First, clone the repository to your local machine:

```bash 
    git clone https://github.com/belmeetmule/projectx.git 
```

2. Get into the cloned directory
    ```bash
        cd projectx
    ```
3. Create vertual environemt
> For linux based systems
    ```bash
        pip3 -m venv px-venv
    ```
> For Windows based systems
    ```bash
        python -m venv px-venv
    ```

4. Run program under virtual environment:

> For linux based systems
```bash
    source px-venv/bin/activate
```

> For Windows based systems
```bash
    .\px-venv\Scripts\activate
```

5. Install the requirements:

```bash 
    pip install -r requirements.txt
```
6. Create the database:

```bash
    python manage.py migrate
```
7. Finally, run the development server:

```bash 
    python manage.py runserver
```
The project will be available at 127.0.0.1:8000.
