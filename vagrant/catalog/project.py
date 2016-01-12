from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from pyatom import AtomFeed
import datetime

app = Flask(__name__)


# load google json for application
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Item App"


# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create a feed for Atom
feed = AtomFeed(title="Catalog Item App",
    subtitle="All changes made to the catalog.",
    feed_url="localhost:8000/atomfeed/",
    url="localhost:8000",
    author="John McLellan")


@app.route('/login')
def showLogin():
    setState()
    return render_template('login.html', STATE=login_session['state'])

# Create anti-forgery state token
def setState():
    if 'state' not in login_session:
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
        login_session['state'] = state


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=100&width=100' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h3>Welcome, '
    output += login_session['username']

    output += '!</h3>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 100px; height: 100px;border-radius: 80px;-webkit-border-radius: 80px;-moz-border-radius: 80px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
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
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h3>Welcome, '
    output += login_session['username']
    output += '!</h3>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 100px; height: 100px;border-radius: \
                80px;-webkit-border-radius: 80px;-moz-border-radius: 80px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Catalog/Item Information
@app.route('/catalog/<category_name>/JSON')
def categoryJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return jsonify(Category_Items=[i.serialize for i in items])


@app.route('/catalog/<category_name>/<item_name>/JSON')
def itemJSON(category_name,item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(
                name=item_name,category_id=category.id).one()
    return jsonify(Item=Item.serialize)


@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(Category).all()
    return jsonify(Categories=[c.serialize for c in categories])


# Atom API feed output
@app.route('/atomfeed/')
def atomFeed():
    return feed.to_string()


# Atom feed add
# Feed posts are generated for any add/delete/edit
# made to the catalog
def atomAdd(itemtype,action,item,url,author):
    feed.add(title="%s %s %s" % (itemtype, item.name, action),
        content="%s %s %s." % (action, itemtype, item.name),
        author=author,
        url="http://localhost:8000/catalog/%s" % url,
        updated=datetime.datetime.utcnow())


# Show all categories and 10 most recent items
@app.route('/')
@app.route('/catalog/')
def catalog():
    setState()
    categories = session.query(Category).order_by(asc(Category.name))
    recentItems = session.query(Item).order_by(desc(Item.id)).limit(10)
    if 'username' not in login_session:
        return render_template('publiccatalog.html', categories=categories, 
                               recentItems=recentItems, STATE=login_session['state'])
    else:
        user = getUserInfo(login_session['user_id'])
        return render_template('catalog.html', categories=categories, 
                               recentItems=recentItems, user=user, 
                               STATE=login_session['state'])


# Create a new category
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        # create new category
        newCategory = Category(name=request.form['name'])
        session.add(newCategory)
        session.commit()

        # create alert and feed updates
        flash('New Category %s Successfully Created' % newCategory.name)
        atomAdd("Category", "Created", newCategory, newCategory.name, 
                login_session['username'])
        return redirect(url_for('catalog'))
    else:
        categories = session.query(Category).order_by(asc(Category.name))
        user = getUserInfo(login_session['user_id'])
        return render_template('newCategory.html', categories=categories, 
                               user=user)


# Delete a category
@app.route('/catalog/<category_name>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    categories = session.query(Category).order_by(asc(Category.name))
    if 'username' not in login_session:
        return redirect('/login')
    user = getUserInfo(login_session['user_id'])
    if request.method == 'POST':
        # We ensure that a category must not have any items associated
        items = session.query(Item).filter_by(category_id=category.id).all()
        if len(items) == 0:
            session.delete(category)
            session.commit()

            # create alert and feed updates
            flash('%s Successfully Deleted' % category.name)
            atomAdd("Category", "Deleted", category, category.name, 
                    login_session['username'])
        else:
            flash('%s could not be deleted. Only empty categories \
                may be deleted.' % category.name)
        return redirect(url_for('catalog'))
    else:
        return render_template('deletecategory.html', category=category, 
                               user=user, categories=categories)

# Show all items for a category
@app.route('/catalog/<category_name>/')
def showCategory(category_name):
    setState()
    categories = session.query(Category).order_by(asc(Category.name))
    category = categories.filter_by(name=category_name).one()
    if 'username' in login_session:
        user = getUserInfo(login_session['user_id'])
        return render_template('category.html', items=category.items, 
                               categories=categories, category=category, 
                               user=user,STATE=login_session['state'])
    else:
        return render_template('category.html', items=category.items, 
                               categories=categories, category=category, 
                               STATE=login_session['state'])

    

# Show an individual item
@app.route('/catalog/<category_name>/<item_name>/')
def showItem(category_name, item_name):
    setState()
    categories = session.query(Category).order_by(asc(Category.name))
    category = categories.filter_by(name=category_name).one()
    item = session.query(Item).filter_by(
                category_id=category.id).filter_by(
                name=item_name).one()
    if 'username' in login_session:
        user = getUserInfo(login_session['user_id'])
        return render_template('item.html', category=item.category,
                               categories=categories, item=item, 
                               user=user, STATE=login_session['state'])
    else:
        return render_template('publicitem.html', category=item.category,
                               categories=categories, item=item,
                               STATE=login_session['state'])

# Check if an item with the same name exists for chosen category
def checkItemUnique(category,item_name):
    try:
        item = session.query(Item).filter_by(
                    category_id=category.id).filter_by(
                    name=item_name).one()
        return item
    except:
        # if no item exists
        return None

# Create a new item
@app.route('/newItem/', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        try:
            # try to find an existing category that matches the input
            category = session.query(Category).filter_by(
                            name=request.form['category']).one()

            # check if that item exists already for this category
            # if it does we redirect the user to that item and inform
            # them that the item was already created
            existingItem = checkItemUnique(category,request.form['name'])
            if existingItem is not None:
                flash('Item [%s] already exists in category [%s].  \
                    If you created the item you may edit it by selecting \
                    edit below.' % (request.form['name'], category.name))
                return redirect(url_for('showItem',
                                        category_name=category.name,
                                        item_name=request.form['name']))

        except:
            # if category does not exist create a new one
            newCategory = Category(name=request.form['category'])
            session.add(newCategory)
            atomAdd("Category", "Created", newCategory, 
                    newCategory.name, login_session['username'])
            session.commit()
            category = session.query(Category).filter_by(
                            name=request.form['category']).one()

        # add new item
        newItem = Item(name=request.form['name'], description=request.form['description'], 
                       category_id=category.id, user_id=login_session['user_id'], 
                       picture=request.form['picture'])
        session.add(newItem)
        session.commit()

        # create flash and feed updates
        atomAdd("Item", "Created", newItem, "%s/%s" % 
            (category.name, newItem.name), login_session['username'])
        flash('New Item %s Successfully Created' % (newItem.name))
        return redirect(url_for('showCategory', category_name=request.form['category']))
    else:
        # deliver new item page
        input_category=""

        # check if new item page was rendered with an argument for
        # the category page it came from (to populate field)
        if request.args.get('category') is not None:
            input_category = request.args.get('category')
        categories = session.query(Category).order_by(asc(Category.name))
        user = getUserInfo(login_session['user_id'])
        return render_template('newitem.html',categories=categories, 
                               user=user, input_category=input_category)

# Edit an item
@app.route('/catalog/<category_name>/<item_name>/edit', methods=['GET', 'POST'])
def editItem(category_name,item_name):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(
                name=item_name).filter_by(
                category_id=category.id).one()

    if login_session['user_id'] != item.user_id:
        return "<script>function myFunction() {alert('You are not authorized \
            to edit items you did not create.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['picture']:
            item.picture = request.form['picture']
        if request.form['category']:
            try:
                # try to find an existing category that matches the input
                category = session.query(Category).filter_by(
                                name=request.form['category']).one()

                # check if that item exists already for this category
                # if it does we redirect the user to that item and inform
                # them that the item was already created
                existingItem = checkItemUnique(category,request.form['name'])
                if existingItem is not None:
                    flash('Item [%s] already exists in category [%s]. If \
                        you created the item you may edit it by selecting \
                        edit below.' % (request.form['name'], category.name))
                    return redirect(url_for('showItem',category_name=category.name,
                                            item_name=request.form['name']))

            except:
                # if category does not exist create a new one
                newCategory = Category(name=request.form['category'])
                session.add(newCategory)
                atomAdd("Category", "Created", newCategory, 
                        newCategory.name, login_session['username'])
                session.commit()
                item.category_id = session.query(Category).filter_by(
                                        name=request.form['category']).one().id

        session.add(item)
        session.commit()

        # Generate alerts and feed updates
        atomAdd("Item", "Updated", item, "%s/%s" % 
            (category.name, item.name), login_session['username'])
        flash('Item Successfully Edited')
        return redirect(url_for('showCategory', category_name=item.category.name))
    else:
        categories = session.query(Category).order_by(asc(Category.name))
        user = getUserInfo(login_session['user_id'])
        return render_template('edititem.html', item=item, 
                               categories=categories, user=user)


# Delete an item
@app.route('/catalog/<category_name>/<item_name>/delete', methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(
                name=item_name).filter_by(
                category_id=category.id).one()

    if login_session['user_id'] != item.user_id:
        return "<script>function myFunction() {alert('You are not authorized to \
            delete items you did not create. Please create your own items in \
            order to delete items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        atomAdd("Item", "Deleted", item, "%s/%s" % 
            (category.name, item.name), login_session['username'])
        flash('Item Successfully Deleted')
        return redirect(url_for('showCategory', category_name=category.name))
    else:
        categories = session.query(Category).order_by(asc(Category.name))
        user = getUserInfo(login_session['user_id'])
        return render_template('deleteitem.html', item=item, 
                               categories=categories, user=user)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        del login_session['state']
        flash("You have successfully been logged out.")
        return redirect(url_for('catalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('catalog'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)