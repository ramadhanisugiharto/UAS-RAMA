from sqlalchemy import Float
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class smartphone(Base):
    __tablename__ = 'smartphone'
    nama: Mapped[str] = mapped_column(primary_key=True)
    harga: Mapped[int] = mapped_column()
    ram: Mapped[int] = mapped_column()
    kapasitas_baterai: Mapped[int] = mapped_column()
    chipset: Mapped[int] = mapped_column()
    memori_internal: Mapped[int] = mapped_column()
    
    def __repr__(self) -> str:
        return f"smartphone(nama={self.nama!r}, harga={self.harga!r})"