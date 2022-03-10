import random
import sys
from unicodedata import numeric
from faker import Faker
from demo import db, Owner, Pet


def create_fake_users(n):
    """
    Generate fake users.
    Expanded from https://blog.miguelgrinberg.com/post/beautiful-interactive-tables-for-your-flask-templates
    """
    faker = Faker()
    number_of_pets = 0
    for i in range(n):
        # Add an owner, since pets have to have owners
        owner = Owner(name=faker.name(),
                    age=random.randint(20, 80),
                    address=faker.address().replace('\n', ', '),
                    phone=faker.phone_number(),
                    email=faker.email())
        db.session.add(owner)
        db.session.commit()

        # for each owner add a random number of pets  
        for i in range(random.randint(1,5)):
            pet = Pet(name=faker.first_name(),
                        type = random.choice(['dog','cat','fish','lizard','paramecium']),
                        age = random.randint(1,5),
                        id_owner = owner.id)
            number_of_pets = number_of_pets+1
            db.session.add(pet)
            db.session.commit()

    print(f'Added {n} fake users with {number_of_pets} pets to the database.')


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print('Pass the number of users you want to create as an argument.')
        sys.exit(1)
    create_fake_users(int(sys.argv[1]))
