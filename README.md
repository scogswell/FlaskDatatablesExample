# README

A "complete" demo program example of using Flask with datatables https://datatables.net/, where the table is made from a join of two flask-sqlalchemy models and the data supplied to the table via ajax.  The table has a global search and can search on each of the columns individually.  

This is expanded on from a very good tutorial by Miguel Grinberg https://blog.miguelgrinberg.com/post/beautiful-interactive-tables-for-your-flask-templates . Check that tutorial for more fundamental usage of datatables.

This uses packages for `Flask`, `Flask-sqlalchemy`, `Faker` (to generate data) and their dependencies.  

This uses bootstrap5 for display, as simple css and js includes. See `base.html`. jQuery is required for databables and is included as part of Bootstrap.  https://getbootstrap.com/

There are lots of commented out print() statements if you want excruciating detail of the internals. 

## How to use this

1. Make a virtual environment:

        python -m venv .venv
        . .venv.bin/activate

2. Install requirements automatically (flask, flask-wtf, email-validator):

        python -m pip install --upgrade pip 
        pip install -r requirements.txt

3. Set development server for demo if desired:

        export FLASK_ENV=development

4. Create and add 1000 records of fake data to the database for testing

        python ./create_fake_users.py 1000 

5. Run!

        python ./demo.py

6. Navigate in web browser to displayed url http://127.0.0.1:5000/

