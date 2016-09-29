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
    def create(cls, name, user_id):
        category = cls.by_name_user(name, user_id)
        if category:
            return category
        else:
            newCategory = cls(category_name=name,
                              user_id=user_id)
            session.add(newCategory)
            session.commit()
            return newCategory

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


class Item(Base):
    __tablename__ = 'item'

    item_id = Column(Integer, primary_key=True)
    item_name = Column(String(250), nullable=False)
    item_description = Column(String(1000), nullable=False)
    category_id = Column(Integer, ForeignKey('category.category_id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.user_id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'item_name': self.item_name,
            'item_description': self.item_description,
            'item_id': self.item_id
        }


engine = create_engine('sqlite:///item_catalog.db')


Base.metadata.create_all(engine)
