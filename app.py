from flask import (
    Flask,
    request,
    Response,
    redirect,
    url_for,
    jsonify,
    make_response,
    session,
)
from boto3.dynamodb.conditions import Key
from models.user import User
from models.todo import Todo
import json
import boto3
import jwt
import datetime
from os import environ
from functools import wraps
import uuid


client = boto3.resource("dynamodb")
user_table = client.Table("users")
items_table = client.Table("items")

app = Flask(__name__)

app.config["SECRET_KEY"] = "CYUq04pUPqeP26PTIR5B"


def _get_user_info(username_provided):
    response = User.get(username=username_provided)
    if not response:
        return jsonify({"message": "User does not exist."}), 403
    return response


def login_required(f):
    def decorated(*args, **kwargs):
        token = session["token"]
        if not token:
            return jsonify({"message": "You are not authenticated"}), 403
        data = jwt.decode(token, app.config["SECRET_KEY"])
        if data:
            return jsonify({"message": "Your token is invalid"}), 403
        return jsonify({"message": f"{token}"}), 403

    return decorated


@app.route("/", methods=["GET"])
def root():
    return redirect(url_for("login"))


def _user_already_exists(username_provided):
    query = User.get(username=username_provided)
    if query:
        return True
    return False


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")

    if _user_already_exists(username) == True:
        return jsonify({"message": "Username is taken, choose another."}), 200

    if username and password:
        User.put({"username": username, "password": password})
        return jsonify({"message": f"User '{username}' created"}), 200
    else:
        return jsonify({"message": "Error creating user"}), 200


# look more into session
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    user = _get_user_info(username)
    if _user_already_exists(username) == False:
        return jsonify({"message": "User doesn't exist."}), 200
    if user.password == password:
        token = jwt.encode(
            {
                "user": user.username,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            },
            app.config["SECRET_KEY"],
        )
        token = token.decode("UTF-8")
        session["username"] = username
        session["token"] = token
        return jsonify({"message": f"{token}"}), 200
    else:
        return jsonify({"message": "Password is incorrect."}), 200


@login_required
@app.route("/items", methods=["GET"])
def items():
    items = list(Todo.scan(username=session["username"]))
    if not items:
        return (
            jsonify({"message": {"item_count": 0, "response": "User has no items"}}),
            200,
        )
    item_string = list(
        {
            "title": item.title,
            "text": item.text,
            "dt_created": item.dt_created,
            "item_id": item.item_id,
        }
        for item in items
    )
    
    return jsonify({"message": {"item_count": len(items), "items": item_string}}), 200


@login_required
@app.route("/items", methods=["POST"])
def create_item():
    username = session["username"]
    dt_created = datetime.datetime.utcnow()
    text = request.form.get("text")
    title = request.form.get("title")
    item_id = int(str(uuid.uuid4().int)[:10])
    item_json = {
            "item_id": item_id,
            "username": username,
            "dt_created": dt_created,
            "text": text,
            "title": title,
        }
    record = Todo.put(
        {
            "item_id": item_id,
            "username": username,
            "dt_created": dt_created,
            "text": text,
            "title": title,
        }
    )

    return jsonify({"message": "Item created.", "Item": item_json}), 200


def _get_item_info(username_provided, id_provided):
    record = Todo.get(username=username_provided, item_id=id_provided)
    if not record:
        jsonify({"message": "record doesn't exist"})
    return record

@login_required
@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    item = _get_item_info(session["username"], item_id)
    old_item_json = {
            "item_id": item.item_id,
            "dt_created": item.dt_created,
            "text": item.text,
            "title": item.title,
        }

    if not item:
        return jsonify(
            {"message": "User has no items or an item with that ID does not exist."}
        )

    input_text = request.form.get("text")
    input_title = request.form.get("title")

    if input_text:
        item.text = input_text
    elif input_title:
        item.title = input_title
    item.save()
    new_item_json = {
            "item_id": item.item_id,
            "dt_created": item.dt_created,
            "text": item.text,
            "title": item.title,
        }
    return jsonify({"message":"Item has been updated", "original_item": old_item_json, "updated_item":new_item_json})


@login_required
@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = Todo.get(username=session["username"], item_id=int(item_id))
    if not item:
        return jsonify({"message": "There is no item that exists with that ID."})
    item_json = {
            "item_id": item.item_id,
            "dt_created": item.dt_created,
            "text": item.text,
            "title": item.title,
        }
    items_table.delete_item(Key={"username": session["username"], 'item_id': int(item_id)})
    return jsonify({"message": "Item created.", "Item": item_json}), 204
