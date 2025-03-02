from sqlalchemy.orm import DeclarativeBase, Mapped,  mapped_column
from sqlalchemy import ForeignKey, JSON


class Base(DeclarativeBase):
    pass

class UsersModel(Base):
    __tablename__ = "Users"
    
    id: Mapped[int] = mapped_column(primary_key= True, autoincrement= True)
    username: Mapped[str] = mapped_column()
    password: Mapped[str] = mapped_column()
    
class DocumentsModel(Base):
    __tablename__ = "Documents"
    
    id:Mapped[int] = mapped_column(primary_key=True, autoincrement= True)
    title: Mapped[str] = mapped_column()
    date_created: Mapped[str] = mapped_column()
    date_updated: Mapped[str] = mapped_column()
    category: Mapped[str] = mapped_column()
    has_coment: Mapped[bool] = mapped_column()
    
class ComentsModel(Base):
    __tablename__ = "Coments"
    
    id: Mapped[int] = mapped_column(primary_key= True, autoincrement= True)
    title: Mapped[str] = mapped_column()
    date_created: Mapped[str] = mapped_column()
    date_updated: Mapped[str] = mapped_column()
    author: Mapped[JSON] = mapped_column(JSON)
    document_id: Mapped[int] = mapped_column(ForeignKey("Documents.id"))
