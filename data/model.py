from flask_sqlalchemy import SQLAlchemy
from flask import Flask, current_app
import os
from config import Config

basedir = os.path.abspath(os.path.dirname(__file__))
app = current_app
db = SQLAlchemy()


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, index=True, unique=True, autoincrement=True)
    # 用户名，不可修改，唯一
    username = db.Column(db.VARCHAR(255), nullable=False, unique=True)
    # 显示名，应该与游戏名相符，可修改，不唯一
    nickname = db.Column(db.Text, nullable=False)
    # 身份，0为普通成员，1为管理员，2为会长
    role = db.Column(db.Integer, nullable=False)
    # 密码，hashed using bcrypt
    password = db.Column(db.Text, nullable=False)
    # 创建时间，自动生成
    created_at = db.Column(db.Date, nullable=False)
    # 绑定的邮箱，可空
    email = db.Column(db.Text)
    # 邮箱已验证
    email_verified = db.Column(db.Boolean, nullable=False)
    # 绑定的手机号，可空
    phone = db.Column(db.Text)
    # 手机号已验证
    phone_verified = db.Column(db.Boolean, nullable=False)
    # 在此日期之前的 token 都会失效（比如更改密码时之类的）
    valid_since = db.Column(db.Date, nullable=False)
    # 外键关联Groups
    group_id = db.Column(db.Integer,db.ForeignKey('group.id'),nullable=True)
    # 方便关联查询
    group = db.relationship('Groups',backref='users')

    def __repr__(self):
        return '<users %r' % self.id


class Groups(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True, index=True, unique=True, autoincrement=True)
    # 群聊号，可以通过群聊号找到公会，也可以在公会找到群号，会长可修改
    group_chat_id = db.Column(db.Text, nullable=True)
    # 公会名，会长可修改
    name = db.Column(db.Text, nullable=False)
    # 公会介绍，会长/管理员可修改
    description = db.Column(db.Text, nullable=False)
    # 公会所有人
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 当前Boss代目，每次公会战刷新
    current_boss_gen = db.Column(db.Integer)
    # 当前是第几个Boss，每次公会战刷新
    current_boss_order = db.Column(db.Integer)
    # 剩余血量，每次公会战刷新
    boss_remaining_health = db.Column(db.Integer)
    # 必须申请出刀
    must_request = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return '<group %r' % self.id


class Records(db.Model):
    __tablename__ = 'records'
    id = db.Column(db.Integer, primary_key=True, index=True, unique=True, autoincrement=True)
    # 对应的 Group ID
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    # 对应的 Group Object
    group = db.relationship('Groups', backref=db.backref('records'))
    # 这是 # 代目
    boss_gen = db.Column(db.Integer, nullable=False)
    # 这是 # 王
    boss_order = db.Column(db.Integer, nullable=False)
    # 伤害
    damage = db.Column(db.Integer, nullable=False)
    # 积分，根据以上信息自动生成
    score = db.Column(db.Integer, nullable=False)
    # 用户ID
    user_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    # 对应的 User Object
    user = db.relationship('Users', backref=db.backref('records'))
    # 游戏名，用于显示
    nickname = db.Column(db.Text, nullable=False)
    # 出刀时间
    date = db.Column(db.DateTime, nullable=False)
    # 出刀类型，normal：普通刀，last：尾刀，compensation：尾刀
    type = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '<records %r' % self.id


# 存放入会申请和邀请的地方
class RequestsAndInvites(db.Model):
    __tablename__ = 'requests_and_invites'
    id = db.Column(db.Integer, primary_key=True, index=True, unique=True, autoincrement=True)
    # 公会ID
    group_id = db.Column(db.Integer, nullable=False)
    # 玩家ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 类型：request=玩家申请加入某公会，invite=公会管理邀请玩家加入某公会
    type = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '<career_fair %r' % self.id