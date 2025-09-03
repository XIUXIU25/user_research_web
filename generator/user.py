from pymongo import MongoClient
from faker import Faker
import random

# MongoDB connection
client = MongoClient("mongodb://root:example@localhost:27017/")
db = client["user"]
collection = db["users"]

# Faker instance
fake = Faker()

# Possible values
sex_choices = ["Male", "Female", "Non-binary", "Other"]
occupations = [
    "Engineer", "Doctor", "Teacher", "Designer", "Manager",
    "Developer", "Nurse", "Artist", "Lawyer", "Student"
]

def generate_user():
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "age": random.randint(18, 70),
        "sex": random.choice(sex_choices),
        "occupation": random.choice(occupations),
        "location": fake.city(),
        "monthly_income": round(random.uniform(2000, 12000), 2)
    }

# Generate and insert N users
def seed_users(n=100):
    users = [generate_user() for _ in range(n)]
    collection.insert_many(users)
    print(f"Inserted {n} users into MongoDB.")

if __name__ == "__main__":
    seed_users(100)