# Data imports
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# Rendering imports
from flask import render_template

Base = declarative_base()

# Connect to Database and create database session
engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


class User(Base):
    """User Table - sqlAlchemy linked with SQLite3 back end"""
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @classmethod
    def create(cls, login_session):
        """Creates User record, taking email from from the login_session
        created during oAuth 2 sequence.
        """
        user = cls.by_email(login_session['email'])
        if user:
            return user
        else:
            newUser = cls(user_name=login_session['username'],
                          email=login_session['email'],
                          picture=login_session['picture'])
            session.add(newUser)
            session.commit()
            return newUser

    @classmethod
    def by_id(cls, user_id):
        """Returns User instance filtered by user_id

        Arg:
            user_id: used to filter the result to a single user
        """
        user = session.query(cls).filter_by(user_id=user_id).first()
        return user

    @classmethod
    def by_email(cls, email):
        """Returns User instance, looked up with email

        Arg:
            email: used to filter the result to a single user
        """
        try:
            user = session.query(cls).filter_by(email=email).first()
            return user
        except:
            return None


class Category(Base):
    """Category table - sqlAlchemy linked with SQLite3 back end"""
    __tablename__ = 'category'

    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.user_id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'category_name': self.category_name,
            'category_id': self.category_id,
            'user_id': self.category_id
        }

    @classmethod
    def add_or_update(cls, name, user_id, category_id=None):
        """Add or update the caegory record

        Args:
            name: category name, per the UI entry
            user_id: user currently signed in
            category_id: present only if being updated

        Returns:
            Adds or updates record in the Category table
        """
        category = cls.by_id(category_id)
        if category:
            return cls.update(name, user_id, category)
        else:
            newCategory = cls(category_name=name,
                              user_id=user_id)
            session.add(newCategory)
            session.commit()
            msg = ('New Category %s Successfully Created'
                   % Category.category_name)
            return newCategory, msg

    @classmethod
    def update(cls, category_name, user_id, category):
        """Returns and updates pdates the category_name, if user owns it.

        Args:
            category_name: Value updated by function
            user_id: Current user, possibly owner of category
            category: category instance to be updated

        Returns:
            Category instance if successful; else False
        """
        if category.user_id == user_id:
            category.category_name = category_name
            session.add(category)
            session.commit()
            return category
        else:
            return False

    @classmethod
    def write(cls, category_name, user_id):
        """Adds a new record to the Category table; returns it as
        category instance.

        Args:
            category_name: name of the category to be created
            user_id: current logged in user

        Returns:
            Adds record to Category table and returns same instance
        """
        newCategory = cls(category_name=category_name,
                          user_id=user_id)
        session.add(newCategory)
        session.commit()
        return newCategory

    @classmethod
    def by_user(cls, user_id):
        """Filter to return all categories owned by user_id, as instance.

        Arg:
            user_id: used to filter the Category table for owner

        Returns:
            categories: all categories owned by user_id, as instance.
        """
        categories = session.query(cls).filter_by(user_id=user_id)
        categories = categories.order_by(cls.category_name).all()
        return categories

    @classmethod
    def by_id(cls, category_id):
        """Filter to return single category - by category_id

        Arg:
            category_id: used in filter to retun category, if present

        Returns:
            category: Category instance, if category with category_id exists;
                      else False
        """
        category = session.query(cls).filter_by(category_id=category_id)
        if category:
            category = category.first()
            return category
        else:
            False

    def render(self, display_items=False):
        """ Allows values to be passed into category_loop.html
            file at runtime.

        Arg:
            display_items: If present, all items within the category are
                           displayed to the user.

        Returns:
            Feeds Category HTML into calling function in flask/jinja template.

        """
        if self:
            self._category_name = self.category_name
            self._category_id = self.category_id
            self._user_id = self.user_id
            self._owner_name = session.query(User).filter_by(
                user_id=self.user_id).one().user_name
            self._items = Item.by_category_id(self.category_id)
            self._show_description = display_items
        return render_template("/category.html", category=self)

    def render_dropdown(self, default_id):
        """ Allows category values to be passed into category_admin.html
            file at runtime"""
        if self:
            self._category_name = self.category_name
            self._category_id = self.category_id
        return render_template("/category_dropdown_part.html",
                               category=self,
                               default_id=default_id)


class Item(Base):
    """Item table - sqlAlchemy linked with SQLite3 back end"""
    __tablename__ = 'item'

    item_id = Column(Integer, primary_key=True)
    item_name = Column(String(250), nullable=False)
    item_description = Column(String(1000), nullable=False)
    category_id = Column(Integer, ForeignKey('category.category_id'))
    user_id = Column(Integer, ForeignKey('user.user_id'))
    category = relationship("Category")
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'item_name': self.item_name,
            'item_description': self.item_description,
            'item_id': self.item_id
        }

    @classmethod
    def add_or_update(cls, item_name, item_description, category_id,
                      user_id, item_id=None):
        """Add or update the item record

        Args:
            item_name: Item name from UI
            item_description: Item description from UI
            category_id: Selected from drop down on UI
            user_id: User currently signed in
            item_id: If present, this is an update; else adding item

        Returns:
            Adds or updates record in the Item table
        """
        item = cls.by_id(item_id)
        if item:
            return cls.update(item_name, item_description, category_id,
                              user_id, item)
        else:
            return cls.write(item_name, item_description, category_id, user_id)

    @classmethod
    def by_id(cls, item_id):
        """Filter to return one item, in an item instance. Based on item_id.

        Arg:
            item_id: used in item filter, so that only one record is returned

        Returns:
            item: item instance if one exists for item_id; else False
        """
        item = session.query(cls).filter_by(item_id=item_id).first()
        if item:
            return item
        else:
            False

    @classmethod
    def update(cls, item_name, item_description, category_id, user_id, item):
        """Updates item record with values from arguments

        Args:
            item_name: Item name, from UI
            item_descpription: Item descriptin, from UI
            category_id: category_id from drop down on UI
            user_id: User currently logged in
            item: item to be updated

        Returns:
            item if user is authorized; else False
        """
        if item.user_id == user_id:
            # Item is owned by current user
            item.item_name = item_name
            item.item_description = item_description
            item.category_id = category_id
            session.commit()
            return item
        else:
            False

    @classmethod
    def write(cls, item_name, item_description, category_id, user_id):
        """Adds a new record to the Item table; returns it as
        item instance.

        Args:
            item_name: item name to be created; from UI
            item_description: item description to be created; from UI
            category_id: Item exists in the category identified; from
                         drop down on UI
            user_id: current logged in user

        Returns:
            Adds record to Item table and returns same as instance
        """
        newItem = cls(item_name=item_name,
                      item_description=item_description,
                      category_id=category_id,
                      user_id=user_id)
        session.add(newItem)
        session.commit()
        return newItem

    @classmethod
    def by_category_id(cls, category_id):
        """Returns all items within a category, as instance, if present

        Arg:
            category_id: used to filter the item list, only returning items
                         for category

        Returns:
            items within the desired category, if present; else False
        """
        items = session.query(cls).filter_by(category_id=category_id)
        if items:
            items = items.order_by(cls.item_name).all()
            return items
        else:
            False

    def render(self, item_display):
        """ Allows values to be passed into category_loop.html
            file at runtime.

        Arg:
            item_display: controls if item information fed into render

        Return:
            rendered HTML - if item_display is True, full item information;
                            else, only the item name
        """
        if self:
            self._item_id = self.item_id
            self._item_name = self.item_name
            self._item_description = self.item_description.replace("\n",
                                                                   "<br>")
            self._category_id = self.category_id
            self._user_id = self.user_id
            self._owner_name = session.query(User).filter_by(
                user_id=self.user_id).one().user_name
        if item_display:
            return render_template("/item_full.html", item=self)
        else:
            return render_template("/item.html", item=self)


engine = create_engine('sqlite:///item_catalog.db')


Base.metadata.create_all(engine)
