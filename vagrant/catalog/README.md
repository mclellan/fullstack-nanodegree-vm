# udacity-catalog
Udacity Catalog database and website.

#####Get latest revision:
  https://github.com/mclellan/fullstack-nanodegree-vm/archive/master.zip
<br><br>
#####Contents of /vagrant/catalog/:
```
README.md
client_secrets.json
database_setup.py
database_setup.pyc
fb_client_secrets.json
itemcatalog.db
project.py
static/styles.css
templates/catalog.html
templates/category.html
templates/deletecategory.html
templates/deleteitem.html
templates/edititem.html
templates/item.html
templates/login.html
templates/main.html
templates/navbar.html
templates/newCategory.html
templates/newitem.html
templates/publiccatalog.html
templates/publicitem.html
```
<br>
#####Requirements
    Python 2.7
    Vagrant VM
    Flask
    SQLAlchemy
    pyAtom
<br>
#####Quickstart:
Start provided Vagrant VM and log in.<br>
Navigate to /vagrant/catalog/<br>
Ensure requirements are installed:
* sudo pip install Flask
* sudo pip install SQLAlchemy
* sudo pip install pyatom

Create database: python database_setup.py<br>
Run web server: python project.py<br>
Visit localhost:8000/ in a web browser to access the page.<br>
<br>
#####Features:
* Guest users my view all content: catalog, categories, items. They will also be shown the add item and add category links but will be prompted to log in before they are allowed to submit content.
* Logged in users may add content of any type and edit/delete that content later. Users may not delete another user's content. 
* Categories without any items may be deleted by any user. 
* Two API endpoints have been implemented: JSON and pyAtom accessible at:
  * /catalog/JSON    (all items in the database)
  * /catalog/\<category_name>/JSON    (all items in a category)
  * /catalog/\<category_name>/<item_name>/JSON    (a single item)
  * /catalog/atomfeed    (feed of user actions such as new items, item edits, item deletion, etc)
* Item names are unique by category (e.g. Category Basketball may only have one item "Ball" but a separate category may also contain "Ball")
* User actions are reflected on the next page-load via Flask's flash.
