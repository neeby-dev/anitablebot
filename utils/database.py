from config.config import DATABASE_URL

import psycopg2


class Database:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    def check_database(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS "users" (
                            "id" SERIAL, 
                            "user_id" INTEGER NOT NULL, 
                            "username" TEXT)""")
        self.cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS user_idx ON users (user_id)")
        self.cur.execute("""CREATE TABLE IF NOT EXISTS "admins" (
                            "id" SERIAL, 
                            "user_id" INTEGER NOT NULL, 
                            "username" TEXT)""")
        self.cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS admin_idx ON admins (user_id)")
        self.conn.commit()

    def get_users(self):
        self.cur.execute("SELECT * FROM users")
        users = self.cur.fetchall()
        return users

    def add_user(self, user_id, username):
        self.cur.execute("INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                         (user_id, username))
        self.conn.commit()

    def get_admins(self):
        self.cur.execute("SELECT * FROM admins")
        admins = self.cur.fetchall()
        return admins

    def check_admin(self, user_id):
        self.cur.execute(f"SELECT * FROM admins WHERE user_id = {user_id}")
        admin = self.cur.fetchone()
        return admin

    def add_admin(self, user_id, username):
        self.cur.execute(f"INSERT INTO admins (user_id, username) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                         (user_id, username))
        self.conn.commit()

    def delete_admin(self, user_id):
        self.cur.execute(f"DELETE FROM admins WHERE user_id = {user_id}")
        self.conn.commit()
