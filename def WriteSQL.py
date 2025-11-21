def WriteSQL(_filename, _list):
    with open ("name_of_file.sql", "w") as file:
        query = "INSERT INTO questions (column1, column2, ...) BALUES (question[1], question[2]),"
        file.write(query +"/n")