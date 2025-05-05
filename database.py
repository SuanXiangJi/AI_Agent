from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, load_only
from sqlalchemy.sql import func
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import secrets
import jwt

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')

# 创建数据库引擎
engine = create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")

# 创建会话工厂
Session = sessionmaker(bind=engine)

# 创建基类
Base = declarative_base()

# 定义用户类
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(512), nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, nickname={self.nickname}, email={self.email})>"

    def activate(self, session):
        """激活用户"""
        self.is_active = True
        try:
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(e)
            return False

    @classmethod
    def get_user_by_id(cls, user_id):
        """根据用户 ID 获取用户"""
        session = Session()
        try:
            user = session.query(cls).filter_by(id=user_id).first()
            return user
        except Exception as e:
            print(e)
            return None
        finally:
            session.close()

    @classmethod
    def create_user(cls, nickname, email, password):
        session = Session()
        try:
            new_user = cls(nickname=nickname, email=email, password=password)
            session.add(new_user)
            session.commit()
            session.refresh(new_user)  # 确保获取数据库生成的ID
            session.expunge(new_user)  # 将对象从会话分离
            return new_user
        except Exception as e:
            session.rollback()
            raise e  # 抛出异常供上层处理
        finally:
            session.close()

    @classmethod
    def get_user_by_email(cls, email):
        session = Session()
        try:
            # 立即加载所有需要的数据
            user = session.query(cls).options(
                load_only(cls.password)  # 明确指定需要加载的字段
            ).filter_by(email=email).first()
            if user:
                session.expunge(user)  # 将对象从会话分离
            return user
        finally:
            session.close()

# 定义任务类
class Task(Base):
    __tablename__ = 'tasks'
    task_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    task_name = Column(String(255), nullable=False)
    task_description = Column(String(255))
    status = Column(Integer, default=0)
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    @classmethod
    def create_task(cls, user_id, task_name, task_description=None):
        session = Session()
        try:
            new_task = cls(user_id=user_id, task_name=task_name, task_description=task_description)
            session.add(new_task)
            session.commit()
            session.refresh(new_task)
            session.expunge(new_task)
            return new_task
        except Exception as e:
            session.rollback()
            print(e)
            return None
        finally:
            session.close()

    @classmethod
    def get_tasks_by_user_id(cls, user_id, is_deleted=0):
        session = Session()
        try:
            tasks = session.query(cls).filter_by(user_id=user_id, is_deleted=is_deleted).all()
            return tasks
        except Exception as e:
            print(e)
            return []
        finally:
            session.close()

    @classmethod
    def mark_task_as_deleted(cls, task_id):
        session = Session()
        try:
            task = session.query(cls).filter_by(task_id=task_id).first()
            if task:
                task.is_deleted = 1
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(e)
            return False
        finally:
            session.close()

    @classmethod
    def update_task_title(cls, task_id, title):
        session = Session()
        try:
            task = session.query(cls).filter_by(task_id=task_id).first()
            if task:
                task.task_name = title
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(e)
            return False
        finally:
            session.close()

# 定义对话类
class Conversation(Base):
    __tablename__ = 'conversations'
    conversation_id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.task_id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    result = Column(String(255), nullable=False)
    sent_at = Column(DateTime, server_default=func.now())
    keywords = Column(String(255))
    is_ai = Column(Integer)
    memory = Column(String(255))
    gif = Column(String(60))
    links = Column(String(255))  # 添加 links 字段的属性定义

    @classmethod
    def create_conversation(cls, task_id, user_id, result, is_ai, keywords=None, memory=None, gif=None, links=None):
        session = Session()
        try:
            new_conversation = cls(task_id=task_id, user_id=user_id, result=result, is_ai=is_ai, keywords=keywords, memory=memory, gif=gif, links=links)
            session.add(new_conversation)
            session.commit()
            session.refresh(new_conversation)
            session.expunge(new_conversation)
            return new_conversation
        except Exception as e:
            session.rollback()
            print(e)
            return None
        finally:
            session.close()

    @classmethod
    def get_conversations_by_task_id(cls, task_id):
        session = Session()
        try:
            conversations = session.query(cls).filter_by(task_id=task_id).order_by(cls.sent_at).all()
            return conversations
        except Exception as e:
            print(e)
            return []
        finally:
            session.close()

# 定义 token 类型
class Token(Base):
    __tablename__ = 'tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    device_info = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def is_token_valid(cls, token, device_info):
        """验证 token 是否有效"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            current_time = datetime.utcnow()
            session = Session()
            token_obj = session.query(cls).filter(cls.token == token, cls.expires_at > current_time, cls.user_id == user_id, cls.device_info == device_info).first()
            session.close()
            return token_obj is not None
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return False

    @classmethod
    def create_token(cls, user_id, device_info):
        session = Session()
        try:
            expiry_days = int(os.getenv('TOKEN_EXPIRY_DAYS', 7))
            expires_at = datetime.utcnow() + timedelta(days=expiry_days)
            payload = {
                'user_id': user_id,
                'exp': expires_at
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            new_token = Token(token=token, user_id=user_id, expires_at=expires_at, device_info=device_info)
            session.add(new_token)
            session.commit()
            return token
        except Exception as e:
            session.rollback()
            print(e)
            return None
        finally:
            session.close()

# 创建表
Base.metadata.create_all(engine)