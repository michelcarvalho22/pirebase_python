import pyrebase



def config_firebase():

    config = {
        "apiKey": ,
        "authDomain": ,
        "databaseURL":,
        "storageBucket": ,
        "serviceAccount":
    }

    firebase = pyrebase.initialize_app(config)
    database = firebase.database()

    return database