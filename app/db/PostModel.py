from .config import CRUD
from flask import g
from datetime import datetime
from .UserModel import User
from markdown import markdown
import bleach
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

formatter = logging.Formatter('%(levelname)s:%(name)s:%(asctime)s:%(funcName)s:%(message)s')	
file_handler = logging.FileHandler(os.path.abspath('logs') + '/PostModel.log')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)


logger.addHandler(stream_handler)
logger.addHandler(file_handler)

class Post(CRUD):
    tablename = 'posts'
    def __init__(self,**columns):
        self.id = columns.get('id',None)
        self.body = columns.get('body',None)
        self.time_stamp = datetime.utcnow()
        self.author_id = columns.get('author_id',None)
        self.in_db = self._check_post()
    
    def _check_post(self):
        if self.id is not None:
            post_dict = self._check(self.tablename,'id',self.id)
        else:
            logger.info('A valid id must be provided for the post')
            return False
        if post_dict is None:
            return False
        else:
            self.id = post_dict['id']
            self.body = post_dict['body']
            self.time_stamp = post_dict['time_stamp']
            self.author_id = post_dict['author_id']
            return True

    @classmethod
    def get_post(cls,primary_key=None):
        if primary_key is not None:
            try:
                conn = g.db
                cursor = conn.cursor()
                sql_query = '''SELECT * FROM users 
                               JOIN posts
                               ON users.id = posts.author_id
                               WHERE posts.id = %s;'''
                cursor.execute(sql_query,(primary_key,))
                post = [cursor.fetchone()]
                return cls._dict_transform(post,cursor)

            except psycopg2.DatabaseError as e:
                logger.exception('Something went wrong fetching the post: %s' % e)
                return None
        else:
            logger.info('A valid post id must be given.')
            return None

    @staticmethod
    def count():
        try:
            conn = g.db
            cursor = conn.cursor()
            sql_query = 'SELECT COUNT(*) FROM posts;'
            cursor.execute(sql_query)
            count = cursor.fetchone()[0]
            return count
        except psycopg2.DatabaseError as e:
            logger.exception('Somthing went wrong while getting the posts count: %s' % e)
            return None

    @staticmethod
    def body_html_transform(value):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        body_html = bleach.linkify(bleach.clean(
            markdown(value,output_format='html'),
            tags=allowed_tags,strip=True))
        return body_html

    @staticmethod
    def _dict_transform(posts,cursor):
        if len(posts) != 0:
            props = [desc[0] for desc in cursor.description]
            posts_list = []
            for post in posts:
                posts_list.append(dict(zip(props,post)))
                cursor.close()
            return posts_list
        return posts

    @classmethod
    def get_all_posts(cls):
        try:
            conn = g.db
            cursor = conn.cursor()
            sql_query = 'SELECT * FROM posts ORDER BY time_stamp DESC;'
            cursor.execute(sql_query)
            posts = cursor.fetchall()
            return cls._dict_transform(posts,cursor)
        except psycopg2.DatabaseError as e:
            logger.exception('Something went wrong fetching all the posts in the get_all_posts method: %s' % e)
            return None

    @classmethod
    def posts_by_page(cls,page,posts_per_page=10):
        try:
            conn = g.db
            cursor = conn.cursor()
            sql_query = '''SELECT * FROM users
                JOIN posts
                ON posts.author_id = users.id
                OFFSET %s LIMIT %s;'''
            cursor.execute(sql_query,(posts_per_page*page,posts_per_page))
            posts = cursor.fetchall()
            return cls._dict_transform(posts,cursor)
        except psycopg2.DatabaseError as e:
            logger.exception('Something went wrong retrieving the posts by page: %s' % e)
    
    @classmethod
    def posts_by_author(cls,author_id):
        try:
            conn = g.db
            cursor = conn.cursor()
            sql_query = '''SELECT * FROM users
                            JOIN posts
                            ON users.id = posts.author_id
                            WHERE author_id = %s 
                            ORDER BY time_stamp DESC;'''
            cursor.execute(sql_query,(author_id,))
            posts = cursor.fetchall()
            return cls._dict_transform(posts,cursor)
        except psycopg2.DatabaseError as e:
            logger.exception("Something went wrong trying to get author %s's id: %s" % (author_id,e))
            return None

    def insert(self):
        if self.in_db is False:
            primary_key = self._insert(self.tablename,body=self.body,
                time_stamp=self.time_stamp,author_id=self.author_id,
                body_html=self.body_html_transform(self.body))
            if primary_key is not None:
                self.id = primary_key
                self.in_db = True

        else:
            logger.info('The post was already in the database.')

    def update(self,prop_dict):
        if self.id is not None and self.in_db is True and "body" in prop_dict:
            prop_dict['body_html'] = self.body_html_transform(prop_dict['body'])
            post = self._update(self.tablename,self.id,prop_dict)
            if post is not None:
                for prop in prop_dict:
                    if hasattr(self,prop):
                        self.__dict__[prop] = prop_dict[prop]
        else:
            logger.info('Post must already exist in the database, and a body key must \
                be specified in prop_dict')
