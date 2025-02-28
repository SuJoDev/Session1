from typing import Annotated
from pathlib import Path

import base64
import hashlib

import json
import hmac

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from datetime import datetime, timedelta

from models.models import UsersModel
from shemas.shemas import UsersShema, DocumentComents, AuthorShema


app = FastAPI()
security = HTTPBearer()

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost/session1"

engine = create_async_engine(DATABASE_URL)
new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

SECRET_KEY = 'secret_key'

def create_token(payload):
    header = {"alg": "HS256", "typ": "JWT"}
    
    def encode(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

    unsigned_token = encode(header) + "." + encode(payload)

    signature = hmac.new(SECRET_KEY.encode(), unsigned_token.encode(), hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    token = unsigned_token + "." + signature
    return token

def verify_password(plain_password, hashed_password):
    return plain_password == hashed_password  

async def get_user_from_db(session: SessionDep, username: str):
    query = select(UsersModel).where(UsersModel.username == username)
    result = await session.execute(query)
    return result.scalar_one_or_none()

def decode_token(token: str):
    try:
        header, payload, signature = token.split(".")
        decoded_payload = base64.urlsafe_b64decode(payload + "==").decode()
        print(f"Декодированная полезная нагрузка: {decoded_payload}")
        return json.loads(decoded_payload)
    except Exception as e:
        print(f"Ошибка декодирования: {e}")
        raise ValueError("Неверный формат токена")


def verify_token_signature(token: str):
    try:
        header, payload, signature = token.split(".")
        unsigned_token = f"{header}.{payload}"
        expected_signature = hmac.new(SECRET_KEY.encode(), unsigned_token.encode(), hashlib.sha256).digest()
        expected_signature = base64.urlsafe_b64encode(expected_signature).decode().rstrip("=")
        print(f"Подпись токена: {signature}")
        print(f"Ожидаемая подпись: {expected_signature}")
        print(signature == expected_signature)
        return signature == expected_signature
    except Exception:
        return False


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    print(f"Полученный токен: {token}")
    try:
        if verify_token_signature(token) != True:
            print("Неверная подпись токена")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверная подпись токена",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = decode_token(token)
        print(f"Декодированная полезная нагрузка: {payload}")

        if datetime.now().timestamp() > payload["exp"]:
            print("Токен истек")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен истек",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/api/v1/SignIn")
async def login(session: SessionDep, form_data: UsersShema):
    user = await get_user_from_db(session, form_data.name)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"timestamp": datetime.now().timestamp(), "message": "Не найдены данные учетной записи", "errorCode": "2344"}
        )
        
    if user.password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"timestamp": datetime.now().timestamp(), "message": "Не верно введенные данные", "errorCode": "2344"}
        )
    
    payload = {
        "user_id": user.id,
        "iat": int(datetime.now().timestamp()),
        "exp": int((datetime.now() + timedelta(minutes=30)).timestamp())
    }
    
    access_token = create_token(payload)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users")
async def get_users(session: SessionDep):
    query = select(UsersModel)
    result = await session.execute(query)
    return result.scalars().all()

@app.get("/api/v1/Documents")
async def get_documents(current_user: dict = Depends(get_current_user)):
    with open('documents.json', "r", encoding="utf_8") as file:
        documents = json.load(file)
    return documents

@app.get("/api/v1/Document/{documentId}/Comments")
async def get_comments(document_id: int, current_user: dict = Depends(get_current_user)):
    with open('documents_coment.json', "r", encoding="utf_8") as file:
        comments = json.load(file)
        filtered_comments = []
        for comment in comments:
            if comment["document_id"] == document_id:
                filtered_comments.append(comment)
        return filtered_comments
    
@app.post("/api/v1/Document/{documentId}/Coment")
async def get_comment(documentId: int, coment: DocumentComents, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    with open("documents_coment.json", "r+", encoding="utf-8") as file:
        comentss = json.load(file)
        found = False
        for comment in comentss:
            if comment["id"] == documentId:
                comment["document_id"] = coment.document_id
                comment["text"] = coment.text
                comment["date_created"] = coment.date_created
                comment["date_updated"] = coment.date_updated
                found = True

        if not found:
            raise HTTPException(status_code=404, detail={"timestamp": 1716767880,"message": "Не найдены комментарии для документа","errorCode": "2344"})

        file.seek(0)
        json.dump(comentss, file, ensure_ascii=False, indent=4)
        file.truncate()
    
    return {"message": "Комментарий обновлён", "document_id": documentId}
