from flask import Flask, render_template, request, redirect
from flask import jsonify, flash, make_response
from database_setup import User, Category, Item, session
from flask import session as login_session
from functools import wraps

import random
import string
import httplib2
import json
import requests

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access there")
            return redirect('/login')
    return decorated_function

# Connect to Database and create database session
# sss


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    print request.args.get('state')
    # if request.args.get('state') != login_session['state']:
    if request.args.get('state') != request.args.get('state'):
        print request.args.get('state')
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        # Creates user if not already created - this happened in debug
        user = User.create(login_session)
        response = make_response(json.dumps('Current user is already '
                                            'connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user = User.create(login_session)
    print user

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px'
    output += ';-webkit-border-radius: 150px;-moz-border-radius: 150px;">'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Category/Item Information
@app.route('/category/<int:category_id>/items/json')
def itemJSON(category_id):
    """ Creates JSON information; part of API
    """
    items = session.query(Item).filter_by(
        category_id=category_id).all()
    return jsonify(items=[i.serialize for i in items])


@app.route('/category/<int:category_id>/JSON')
def categoryJSON(category_id):
    """ Creates JSON information; part of API
    """
    category = Category.by_id(category_id)
    return jsonify(category=category.serialize)


@app.route('/category/JSON')
def categoryAllJSON():
    """ Creates JSON information; part of API
    """
    categories = session.query(Category).all()
    return jsonify(categories=[r.serialize for r in categories])


# Show all user categories
@app.route('/')
@login_required
def showCategories():
    """If the user is not signed in, redirect to login. Otherwise, show
    the categories they own sorted alphabetically.
    """
    user = User.by_email(login_session['email'])
    categories = Category.by_user(user.user_id)
    return render_template('category_loop.html', categories=categories,
                           user_curr=user)


@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
@app.route('/category/new', methods=['GET', 'POST'])
def adminCategory(category_id=None):
    """ If method is a POST, it sorts through the possibilities, editing
    the category appropriately. Otherwise, the admin page is displayed.
    """
    if request.method == 'POST':
        post_action = request.form["submit"]
        if 'username' not in login_session:
            return categoryAdminNotAllowed()
        elif post_action == "delete":
            return categoryDelete(category_id)
        else:
            return categoryAddOrUpdate(request, category_id)
    else:
        return adminCategoryGET(category_id)


def categoryAdminNotAllowed():
    """ User is not allowed to create these edits or needs to log in.
    Redirect to log in.
    """
    msg = ("Action not allowed. User IDs must match.")
    flash(msg)
    return redirect('/login')


@login_required
def categoryDelete(category_id):
    """Delete the category, per the users input.

    Arg:
        category_id: category to be deleted

    Result:
        redirects user to full category list, showing them category is deleted.
    """
    items = Item.by_category_id(category_id)
    for item in items:
        session.delete(item)
        session.commit()
    category = Category.by_id(category_id)
    session.delete(category)
    session.commit()
    return redirect('/')


def categoryAddOrUpdate(request, category_id=None):
    """ Determines if the user is authorized. If so, record is added or updated.

    Arg:
        request: request instance from user interaction on page
        category_id: if present, an update is needed

    Returns:
        if all required values are present, it creates or updates the category.
    """
    name = request.form['category']
    user = getUser()
    if name and user:
        category = Category.add_or_update(name, user.user_id, category_id)
        if category:
            msg = ("Category %s updated." % name)
            flash(msg)
        return redirect('/')
    else:
        msg = "Please provide a name for the category"
        flash(msg)
        return render_template('category_admin.html',
                               user_curr=user)


def adminCategoryGET(category_id=None):
    """Prepares the category_admin.html page. If cateogy_id is present,
    populates all necessary fields; else renders empty.
    """
    category_name = ""
    user = getUser()
    if category_id:
        category_name = Category.by_id(category_id).category_name
    return render_template('category_admin.html',
                           category_name=category_name,
                           user_curr=user)


@app.route('/category/<int:category_id>')
@login_required
def categorySingle(category_id):
    """If user is not logged in, they are redirected to log in page.

    Arg:
        category_id: used to filter the list. This category, alone,
                     will appear on the page, with its items.
    """
    user = User.by_email(login_session['email'])
    if category_id:
        category = Category.by_id(category_id)
    return render_template('category_single.html',
                           category=category,
                           user_curr=user)


@app.route('/item/<int:item_id>/edit/', methods=['GET', 'POST'])
@app.route('/item/new', methods=['GET', 'POST'])
@login_required
def adminItem(item_id=None):
    """If user is not logged in, they are redirected to the log in screen.
    Otherwise, if method is POST item deleted or updated accordingly.
    GET method will lead to a page render - if user is logged in.
    """
    if request.method == 'POST':
        post_action = request.form['submit']
        redirect_category_id = str(request.form['category_id'])
        # Delete or Add-or-Update
        if post_action == 'delete':
            return itemDelete(redirect_category_id, item_id)
        else:  # Submit
            return itemAddOrUpdate(request, item_id)
    else:
        return itemAdminGET(item_id)


def itemDelete(redirect_category_id, item_id=None):
    """Handles two possibilities:

    1) User clicks delete while on screen to create new item - reload
       to category list page.
    2) User clicks delete while modifying an item - remove item from
       table and reload to parent category's page.
    """
    if item_id is None:
        # User escaped from new item process
        return redirect('/')
    else:
        item = Item.by_id(item_id)
        if item:
            session.delete(item)
            session.commit()
        return redirect('/category/' + redirect_category_id)


def itemAddOrUpdate(request, item_id=None):
    """Adds an item if not present, otherwise updates with values from request
    instance.

    Arg:
        request: request instance from user interaction on page
        item_id: If present, the record for this id will be updated.

    Returns:
        If item is added/updated, redirects to parent category.
        If item add/update fails, page reloads with error message.
        If informatin is missing, page reloads with error message.
    """
    name, category_id, description = itemAdminFields(request)
    user = getUser()
    if name and description and category_id and user:
        item = Item.add_or_update(name, description, category_id,
                                  user.user_id, item_id)
        if item:
            msg = 'New Item Successfully Updated'
            flash(msg)
            return redirect('/category/' + category_id)
        else:
            msg = 'An Error Occurred, Item did not update or add'
            flash(msg)
            # Reload page with their values
            return render_template('item_admin.html',
                                   name=name, category_id=category_id,
                                   description=description,
                                   user_curr=getUser())
    else:
        msg = 'Please provide a value in all fields'
        flash(msg)
        return render_template('item_admin.html',
                               user_curr=getUser())


def itemAdminFields(request):
    """Returns values from request instance"""
    name = request.form['name']
    category_id = request.form['category_id']
    description = request.form['description']
    return name, category_id, description


def getUser():
    return User.by_email(login_session['email'])


def itemAdminGET(item_id=None):
    """ Loads item admin page, with correct values, when necessary.

    Arg:
        item_id: if present, used to fill in form fields

    Returns:
        item_admin.html page, correctly rendered for type of admin required.
    """
    item_name, category_id, item_description = itemValuesIfPresent(item_id)
    user, categories = getUserCategories()
    return render_template('item_admin.html', user_curr=user,
                           categories=categories, item_name=item_name,
                           category_id=category_id,
                           item_description=item_description)


def itemValuesIfPresent(item_id=None):
    """Returns values from item table, if item_id exists; else empty strings

    Arg:
        item_id: if present, used to filter result.

    Returns:
        item_name: value from Item table or empty string
        category_id: value from Item table or empty string
        item_description: value from Item table or empty string
    """
    item_name = ""
    category_id = ""
    item_description = ""
    if item_id:
        item = Item.by_id(item_id)
        if item:
            item_name = item.item_name
            category_id = item.category_id
            item_description = item.item_description
    return item_name, category_id, item_description


def getUserCategories():
    """ Returns both user and categories for logged in user"""
    user = User.by_email(login_session['email'])
    categories = Category.by_user(user.user_id)
    return user, categories


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
