class ParseQuery:
    def __init__(self, className):
        self.className = className
        self.filters = {}
        self.limit_value = None
        self.skip_value = None
        self.aggregation_value = None

    def equalTo(self, key, value):
        self.filters[key] = value

    def notEqualTo(self, key, value):
        self.filters[key] = {"$ne": value}

    def lessThan(self, key, value):
        self.filters[key] = {"$lt": value}

    def greaterThan(self, key, value):
        self.filters[key] = {"$gt": value}

    def limit(self, value):
        self.limit_value = value

    def skip(self, value):
        self.skip_value = value

    # let's add a function that allows for mongodb aggregation
    def aggregate(self, value):
        self.aggregation_value = value
    
    def include(self, value):
        self.filters["include"] = value
    

    def find(self):
        # Here you would typically make a request to the Parse server with the filters
        # For simplicity, we'll just print the filters
        print(f"Filters: {self.filters}")
        if self.limit_value is not None:
            print(f"Limit: {self.limit_value}")
        if self.skip_value is not None:
            print(f"Skip: {self.skip_value}")

if __name__ == "__main__":
    query = ParseQuery('MyClass')
    query.equalTo('key1', 'value1')
    query.notEqualTo('key2', 'value2')
    query.limit(10)
    query.skip(20)
    query.find()
