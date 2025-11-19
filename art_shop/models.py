from typing import Optional
from sqlmodel import Field, SQLModel

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    price: int
    image_url: str  # Путь к картинке
