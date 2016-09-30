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
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @classmethod
    def create(cls, login_session):
        user = cls.by_name_email(login_session['username'],
                                 login_session['email'])
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
        user = session.query(cls).filter_by(user_id=user_id).first()
        return user

    @classmethod
    def by_name_email(cls, user_name, email):
        user = session.query(cls).filter_by(user_name=user_name)
        user = user.filter_by(email=email).first()
        return user

    @classmethod
    def by_email(cls, email):
        try:
            user = session.query(cls).filter_by(email=email).first()
            return user
        except:
            return None


class Category(Base):
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
        category = cls.by_id(category_id)
        if category:
            if category.user_id == user_id:
                category.category_name = name
                session.add(category)
                session.commit()
                msg = ('New Category %s Successfully Updated'
                       % Category.category_name)
                return category, msg
            else:
                msg = ('Category %s Not Owned by User'
                       % Category.category_name)
                return category, msg
        else:
            newCategory = cls(category_name=name,
                              user_id=user_id)
            session.add(newCategory)
            session.commit()
            msg = ('New Category %s Successfully Created'
                   % Category.category_name)
            return newCategory, msg

    @classmethod
    def by_name_user(cls, name, user_id):
        category = session.query(cls).filter_by(category_name=name)
        category = category.filter_by(user_id=user_id).first()
        return category

    @classmethod
    def by_user(cls, user_id):
        categories = session.query(cls).filter_by(user_id=user_id)
        categories = categories.order_by(cls.category_name).all()
        return categories

    @classmethod
    def by_id(cls, category_id):
        category = session.query(cls).filter_by(category_id=category_id)
        if category:
            category = category.first()
            return category

    @classmethod
    def name_by_id(cls, category_id):
        return Category.by_id(category_id).category_name

    def render(self):
        """ Allows values to be passed into category_loop.html
            file at runtime"""
        if self:
            self._category_name = self.category_name
            self._category_id = self.category_id
            self._user_id = self.user_id
            self._owner_name = session.query(User).filter_by(
                user_id=self.user_id).one().user_name
        return render_template("/category.html", category=self)

    def render_dropdown(self, default_id):
        """ Allows values to be passed into category_loop.html
            file at runtime"""
        if self:
            self._category_name = self.category_name
            self._category_id = self.category_id
        return render_template("/category_dropdown_part.html",
                               category=self,
                               default_id=default_id)


class Item(Base):
    __tablename__ = 'item'

    item_id = Column(Integer, primary_key=True)
    item_name = Column(String(250), nullable=False)
    item_description = Column(String(1000), nullable=False)
    category_id = Column(Integer, ForeignKey('category.category_id'))
    user_id = Column(Integer, ForeignKey('user.user_id'))
    category = relationship(Category)
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'item_name': self.item_name,
            'item_description': self.item_description,
            'item_id': self.item_id
        }

    def add_or_update(cls, item_name, item_description, category_id,
                      user_id, item_id=None):
        item = cls.by_id(item_id)
        if item:
            if item.user_id == user_id:
                # Item exists and is owned by current user
                item.item_name = item_name
                item.item_description = item_description
                item.category_id = category_id
                session.add(item)
                session.commit()
                msg = ('New Item %s Successfully Updated'
                       % Item.item_name)
                return item, msg
            else:
                msg = ('Item %s Not Owned by User'
                       % Item.category_name)
                return item, msg
        else:
            # Item does not exist in db, add item
            newItem = cls(item_name=item_name,
                          item_description=item_description,
                          category_id=category_id,
                          user_id=user_id)
            session.add(newItem)
            session.commit()
            msg = ('New Item %s Successfully Created'
                   % Item.item_name)
            return newItem, msg

    @classmethod
    def create(cls, item_name, item_description, category_id, user_id):
        item = cls.by_category_user(category_id, user_id)
        if item:
            return item
        else:
            newItem = cls(item_name=item_name,
                          item_description=item_description,
                          category_id=category_id,
                          user_id=user_id)
            session.add(newItem)
            session.commit()
            return newItem

    @classmethod
    def by_id(cls, item_id):
        item = session.query(cls).filter_by(item_id=item_id).first()
        return item

    @classmethod
    def by_category_user(cls, category_id, user_id):
        item = session.query(cls).filter_by(category_id=category_id)
        item = item.filter_by(user_id=user_id).all()
        return item

    @classmethod
    def by_category_id(cls, category_id):
        categories = session.query(cls).filter_by(category_id=category_id)
        categories = categories.order_by(cls.item_name).all()
        return categories

    def render(self):
        """ Allows values to be passed into category_loop.html
            file at runtime"""
        if self:
            self._item_id = self.item_id
            self._item_name = self.item_name
            self._item_description = self.item_description
            self._category_id = self.category_id
            self._user_id = self.user_id
            self._owner_name = session.query(User).filter_by(
                user_id=self.user_id).one().user_name
        return render_template("/category.html", category=self)


engine = create_engine('sqlite:///item_catalog.db')


Base.metadata.create_all(engine)
