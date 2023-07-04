import sqlite3
import threading
import time
from datetime import timedelta
from app import DATABASE_PATH
from app.utilities import check_password

sem = threading.Semaphore()

NAME_LIMIT: int = 50

class Database:
    db: 'Database' = None

    @classmethod
    def get_db(cls):
        if (Database.db is None):
            Database.db = Database(DATABASE_PATH)

        return Database.db

    def __init__(self, path: str):
        self.con = sqlite3.connect(path, check_same_thread=False)

        self.cur = self.con.cursor()

        self.setup_tables()

    def setup_tables(self):
        # Check if table Users exists.
        res = self.cur.execute("""
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' AND name='Users'
        """)

        result_list = res.fetchall()
        if (not result_list):
            self.cur.execute(f"""
            CREATE TABLE Users 
            (
                id integer primary key not null, 
                name char({NAME_LIMIT}) unique not null, 
                password text not null,
                lastAccessedTime unsigned integer(8) not null,
                loginAttemptCount unsigned integer not null,
                currentPublicKey text,

                isMuted integer not null,
                isAdmin integer not null
            )
            """)

        res = self.cur.execute("""
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' AND name='Friendship'
        """)

        result_list = res.fetchall()

        if (not result_list):
            self.cur.execute("""
            CREATE TABLE Friendship
            (
                User_1 integer,
                User_2 integer
            )
            """)

        res = self.cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name='Messages'
        """)

        result_list = res.fetchall()

        if (not result_list):
            self.cur.execute("""
            CREATE TABLE Messages
            (
                Sender_id integer,
                Receiver_id integer,
                Content text not null,
                Timestamp integer(8) not null
            )
            """)

        res = self.cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name='Posts'
        """)

        result_list = res.fetchall()

        if (not result_list):
            self.cur.execute("""
            CREATE TABLE Posts
            (
                id integer primary key not null,
                title char(250) not null,
                content text not null,
                creator_id integer not null,
                upvote integer not null,
                downvote integer not null,
                timestamp unsigned integer(8) not null
            )
            """)

        res = self.cur.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='Comments'
            """
        )

        result_list = res.fetchall()

        if (not result_list):
            self.cur.execute("""
            CREATE TABLE Comments
            (
                id integer primary key not null,
                content text not null,
                parent_id integer not null,
                commentor_id integer not null,
                timestamp unsigned integer(8) not null
            )
            """)

        res = self.cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name='Interaction'
        """)

        result_list = res.fetchall()

        if not (result_list):
            self.cur.execute("""
            CREATE TABLE Interaction
            (
                user_id integer not null,
                post_id integer not null,
                interaction integer not null
            )
            """)
        self.con.commit()
        return None

    def register_friendship(self, friendship: 'Friendship') -> None:
        sem.acquire()
        self.cur.execute("""
        INSERT INTO Friendship
        VALUES (?, ?)
        """, friendship.get_sql_format())
        self.con.commit()
        sem.release()
        return None
    
    def check_if_friend(self, id1: int, id2: int) -> bool:
        lower_id = id1 if (id1 < id2) else id2
        bigger_id = id1 + id2 - lower_id

        result = self.cur.execute("""
        SELECT * FROM Friendship
        WHERE User_1 = ? AND User_2 = ?
        """, (lower_id, bigger_id))

        result = result.fetchone()

        if (result == None):
            return False
        
        return True
    
    def get_all_friend(self, user_id: int) -> tuple:
        '''
        Get all friends of a particular user
        '''
        final_list = []

        result = self.cur.execute("""
        SELECT User_1 FROM Friendship 
        WHERE User_2 = ?
        """, (user_id, ))

        final_list.extend([x[0] for x in result.fetchall()])

        result = self.cur.execute("""
        SELECT User_2 FROM Friendship 
        WHERE User_1 = ?
        """, (user_id, ))

        final_list.extend([x[0] for x in result.fetchall()])

        for index, user_id in enumerate(final_list):
            final_list[index] = User.load_user(user_id)

        return final_list
    
    def delete_friendship(self, friendship: 'Friendship'):
        sem.acquire()

        self.cur.execute("""
        DELETE FROM Friendship
        WHERE 
        User_1 = ? AND User_2 = ?
        """, friendship.get_sql_format())

        self.con.commit()
        sem.release()

        return None

ONLINE_TIMEOUT = 300

class User:
    db = Database.get_db()
    
    def __init__(
            self, id: int, username: str, password: str, metadata: dict = None,
            is_admin: bool=False, is_muted: bool=False
        ):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin
        self.is_muted = is_muted

        if (metadata is not None):
            self.last_access = metadata["lastAccessedTime"]
            self.login_attempt_count = metadata["loginAttemptCount"]
            self.current_public_key = metadata["currentPublicKey"]

        else:
            self.last_access = 0
            self.login_attempt_count = 0
            self.current_public_key = None
        
    @classmethod
    def register_user(cls, user: 'User'):
        '''
        This should only be called AFTER sanitising the input.
        '''    
        sem.acquire()
        if (user.username == "Thomas" 
            or user.username == "Rason" 
            or user.username == "MomosuzuNene"):
            
            User.db.cur.execute("""
            INSERT INTO Users 
            (
                name, password, lastAccessedTime, loginAttemptCount, 
                currentPublicKey, isMuted, isAdmin
            )
            VALUES (?, ?, ?, ?, ?, 0, 1)
            """, user.get_sql_format())

        else:
            User.db.cur.execute("""
            INSERT INTO Users 
            (
                name, password, lastAccessedTime, loginAttemptCount, 
                currentPublicKey, isMuted, isAdmin
            )
            VALUES (?, ?, ?, ?, ?, 0, 0)
            """, user.get_sql_format())

        User.db.con.commit()
        sem.release()
        return None
    
    @classmethod
    def load_user(cls, id: int):
        if (id == None):
            return None
        sem.acquire()

        param = (id,)
        result = User.db.cur.execute("""
        SELECT id, name, password, 
        lastAccessedTime, loginAttemptCount, currentPublicKey,
        isAdmin, isMuted
        FROM Users 
        WHERE id = ?
        """, param)

        sem.release()

        result = result.fetchone()

        if (not result):
            return None
        
        metadata = {
            "lastAccessedTime": result[3],
            "loginAttemptCount": result[4],
            "currentPublicKey": result[5]
        }

        return User(
            result[0], result[1], result[2], metadata=metadata, 
            is_admin=result[6], is_muted=result[7]
        )
    
    @classmethod
    def get_user_by_name(cls, username: str):
        param = (username,)
        result = User.db.cur.execute("""
        SELECT 
        id, name, password, 
        lastAccessedTime, loginAttemptCount, currentPublicKey,
        isAdmin, isMuted
        FROM Users 
        WHERE name = ?
        """, param)

        result = result.fetchone()

        if (not result):
            return None

        metadata = {
            "lastAccessedTime": result[3],
            "loginAttemptCount": result[4],
            "currentPublicKey": result[5]
        }
        return User(
            result[0], result[1], result[2], metadata=metadata, 
            is_admin=result[6], is_muted=result[7]
        )
            
    def check_password(self, password: str):
        return check_password(self.password, password)
    
    def update_pubkey(self, pubkey: str):
        sem.acquire()
        User.db.cur.execute("""
        UPDATE Users
        SET currentPublicKey = ?
        WHERE id = ?
        """, (pubkey, self.id))
        User.db.con.commit()
        sem.release()

    def update_time(self):
        new_time = int(round(time.time()))
        
        sem.acquire()
        User.db.cur.execute("""
        UPDATE Users
        SET lastAccessedTime = ?
        WHERE id = ?
        """, (new_time, self.id))
        User.db.con.commit()
        sem.release()

    def increment_attempt(self):
        sem.acquire()
        User.db.cur.execute("""
        UPDATE Users
        SET loginAttemptCount = loginAttemptCount + 1
        WHERE id = ?
        """,(self.id,))
        User.db.con.commit()
        sem.release()

    def reset_attempt(self):
        sem.acquire()
        User.db.cur.execute("""
            UPDATE Users
            SET loginAttemptCount = 0
            WHERE id = ?
        """, (self.id,))
        User.db.con.commit()
        sem.release()
    
    def is_locked(self):
        return self.login_attempt_count >= 5

    def get_sql_format(self):
        return (
            self.username, 
            self.password,
            self.last_access,
            self.login_attempt_count,
            self.current_public_key
        )

    def add_friend(self, other: 'User'):
        friend_ship_obj = Friendship(self.id, other.id)
        User.db.register_friendship(friend_ship_obj)
        return
    
    def remove_friend(self, other: 'User'):
        friend_ship = Friendship(self.id, other.id)
        User.db.delete_friendship(friend_ship)
        return None

    def is_friend(self, other: 'User') -> bool:
        return User.db.check_if_friend(self.id, other.id)
    
    def get_all_friend(self):
        return User.db.get_all_friend(self.id)
    
    def get_last_accesed_time(self):
        result = User.db.cur.execute("""
        SELECT lastAccessedTime
        FROM Users
        WHERE id = ?
        """, (self.id,))

        result = result.fetchone()
        return result[0]       

    def get_pubkey(self):
        if (time.time() - User.get_last_accesed_time(self) >= ONLINE_TIMEOUT):
            User.update_pubkey(self, None)
            return None
        
        result = User.db.cur.execute("""
        SELECT currentPublicKey
        FROM Users
        WHERE id = ?
        """, (self.id,))

        result = result.fetchone()
        return result[0]
    
    def mute(self, mute):
        sem.acquire()
        User.db.cur.execute("""
            UPDATE Users
            SET isMuted = ?
            WHERE id = ?
        """, (mute, self.id))
        User.db.con.commit()
        sem.release()

    def upvote(self, post: 'Post'):
        sem.acquire()
        result = User.db.cur.execute("""
            SELECT interaction
            FROM Interaction
            WHERE user_id = ? AND post_id = ?
        """, (self.id, post.post_id)
        )

        result = result.fetchone()

        if (not result):
            User.db.cur.execute("""
            INSERT INTO Interaction
            (user_id, post_id, interaction)
            VALUES
            (?, ?, 1)
            """, (self.id, post.post_id)
            )

            User.db.cur.execute("""
            UPDATE Posts
            SET upvote = upvote + 1
            WHERE id = ?
            """, (post.post_id,)
            )
        
        elif (result[0] == 1):
            User.db.cur.execute("""
            UPDATE Interaction
            SET interaction = 0
            WHERE user_id = ? AND post_id = ?
            """, (self.id, post.post_id)
            )
            
            User.db.cur.execute("""
            UPDATE Posts
            SET upvote = upvote - 1
            WHERE id = ?
            """, (post.post_id,)
            )

        else:
            User.db.cur.execute("""
            UPDATE Interaction
            SET interaction = 1
            WHERE user_id = ? AND post_id = ?
            """, (self.id, post.post_id)
            )

            if (result[0] == -1):
                User.db.cur.execute("""
                UPDATE Posts
                SET upvote = upvote + 1, downvote = downvote - 1
                WHERE id = ?
                """, (post.post_id,)
                )

            else:
                User.db.cur.execute("""
                UPDATE Posts
                SET upvote = upvote + 1
                WHERE id = ?
                """, (post.post_id,)
                )
        User.db.con.commit()

        sem.release()
    
    def check_if_upvoted(self, post: 'Post') -> bool:
        sem.acquire()

        result = User.db.cur.execute("""
        SELECT interaction
        FROM Interaction
        WHERE user_id = ? AND post_id = ?
        """,
        (self.id, post.post_id)
        )

        result = result.fetchone()
        
        if (not result or result[0] != 1):
            sem.release()
            return False
        sem.release()
        return True

    def downvote(self, post: 'Post'):
        sem.acquire()
        result = User.db.cur.execute("""
            SELECT interaction
            FROM Interaction
            WHERE user_id = ? AND post_id = ?
        """, (self.id, post.post_id)
        )

        result = result.fetchone()

        if (not result):
            User.db.cur.execute("""
            INSERT INTO Interaction
            (user_id, post_id, interaction)
            VALUES
            (?, ?, -1)
            """, (self.id, post.post_id)
            )

            User.db.cur.execute("""
            UPDATE Posts
            SET downvote = downvote + 1
            WHERE id = ?
            """, (post.post_id,)
            )
        
        elif (result[0] == -1):
            User.db.cur.execute("""
            UPDATE Interaction
            SET interaction = 0
            WHERE user_id = ? AND post_id = ?
            """, (self.id, post.post_id)
            )
            
            User.db.cur.execute("""
            UPDATE Posts
            SET downvote = downvote - 1
            WHERE id = ?
            """, (post.post_id,)
            )

        else:
            User.db.cur.execute("""
            UPDATE Interaction
            SET interaction = -1
            WHERE user_id = ? AND post_id = ?
            """, (self.id, post.post_id)
            )

            if (result[0] == 1):
                User.db.cur.execute("""
                UPDATE Posts
                SET upvote = upvote - 1, downvote = downvote + 1
                WHERE id = ?
                """, (post.post_id,)
                )

            else:
                User.db.cur.execute("""
                UPDATE Posts
                SET downvote = downvote + 1
                WHERE id = ?
                """, (post.post_id,)
                )
        User.db.con.commit()

        sem.release()

    def check_if_downvoted(self, post: 'Post') -> bool:
        sem.acquire()

        result = User.db.cur.execute("""
        SELECT interaction
        FROM Interaction
        WHERE user_id = ? AND post_id = ?
        """,
        (self.id, post.post_id)
        )

        result = result.fetchone()

        if (not result or result[0] != -1):
            sem.release()
            return False
        sem.release()
        return True

    def delete(self):
        sem.acquire()

        User.db.cur.execute("""
        UPDATE Posts
        SET creator_id = -1
        WHERE creator_id = ?
        """, (self.id,))

        User.db.cur.execute("""
        DELETE FROM Messages
        WHERE Sender_id = ? OR Receiver_id = ?
        """, (self.id, self.id))

        User.db.cur.execute("""
        DELETE FROM Friendship
        WHERE User_1 = ? OR User_2 = ?
        """, (self.id, self.id))

        User.db.cur.execute("""
        DELETE FROM Users
        WHERE id = ?
        """, (self.id,))

        User.db.con.commit()

        sem.release()
        return
        
    def __repr__(self):
        return f"User {self.username}"

    def __eq__(self, other: 'User'):
        if (not isinstance(other, User)):
            return False

        if (self.id == other.id):
            return True
        
        return False
    
        
class Friendship:
    def __init__(self, user1_id: int, user2_id: int):
        
        if (user1_id > user2_id):
            self.lower_id = user2_id
            self.higher_id = user1_id

        elif (user1_id < user2_id):
            self.lower_id = user1_id
            self.higher_id = user2_id

        else:
            raise TypeError
        
    def get_sql_format(self):
        return (self.lower_id, self.higher_id)
    
class Message:
    def __init__(self, sender_id: int, receiver_id: int, content: str, timestamp: int):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.timestamp = timestamp

    @classmethod
    def wrap_into_json(cls, message_list: list):
        '''
        The JSON model of the data to be sent is

        {
        "event": "incoming",
        "count": number of messages,
        "messages":[
            {
                "content": content of the message,
                "timestamp": timestamp of the message
            }, ...
        ]
        }
        '''
        return {
            "event": "incoming",
            "count": len(message_list),
            "messages": message_list
        }
    
    @classmethod
    def find_all_msgs(cls, sender_id: int, receiver_id: int):
        db = Database.get_db()

        result = db.cur.execute("""
        SELECT Content, Timestamp 
        FROM Messages
        WHERE Sender_id = ? AND Receiver_id = ?
        ORDER BY Timestamp
        """, (sender_id, receiver_id))

        res = result.fetchall()

        res = [Message.get_json(message) for message in res]

        if (len(res) == 0):
            return Message.wrap_into_json([])
        
        earliest_time = res[0]["timestamp"]
        latest_time = res[len(res) - 1]["timestamp"]

        sem.acquire()
        db.cur.execute("""
        DELETE FROM Messages
        WHERE 
        Sender_id = ? AND Receiver_id = ? AND
        timestamp >= ? AND timestamp <= ?        
        """, (sender_id, receiver_id, earliest_time, latest_time))

        db.con.commit()
        sem.release()

        return Message.wrap_into_json(res)

    @classmethod
    def get_json(cls, tup: tuple):
        return {
            "content": tup[0],
            "timestamp": tup[1]
        }


    def save_to_db(self):
        db = Database.get_db()

        sem.acquire()
        db.cur.execute("""
        INSERT INTO Messages
        (Sender_id, Receiver_id, Content, Timestamp)
        VALUES (?,?,?,?)
        """, self.get_sql_format())
        db.con.commit()
        sem.release()

    def get_sql_format(self):
        return (self.sender_id, self.receiver_id, self.content, self.timestamp)


class ObjectWithTimestamp:
    def __init__(self, timestamp: int):
        self.timestamp = timestamp

    def get_time_passed(self) -> str:
        time_diff = int(round(time.time())) - self.timestamp

        time_diff = timedelta(seconds=time_diff)

        if (time_diff.days//7 > 0):
            return f"{time_diff.days//7} week(s)"
        elif (time_diff.days > 0):
            return f"{time_diff.days} day(s)"
        elif(time_diff.seconds//3600 > 0):
            return f"{time_diff.seconds//3600} hour(s)"
        elif (time_diff.seconds//60 > 0):
            return f"{time_diff.seconds//60} minute(s)"
        else:
            return f"{time_diff.seconds} second(s)"
        
        
        
    def get_accurate_time(self):
        struct_time_obj = time.localtime(self.timestamp)

        format = "%a, %Y-%m-%d %H:%M:%S"
        return time.strftime(format, struct_time_obj)


class Post(ObjectWithTimestamp):
    def __init__(
            self, post_id: int, title: str, content: str, 
            user: User, timestamp: int, upvote: int, downvote: int, comments: list=None
        ):
        self.title = title
        self.content = content
        self.creator = user
        self.post_id = post_id
        self.upvote = upvote
        self.downvote = downvote
        self.timestamp = timestamp
        self.comments = comments

    @classmethod
    def make_post(cls, title: str, content: str, creator_id: int):
        db = Database.get_db()

        sem.acquire()
        db.cur.execute("""
        INSERT INTO Posts
        (creator_id, title, content, timestamp, upvote, downvote)
        VALUES
        (?, ?, ?, ?, 0, 0)
        """,
        (creator_id, title, content, int(round(time.time())))
        )
        db.con.commit()
        result = db.cur.execute("""
        SELECT id 
        FROM Posts
        ORDER BY id 
        DESC
        LIMIT 1
        """)
        sem.release()

        return result.fetchone()[0]
    
    @classmethod
    def search_post(cls, id: int) -> "Post":
        db = Database.get_db()

        sem.acquire()
        result = db.cur.execute("""
        SELECT id, title, content, creator_id, timestamp, upvote, downvote
        FROM Posts
        WHERE id = ?
        """, (id, ))
        sem.release()

        result = result.fetchone()

        if (result == None):
            return None
        
        comments = db.cur.execute("""
        SELECT commentor_id, content, timestamp
        FROM Comments
        WHERE parent_id = ?
        ORDER BY id DESC
        """, (id,))

        comments = comments.fetchall()

        all_comments = [Comment(User.load_user(x[0]), x[1], x[2]) for x in comments]
        
        user = User.load_user(result[3])
        post = Post(result[0], result[1], result[2], user, result[4], result[5], result[6], comments=all_comments)

        return post
    
    @classmethod
    def get_all_posts(cls):
        db = Database.get_db()

        sem.acquire()
        result = db.cur.execute("""
        SELECT id, title, content, creator_id, timestamp, upvote, downvote
        FROM Posts
        ORDER BY id DESC
        """)
        sem.release()

        result = result.fetchall()

        list_of_posts = [Post(x[0], x[1], x[2], User.load_user(x[3]), x[4], x[5], x[6]) for x in result]

        return list_of_posts
    
    def delete(self) -> None:
        sem.acquire()

        db = Database.get_db()

        db.cur.execute("""
        DELETE FROM Posts
        WHERE id = ?
        """, (self.post_id,))

        db.cur.execute("""
        DELETE FROM Interaction
        WHERE post_id = ?
        """, (self.post_id,))

        db.cur.execute("""
        DELETE FROM Comments
        WHERE parent_id = ?
        """, (self.post_id,))

        db.con.commit()
        sem.release()
        return
    
    def add_comment(self, commentor: User, content: str):
        db = Database.get_db()

        sem.acquire()
        db.cur.execute("""
        INSERT INTO Comments
        (commentor_id, parent_id, content, timestamp)
        VALUES
        (?, ?, ?, ?)
        """, (commentor.id, self.post_id, content, int(round(time.time()))))

        db.con.commit()

        sem.release()

    def get_content(self):
        return self.content.split("\n")
    

class Comment(ObjectWithTimestamp):

    def __init__(self, commentor: User, content: str, timestamp: int):
        self.commentor = commentor
        self.content = content
        self.timestamp = timestamp

    def get_content(self):
        return self.content.split("\n")