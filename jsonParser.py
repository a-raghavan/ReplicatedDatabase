import json

class Person:
    def __init__(self, name, age, city):
        self.name = name
        self.age = age
        self.city = city

    def say_hello(self):
        print(f"Hello, my name is {self.name} and I'm from {self.city}.")

# create a Person object
person = Person("John", 30, "New York")

# convert the object to a JSON string
json_string = json.dumps(person.__dict__)

# print the JSON string
print(json_string)
