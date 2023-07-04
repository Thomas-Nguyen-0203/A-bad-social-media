from flask import render_template

class View:
    def __init__(self, **kwargs):
        self.args = kwargs

    def index_page(self):
        return render_template("index.html", **self.args)
    
    def faq_page(self):
        return render_template("faq.html", **self.args)
    
    def forum_page(self):
        return render_template("forums.html", **self.args)
    
    def new_post(self):
        return render_template("newpost.html", **self.args)
    
    def post(self):
        return render_template("post.html", **self.args)

    def login_page(self):
        return render_template("new_login.html", **self.args)

    def profile_page(self):
        return render_template("user_profile.html", **self.args)

    def search(self):
        return render_template("search.html", **self.args)
    
    def messages_page(self):
        return render_template("messages.html", **self.args)
    
    def not_found_page(self):
        return render_template("404.html", **self.args)