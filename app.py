from typing import Annotated

import hmac
import base64
import hashlib

import json

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models.models import *
from shemas.shemas import *

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost/session1"
SECRET_KEY = "secret_key"


app = FastAPI()
security = HTTPBearer()

error_code = 1000

engine = create_async_engine(DATABASE_URL)
new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session
        
SessionDep = Annotated[AsyncSession, Depends(get_session)]

def score_error():
    global error_code
    error_code +=1
    return error_code

async def get_user_from_db(session:SessionDep, username: str):
    query = select(UsersModel).where(UsersModel.username == username)
    result = await session.execute(query)
    return result.scalar_one_or_none()

def encode(data):
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

def create_token(payload):
    header = {"alg": "SH256", "typ": "JWT"}
    
    unsigned_token = encode(header) + "." + encode(payload)
    signature = hmac.new(SECRET_KEY.encode(), unsigned_token.encode(), hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    token = unsigned_token + "." + signature
    return token

def verfy_signature_token(token:str):
    try:
        header, payload, signature = token.split(".")
        unsigned_token = f"{header}.{payload}"
        expected_signature = hmac.new(SECRET_KEY.encode(), unsigned_token.encode(), hashlib.sha256).digest()
        expected_signature = base64.urlsafe_b64encode(expected_signature).decode().rstrip("=")
        return signature == expected_signature
    except Exception:
        return False    
    
def decode_payload(token:str):
    try:
        header, payload, signature = token.split(".")
        decoded_payload = base64.urlsafe_b64decode(payload + "==").decode()
        return json.loads(decoded_payload)
    except Exception:
        return ValueError("Неверный формат токена")
    
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    
    try:
        if verfy_signature_token(token) != True:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неподходящий формат токена"
            )
            
        payload = decode_payload(token)
        
        if datetime.now().timestamp() > payload["exp"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Срок действия токена истек"
            )
        
        return payload
    
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="НЕверный формат токена"
        )
    

@app.post("/api/v1/SignIn")
async def auth(session: SessionDep, form_data: UserShema):
    user = await get_user_from_db(session, form_data.name)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"timestamp": datetime.now().timestamp(), "messege": "Введенные данные не найдены", "error_code": score_error()}
        )
        
    if form_data.password != user.password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"timestamp": datetime.now().timestamp(), "messege": "Введенные данные неверны", "error_code": score_error()}
        )
        
    playload = {
        "user_id": user.id,
        "iat" : int(datetime.now().timestamp()),
        "exp": int((datetime.now() + timedelta(minutes=30)).timestamp())
    }
    
    acess_token = create_token(playload)
    
    return {"acess_token": acess_token, "type": "bearer"}

@app.get("/api/v1/Documents")
async def get_documents(session: SessionDep, current_user: dict = Depends(get_current_user)):
    query = select(DocumentsModel)
    result = await session.execute(query)
    return result.scalars().all()

@app.get("/api/v1/Document/{documentId}/Comments")
async def def_get_coments(session:SessionDep,  coment_id: int, curent_user: dict = Depends(get_current_user)):
    query = select(ComentsModel).where(ComentsModel.document_id == coment_id)
    result = await session.execute(query)
    result = result.scalars().all()
    if result == []:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= {
                    "timestamp": datetime.now().timestamp(),
                    "message": "Не найдены комментарии для документа",
                    "errorCode": score_error()
                    }
                )
    else:
        return result
    
@app.post("/api/v1/Document/{documentId}/Comments")
async def def_post_coment(
    session: SessionDep,
    documentId: int,
    coment_data: ComentsAddShema,
    curent_user: dict = Depends(get_current_user)
):
    # Проверяем, существует ли документ с указанным ID
    document_exists = await session.execute(
        select(ComentsModel).where(ComentsModel.document_id == documentId)
    )
    if not document_exists.scalar():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "timestamp": datetime.now().timestamp(),
                "message": "Документ не найден",
                "errorCode": score_error()
            }
        )

    # Создаем новый комментарий
    new_coment = ComentsModel(
        title=coment_data.title,
        date_created=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        date_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        author=coment_data.author.dict(),
        document_id=documentId
    )

    # Добавляем комментарий в базу данных
    session.add(new_coment)
    await session.commit()
    await session.refresh(new_coment)

    return HTTPException(
        status_code=status.HTTP_200_OK,
        detail={"message": "Коментарий добавлен успешно"}
    )
