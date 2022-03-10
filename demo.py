# Using Datatables in server-side configuration, with data coming from a join, and providing live search
# for each column. 
# 
# Steven Cogswell March 2022
# 
# Expanded from concepts on https://blog.miguelgrinberg.com/post/beautiful-interactive-tables-for-your-flask-templates
import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Owner(db.Model):
    """
    The owner class, each Pet has to have an owner.
    Note there are fields that are set but not displayed in the table
    as a demonstration.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    age = db.Column(db.Integer, index=True)
    address = db.Column(db.String(256))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    pets = db.relationship('Pet', backref='owner', lazy='dynamic')

    def to_dict(self, prefix=""):
        """
        The dict we generate from the /api/data endpoint returns data in a dict for all 
        columns we want to show in the table.  But there are fields for Owner.name and Pet.name.
        Because we have fields that are the same column name in both Owner and Pet models, 
        but we want those to_dict()'s returned to have unique names, but also we don't want
        to change an entire class model definition in order to accomodate another, we provide 
        a 'prefix' we can se when asking for the to_dict().  This way we owner will normally
        respond with 'name' and 'email' in the dict, but with prefix set to 'owner_' they will
        generate as 'owner_name' and 'owner_email'
        """
        return {
            prefix+'name': self.name,
            prefix+'email': self.email,
        }

class Pet(db.Model):
    """
    The table display will be all about pets, listing their owners via relationship
    """
    id = db.Column(db.Integer, primary_key=True)
    id_owner = db.Column(db.Integer, db.ForeignKey("owner.id"))
    name = db.Column(db.String(64), index=True)
    type = db.Column(db.String(64), index=True)
    age = db.Column(db.Integer, index=True)

    def to_dict(self,prefix=""):
        """
        See Owner model for the purpose of the "prefix" option. 
        Note we could have made this entire project simpler by just 
        providing a dict directly from the relationship: 

        return {
            'name':self.name,
            'type':self.type,
            'age':self.age,
            'owner_name':self.owner.age,
            'owner_email':self.owner.email
        }

        But this demo is to illustrate how to do this with a Join, which might be 
        two tables you don't want to write out a huge to_dict() function for.  
        """
        return {
            prefix+'name':self.name,
            prefix+'type':self.type,
            prefix+'age':self.age,
        }

# Housekeeping, create the database if it doesn't exist, check for records. You 
# need records to show tables, people.   
db.create_all()
if (Pet.query.count() > 0):
    print("Database has {} records in it, good".format(Pet.query.count()))
else:
    print("Database has no records.  Use 'python create_fake_users.py' before viewing tables")
if 'FLASK_ENV' not in os.environ:
    print("Remember FLASK_ENV=development if you want debugging")

@app.route('/')
def index():
    return render_template('table-view.html', title='Server-Driven Table with Join')


@app.route('/api/data')
def data():
    """
    API endpoint where datatables' javascript will get the data for the displayed table from. 
    """
    # We want a join so we can show data about Pets' owners in the same table.  
    query = Pet.query.join(Owner)
    #print("args are [{}]".format(request.args))

    # Handle the global search filter
    # because it's a join we can mix models in the query 
    search = request.args.get('search[value]')
    if search:
        query = query.filter(db.or_(
            Owner.name.like(f'%{search}%'),
            Owner.email.like(f'%{search}%'),
            Pet.name.like(f'%{search}%'),
            Pet.type.like(f'%{search}%')
        ))
    total_filtered = query.count()

    # Handle the individual column search filter, the ones that show at the bottom 
    # of each column.  This is in *addition* to the global search fiter above.  
    #
    # We will iterate through this in a similar fashion to how Miguel Grinberg 
    # handled the sort.  
    i=0
    column_query=[]   # Blank query to start
    while True:
        # If you're searching on a column, there be a non-blank value for the argument e.g. 'columns[3][search][value]'
        col_search = request.args.get(f'columns[{i}][search][value]')
        if col_search is None:  # we've gone through them all
            break  # escape the while loop
        # If the col_search is not blank, we're going to do a search in that column 
        if col_search != "":  
            #print(f"column search: col_search for column {i} search is [{col_search}]")
            # Get the name of the column we need in the datatables format 
            col_name = request.args.get(f'columns[{i}][data]')
            #print(f"column search: desired col_name is {col_name}")
            # Like sort, we have a 'blacklist' of things you can't search for prohibited 
            # from the start.  This is here to be feature complete with Miguel Grinberg's 
            # 'sort' blacklist. 
            if col_name not in ['pet_name', 'pet_age', 'pet_type', 'owner_name', 'owner_email']:
                col_name = 'pet_name'
            #print("column search: actual col_name is {}".format(col_name))
            
            # Here's why we put prefixes on the to_dict() functions.  We can then tell from the column
            # names whether the column is from the Owner model or the Pet model.  
            #
            # To actually query the Pet object we need to strip the prefix off the front 
            # so that the name of the sqlalchemy model is correct. 
            # i.e - sqlalchemy model is Pet.name, the to_dict(prefix="pet_") will return 
            # as pet_name which we can insert into the datatables table and tell that the column
            # is pet_name and not confused with owner_name (for which we do the same prefix idea)
            if col_name.startswith("pet_"):
                col_name = col_name.split("pet_",1)[1]  # strip off the prefix
                col = getattr(Pet, col_name)    # This let's us call e.g. "Pet.name" as the object while only known "name" as a string.  
                                                # since you can't do "Pet.col_name" directly, as model Pet has no field called "col_name"
                                                # it's like being able to reference the model as "Pet.str(col_name)"
                #print("column search: name for Pet getattr is {}".format(col_name))

            # Because Pet and Owner are two different models in the Join for the query, we have to 
            # reference each of them separately.  Same technique as handling "pet_" above.      
            if col_name.startswith("owner_"):
                col_name = col_name.split("owner_",1)[1]
                col = getattr(Owner, col_name)
                #print("column search: name for Owner getattr is {}".format(col_name))

            # You can append query filters, apparently.
            # remember col is equivalent of an actual column e.g. "Pet.name"
            # so this is query for "Pet.name.like(f'%{col_search}%')" or maybe "Owner.email.like(f'%{col_search}%')"
            col=col.like(f'%{col_search}%')
            column_query.append(col)
        i+=1   # loop to the next column in the table. 
    if column_query:
        # rint(f"column search: column_query is [{column_query}]")
        # Like with the sort functions below, we add the query to the global query above
        # and generate a new total_filtered since we might have fewer records than before. 
        query=query.filter(*column_query)
        total_filtered = query.count()
    else:  
        pass
        #print("No column search terms")

    # sorting
    # This is the sort, almost verbatim from https://blog.miguelgrinberg.com/post/beautiful-interactive-tables-for-your-flask-templates
    # Except we deal with the prefixes on "pet_" and "owner_" fields from the table like we did above in the column searches.  
    # Because it's a join we can do both Pet and Owner models.  
    order = []
    i = 0
    while True:
        col_index = request.args.get(f'order[{i}][column]')
        if col_index is None:
            break
        col_name = request.args.get(f'columns[{col_index}][data]')
        #print("sort: desired col_name is {}".format(col_name))
        if col_name not in ['pet_name', 'pet_age', 'pet_type', 'owner_name', 'owner_email']:
            col_name = 'pet_name'
        #print("sort: actual col_name is {}".format(col_name))
        descending = request.args.get(f'order[{i}][dir]') == 'desc'

        if col_name.startswith("pet_"):
            col_name = col_name.split("pet_",1)[1]
            col = getattr(Pet, col_name)
            #print("sort: name for Pet getattr is {}".format(col_name))
            
        if col_name.startswith("owner_"):
            col_name = col_name.split("owner_",1)[1]
            col = getattr(Owner, col_name)
            #print("sort: name for Owner getattr is {}".format(col_name))

        #print("sort: col is {}".format(col))
        if descending:
            col = col.desc()
        order.append(col)
        i += 1
    if order:
        query = query.order_by(*order)
        #print("sort: query is {}".format(str(query)))

    # pagination
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    query = query.offset(start).limit(length)

    # Because of the join, we can't do a simple dict generation
    # like the original version of this like:
    #  'data': [pet.to_dict() for pet in query] 
    #
    # We could probably find an even more compact way of generating to_dict()'s 
    # from both models and making them into one combined dict but this way 
    # is supposed to be simple to look at and understand 
    query_data = []
    for pet in query:
        pet_data = pet.to_dict(prefix="pet_")
        owner_data = pet.owner.to_dict(prefix="owner_")
        both_data = merge_dicts(pet_data,owner_data)  # merge_dicts is down below in this file 
        query_data.append(both_data)

    #narf = [pet.to_dict() for pet in query]
    #print("narf: {}".format(narf))
    #print("query_data: {}".format(query_data))

    # The response send to datatable's ajax function. 
    return {
        'data': query_data,
        'recordsFiltered': total_filtered,
        'recordsTotal': Pet.query.count(),
        'draw': request.args.get('draw', type=int),
    }


def merge_dicts(*dict_args):
    """
    https://stackoverflow.com/questions/38987/how-do-i-merge-two-dictionaries-in-a-single-expression-take-union-of-dictionari
    Given any number of dictionaries, shallow copy and merge into a new dict,
    precedence goes to key-value pairs in latter dictionaries.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

@app.route("/getinfo/<email>", methods=['GET','POST'])
def getinfo(email):
    """
    This is just a simple endpoint for demonstrating destination of the action href links
    in the first column of every table
    """
    owner = Owner.query.filter_by(email=email).first_or_404()
    return render_template("info.html", owner=owner, title=f"Information for {email}")

if __name__ == '__main__':
    app.run()
