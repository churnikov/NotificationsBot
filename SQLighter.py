import sqlite3

class SQLighter:


    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()


    def add_event(self, data):
        """
        add new event to EVENTS table.
        :data: -- (tuple) -- tuple of 2 elements:
                                - id of event
                                - type of sourse:
                                    - 1 -- vk, matobes
                                    - 2 -- vk, mmspbu
                                    - 3 -- website, mathmech
                                    - 4 -- website, mathmech announcements
        :returns:
            (bool) -- added or not data in database
        """
        with self.connection:
            if not self.exists(data):
                self.cursor.execute('INSERT INTO EVENTS VALUES (NULL, ?, ?)', data)
                return True
            else:
                return False


    def exists(self, data):
        self.cursor.execute('SELECT ID FROM EVENTS WHERE ID_EVENT = ? AND SOURCE_TYPE = ?', data)
        result = self.cursor.fetchone()
        if result is None:
            return False
        else:
            return True


    def close(self):
        """Close connection with DB"""
        self.connection.close()
