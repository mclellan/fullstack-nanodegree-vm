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
   sudo pip install Flask
   sudo pip install SQLAlchemy
   sudo pip install pyatom
Create database: python database_setup.py<br>
Run web server: python project.py
Visit localhost:8000/ in a web browser to access the page.
