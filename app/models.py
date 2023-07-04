from flask import flash, session, request
import json

from app.Database import Database, User, Message, Post
from app.view import View
from app.utilities import encrypt_plain_password

_current_user = None

JSON = 3
URL = 2
TEMPLATE = 1
REDIRECT = 0


def _update_cur_user():
    session["user"] = session["user"] if ("user" in session) else None
    global _current_user
    _current_user = User.load_user(session["user"])
    return

def check_user(func: callable):
    def returned_function(*args, **kwargs):
        _update_cur_user()
        if (_current_user is not None):
            _current_user.update_time()
        return func(*args, **kwargs)

    return returned_function

@check_user
def get_index(first_login):
    view_obj = View(cur_user=_current_user, first_login=first_login, posts=Post.get_all_posts())
    return (TEMPLATE, view_obj.index_page())

@check_user
def get_faq():
    view_obj = View(cur_user=_current_user)
    return (TEMPLATE, view_obj.faq_page())

@check_user
def get_forums():
    view_obj = View(cur_user=_current_user, posts=Post.get_all_posts())
    return (TEMPLATE, view_obj.forum_page())

@check_user
def get_login():
    if (_current_user is not None):
        return (REDIRECT, "index")

    if (request.method == "POST"):
        data = request.get_json()

        user = User.get_user_by_name(data["username"])

        if (user is None):
            flash("Invalid username or password.")
            return (URL, "login")
        
        if (user.is_locked()):
            return (URL, "locked_account")

        if (not user.check_password(data["password"])):
            flash("Invalid username or password.")
            user.increment_attempt()
            return (URL, "login")
        
        session["user"] = user.id
        user.update_pubkey(data["public_key"])
        user.update_time()
        user.reset_attempt()

        return (URL, "index")

    view_obj = View(sign_up=False)

    return (TEMPLATE, view_obj.login_page())

@check_user
def log_user_out():
    global _current_user
    if (_current_user is None):
        (REDIRECT, "index")

    if (_current_user is not None):
        _current_user.update_pubkey(None)

    session["user"] = None
    _current_user = None

    return (REDIRECT, "index")


@check_user
def sign_user_up():
    if (_current_user is not None):
        return (REDIRECT, "index")

    if (request.method == "POST"):
        data = request.get_json()

        user = User.get_user_by_name(data["username"])

        if (user is not None):
            flash(
                "Username was already taken, please use a different username."
            )

            return (URL, "sign_up")
        
        User.register_user(
            User(
            0,
            data["username"],
            encrypt_plain_password(data["password"])
            )
        )
        flash("Signed up successfully, please log in")
        return (URL, "login")

    view_obj = View(sign_up=True)

    return (TEMPLATE, view_obj.login_page())

    # form = LoginForm()

    # if (form.validate_on_submit()):
    #     user = db.get_user_by_name(form.username.data)

    #     if (user is not None):
    #         flash("Username was already taken, please use a different username.")

    #         return (REDIRECT, "sign_up")
        
    #     db.register_user(
    #         User(0, 
    #             form.username.data, 
    #             encrypt_plain_password(form.password.data))
    #     )
    #     flash("Signed up successfully, please log in")
    #     return (REDIRECT, "login")

    # view_obj = View(sign_up=True, form=form)

@check_user
def get_user_pf_page(user_id: int):
    other_user = User.load_user(user_id)

    if (not other_user):
        # Can return a 404 not found here.
        flash("This user does not exist")
        return (REDIRECT, "index")
    
    friends = None
    sameUser = False
    logged_in = False
    is_friend = False

    view_obj = None

    if (not _current_user):
        view_obj = View(
            cur_user=_current_user, 
            friends=friends,
            sameUser=sameUser,
            user=other_user,
            logged_in = logged_in,
            is_friend=is_friend
        )

        return (TEMPLATE, view_obj.profile_page())
    
    logged_in = True
    if (_current_user == other_user):
        sameUser = True
        friends = _current_user.get_all_friend()
        view_obj = View(
            cur_user=_current_user, 
            friends=friends,
            sameUser=sameUser,
            user=other_user,
            logged_in = logged_in,
            is_friend=is_friend
        )

        return (TEMPLATE, view_obj.profile_page())
    
    is_friend = _current_user.is_friend(other_user)

    view_obj = View(
        cur_user=_current_user, 
        friends=None,
        sameUser=sameUser,
        user=other_user,
        logged_in = logged_in,
        is_friend=is_friend
    )

    return (TEMPLATE, view_obj.profile_page())


@check_user
def search_user(username: str = None):

    if (not _current_user):
        return (REDIRECT, "index", {})
    
    if (username is None):
        view_obj = View(cur_user=_current_user)
        return (TEMPLATE, view_obj.search())
    
    user = User.get_user_by_name(username)

    if (not user):
        flash("This user does not exist")
        return (REDIRECT, "search", {})
    
    return (REDIRECT, "get_profile_page", {"user_id": user.id})
    
@check_user
def add_friend_logic(user_id: int):
    other_user = User.load_user(user_id)

    if (not _current_user):
        flash("Please log in to access this feature")
        return (URL, "login", {})

    if (not other_user):
        flash("This person does not exist")
        return (URL, "search", {})
    
    if (_current_user == other_user):
        flash("You cannot add friend with yourself, please go out and make some real friends :)")
        return (URL, "search", {})
    
    if (_current_user.is_friend(other_user)):
        flash("You guys are already friends, cannot add another time.")
        return (URL, "get_profile_page", {"user_id": other_user.id})
    
    _current_user.add_friend(other_user)
    flash("Friend added successfully")
    return (URL, "get_profile_page", {"user_id": other_user.id})

@check_user
def remove_friend_logic(user_id: int):
    other_user = User.load_user(user_id)

    if (_current_user is None):
        flash("Please log in to access this feature")
        return (URL, "login", {})

    if (not other_user):
        flash("This person does not exist")
        return (URL, "search", {})
    
    if (_current_user == other_user):
        flash("You cannot unfriend yourself")
        return (URL, "search", {})
    
    if (not _current_user.is_friend(other_user)):
        flash("You cannot unfriend someone who is not your friend to begin with")
        return (URL, "get_profile_page", {"user_id": other_user.id})
    
    _current_user.remove_friend(other_user)
    flash("Friend removed successfully")
    return (URL, "get_profile_page", {"user_id": other_user.id})

@check_user
def chat_page_logic(receiver_id: int, sender_id: int):
    if (_current_user is None):
        flash("Please log in to access this feature")
        return (REDIRECT, "index", {})
    
    if (receiver_id == sender_id):
        flash("We would prefer you to not send a message to yourself.")
        return (REDIRECT, "get_profile_page", {"user_id": sender_id})
    
    sender = User.load_user(sender_id)

    if (sender != _current_user):
        flash("You are not supposed to access this url.")
        return(REDIRECT, "get_profile_page", {"user_id": _current_user.id})
    
    receiver = User.load_user(receiver_id)

    if (receiver is None):
        flash("This user does not exist, please recheck your url.")
        return(REDIRECT, "get_profile_page", {"user_id": _current_user.id})
    
    if (not receiver.is_friend(_current_user)):
        flash("You cannot message anyone that is not your friend, please add them as friend first.")
        return(REDIRECT, "get_profile_page", {"user_id": receiver_id})
    
    public_key: str = receiver.get_pubkey()
    
    if (public_key is None):
        flash(f"User {receiver.username} is not currently online :( please try again later")
        return (REDIRECT, "get_profile_page", {"user_id": receiver_id})
    
    view_obj = View(cur_user = _current_user, other_user = receiver, pubKey = public_key)

    return (TEMPLATE, view_obj.messages_page())

# If the request is a get request, then the sender is the receiver and the 
# receiver is actually the sender, I could have done string manipulation in JS 
# to reverse them but I don't really want to :/


@check_user
def message_logic(data: str, receiver_id: int, sender_id: int):

    if (_current_user is None):
        flash("Please log in to access this service")
        return {"error": "login required"}
    
    sender = User.load_user(sender_id)
    receiver = User.load_user(receiver_id)

    if (_current_user != sender):
            flash("Error")
            return {"error": "error"}
        
    if (receiver is None):
        flash("Error")
        return {"error": "error"}
    
    if (not _current_user.is_friend(receiver)):
            flash("Error")
            return {"error": "error"}
    
    data = json.loads(data)
    
    if (data["method"] == "POST"):        
        message_sent = Message(sender_id, receiver_id, data["content"], data["timestamp"])

        message_sent.save_to_db()

        return """{"event": "outgoing", "status": "ok"}"""
    elif (data["method"] == "ALERT"):
        print("The Server is compromised")
    
    # The roles are reversed
    messages = Message.find_all_msgs(
        sender_id=receiver_id, receiver_id=sender_id
    )
    
    return json.dumps(messages)

@check_user
def reset_user_timeout():

    if (_current_user is None):
        return (REDIRECT, "index", {})
    
    _current_user.update_time()

    return (REDIRECT, "index", {})

@check_user
def not_found():
    view_obj = View(cur_user=_current_user)
    return (TEMPLATE, view_obj.not_found_page())

@check_user
def mute_user_logic(user_id: int):
    if (_current_user == None):
        flash("You do not have access to this feature")
        return (REDIRECT, "index", {})
    
    if (not _current_user.is_admin):
        flash("You do not have access to this feature")
        return (REDIRECT, "index", {})
    
    target_user = User.load_user(user_id)

    if (target_user == None):
        flash("User does not exist")
        return (REDIRECT, "index", {})
    
    if (target_user.is_admin):
        flash("Cannot mute a fellow admin :)")
        return (REDIRECT, "get_profile_page", {"user_id": target_user.id})
    
    if (target_user.is_muted):
        flash("Cannot mute twice")
        return (REDIRECT, "get_profile_page", {"user_id": target_user.id})
    
    target_user.mute()
    return (REDIRECT, "get_profile_page", {"user_id": target_user.id})

@check_user
def mute_user_logic(user_id: int):
    if (_current_user == None):
        flash("You do not have access to this feature")
        return (REDIRECT, "index", {})
    
    if (not _current_user.is_admin):
        flash("You do not have access to this feature")
        return (REDIRECT, "index", {})
    
    target_user = User.load_user(user_id)

    if (target_user == None):
        flash("User does not exist")
        return (REDIRECT, "index", {})
    
    if (target_user.is_admin):
        flash("Cannot mute a fellow admin :)")
        return (REDIRECT, "get_profile_page", {"user_id": target_user.id})
    
    if (target_user.is_muted):
        flash("Cannot mute twice")
        return (REDIRECT, "get_profile_page", {"user_id": target_user.id})
    
    target_user.mute(1)
    flash(f"Muted user {target_user.username} successfully")
    return (REDIRECT, "get_profile_page", {"user_id": target_user.id})

@check_user
def unmute_user_logic(user_id: int):
    if (_current_user == None):
        flash("You do not have access to this feature")
        return (REDIRECT, "index", {})
    
    if (not _current_user.is_admin):
        flash("You do not have access to this feature")
        return (REDIRECT, "index", {})
    
    target_user = User.load_user(user_id)

    if (target_user == None):
        flash("User does not exist")
        return (REDIRECT, "index", {})
    
    if (target_user.is_admin):
        flash("Error")
        return (REDIRECT, "get_profile_page", {"user_id": target_user.id})
    
    if (not target_user.is_muted):
        flash("Cannot unmute someone who is not muted")
        return (REDIRECT, "get_profile_page", {"user_id": target_user.id})
    
    target_user.mute(0)
    flash(f"Unmuted user {target_user.username} successfully")
    return (REDIRECT, "get_profile_page", {"user_id": target_user.id})

@check_user
def get_newpost():
    if (_current_user == None):
        flash("Please login")
        return (REDIRECT, "index", {})
    if (request.method == "GET"):
        view_obj = View(cur_user=_current_user)
        return (TEMPLATE, view_obj.new_post())
    
    if (request.method == "POST"):
        if (_current_user.is_muted):
            return (JSON, {"isMuted": 1})
        
        else:
            data = request.json

            new_post_id = Post.make_post(data["title"], data["content"], _current_user.id)

            return (URL, {"isMuted": 0, "URL": "see_post", "params": {"id": new_post_id}})
        

@check_user
def see_post_logic(id: int):
    if (_current_user == None):
        flash("Please login to access this feature")
        return (REDIRECT, "index", {})
    
    post = Post.search_post(id)

    if (post == None):
        flash("This post does not exist")
        return (REDIRECT, "index", {})
    
    view_obj = View(post=post, cur_user = _current_user)

    return (TEMPLATE, view_obj.post())

@check_user
def upvote_post(post_id: int):
    if (_current_user == None):
        flash("Please login to access this feature")
        return (REDIRECT, "index", {})
    
    post = Post.search_post(post_id)

    if (post == None):
        flash("Post does not exist")
        return (REDIRECT, "index", {})
    
    _current_user.upvote(post)

    view_obj = View(post=Post.search_post(post_id), cur_user = _current_user)

    return (TEMPLATE, view_obj.post())

@check_user
def downvote_post(post_id: int):
    if (_current_user == None):
        flash("Please login to access this feature")
        return (REDIRECT, "index", {})
    
    post = Post.search_post(post_id)

    if (post == None):
        flash("Post does not exist")
        return (REDIRECT, "index", {})
    
    _current_user.downvote(post)

    view_obj = View(post=Post.search_post(post_id), cur_user = _current_user)

    return (TEMPLATE, view_obj.post())

@check_user
def delete_post(post_id: int):
    if (_current_user == None):
        flash("Please login to access this feature")
        return (REDIRECT, "index", {})
    
    if (not _current_user.is_admin):
        flash("You do not have access to this feature")
        return (REDIRECT, "index", {})
    
    post = Post.search_post(post_id)

    if (post == None):
        flash("Post does not exist")
        return (REDIRECT, "index", {})
    
    post.delete()
    flash("Post deleted successfully")

    return (REDIRECT, "index", {})

@check_user
def delete_user(user_id: int):
    if (_current_user == None):
        flash("Please login to access this feature")
        return (REDIRECT, "index", {})
    
    if (not _current_user.is_admin):
        flash("You do not have access to this feature")
        return (REDIRECT, "index", {})
    
    target_user = User.load_user(user_id)

    if (target_user == None):
        flash("User does not exist")
        return (REDIRECT, "index", {})
    
    if (target_user.is_admin):
        flash("Friendly fire is not enabled")
        return (REDIRECT, "index", {})
    
    target_user.delete()
    flash("User deleted successfully")
    return (REDIRECT, "index", {})
    
@check_user
def add_comment(post_id: int):
    if (_current_user == None):
        flash("Please login to access this feature")
        return (REDIRECT, "index", {})
    
    post = Post.search_post(post_id)

    if (post == None):
        flash("Post does not exist")
        return (REDIRECT, "index", {})
    
    if (_current_user.is_muted):
        return (JSON, {"isMuted": 1})
    
    data = request.json
    post.add_comment(_current_user, data["content"])
    return (JSON, {"isMuted": 0})