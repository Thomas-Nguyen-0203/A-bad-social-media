from app import app, sock
from flask import redirect, url_for, session

from app.models import *

@app.route("/")
@app.route("/index")
@app.route("/index/<first_login>")
def index(first_login=False):

    first_login = True if first_login == "True" else False
    return get_index(first_login)[1]

@app.route("/login", methods=["GET", "POST"])
def login():
    ret_val = get_login()

    if (ret_val[0] == URL):
        if "first_login" not in session:
            session["first_login"] = True
            return url_for(ret_val[1], first_login=True)
        else:
            session.pop("first_login")
            return url_for(ret_val[1])
    
    elif (ret_val[0] == REDIRECT):
        return redirect(url_for(ret_val[1]))
    else:
        return ret_val[1]

@app.route("/logout")
def logout():
    if "first_login" in session:
        session.pop("first_login")
    return redirect(url_for(log_user_out()[1]))

@app.route("/signup", methods=["GET", "POST"])
def sign_up():
    ret_val = sign_user_up()

    if (ret_val[0] == URL):
        return url_for(ret_val[1])
    elif (ret_val[0] == REDIRECT):
        return redirect(url_for(ret_val[1]))
    else:
        return ret_val[1]

@app.route("/page/<int:user_id>")
def get_profile_page(user_id: int):
    ret_val = get_user_pf_page(user_id)

    if (ret_val[0] == REDIRECT):
        return redirect(url_for(ret_val[1]))

    else:
        return ret_val[1]

@app.route("/search")
@app.route("/search/")
@app.route("/search/<username>")
def search(username: str = None):
    ret_val = search_user(username)

    if (ret_val[0] == REDIRECT):
        return redirect(url_for(ret_val[1], **ret_val[2]))
    return ret_val[1]
    
@app.route("/page/<int:user_id>/add_friend", methods=["POST"])
def add_friend(user_id: int):
    ret_val = add_friend_logic(user_id)
    
    return url_for(ret_val[1], **ret_val[2])
    
@app.route("/page/<int:user_id>/remove_friend", methods=["POST"])
def remove_friend(user_id: int):
    ret_val = remove_friend_logic(user_id)
    
    return url_for(ret_val[1], **ret_val[2])

@app.route("/page/<int:receiver_id>/chat/<int:sender_id>")
def get_chat_page(receiver_id: int, sender_id: int):
    ret_val = chat_page_logic(receiver_id, sender_id)

    if (ret_val[0] == REDIRECT):
        return redirect(url_for(ret_val[1], **ret_val[2]))
    
    return ret_val[1]

@app.route("/locked")
def locked_account():
    return "Your account is locked bro."
    
@app.route("/reset_timer")
def reset_timer():
    ret_val = reset_user_timeout()

    return redirect(url_for(ret_val[1], *ret_val[2]))

@app.route("/faq")
def faq():
    return get_faq()[1]

@app.route("/forum")
def forums():
    return get_forums()[1]

@app.route("/make_new_post", methods=["GET", "POST"])
def new_post():
    action = get_newpost()
    if (action[0] == JSON or action[0] == TEMPLATE):
        return action[1]
    
    elif (action[0] == REDIRECT):
        return redirect(url_for(action[1], **action[2]))
    
    elif (action[0] == URL):
        action[1]["URL"] = url_for(action[1]["URL"], **action[1]["params"])
        return action[1] 
    
@app.errorhandler(404)
def page_not_found(e):
    ret_val = not_found()
    return ret_val[1]

@sock.route("/page/<int:receiver_id>/chat/<int:sender_id>/messages")
def check_new_msg(sock, receiver_id: int, sender_id: int):
    while (True):
        data = sock.receive()
        sock.send(message_logic(data, receiver_id, sender_id))

@app.route("/mute/<int:user_id>", methods=["POST"])
def mute_user(user_id: int):
    action = mute_user_logic(user_id)

    if (action[0] == REDIRECT):
        return redirect(url_for(action[1], **action[2]))

@app.route("/unmute/<int:user_id>", methods=["POST"])
def unmute_user(user_id: int):
    action = unmute_user_logic(user_id)

    if (action[0] == REDIRECT):
        return redirect(url_for(action[1], **action[2]))
    
@app.route("/posts/<int:id>")
def see_post(id: int):
    action = see_post_logic(id)

    if (action[0] == REDIRECT):
        return redirect(url_for(action[1], **action[2]))
    elif (action[0] == TEMPLATE):
        return action[1]
    
@app.route("/posts/<int:post_id>/upvote", methods=["POST"])
def upvote_post_route(post_id: int):
    action = upvote_post(post_id)

    if (action[0] == REDIRECT):
        return redirect(url_for(action[1], **action[2]))
    else:
        return action[1]

@app.route("/posts/<int:post_id>/downvote", methods=["POST"])
def downvote_post_route(post_id: int):
    action = downvote_post(post_id)

    if (action[0] == REDIRECT):
        return redirect(url_for(action[1], **action[2]))
    else:
        return action[1]
    
@app.route("/posts/<int:post_id>/delete", methods=["POST"])
def delete_post_route(post_id: int):
    action = delete_post(post_id)

    return redirect(url_for(action[1], **action[2]))

@app.route("/page/<int:user_id>/delete")
def delete_user_route(user_id: int):
    action = delete_user(user_id)

    return redirect(url_for(action[1], **action[2]))

@app.route("/posts/<int:post_id>/comment", methods=["POST"])
def add_comment_route(post_id: int):
    action = add_comment(post_id)

    return action[1]
