from sqlalchemy import String, Integer, Column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Mobil(Base):
    __tablename__ = "tbl_showroom_mobil"
    no = Column(Integer, primary_key=True)
    merek = Column(String)
    model = Column(String)
    harga = Column(Integer)
    konsumsi_bbm = Column(Integer)
    kapasitas_mesin = Column(Integer)
    jumlah_kursi = Column(Integer)
    kecepatan_maksimum = Column(Integer)

    def __repr__(self):
        return f"Mobil(no={self.no!r}, harga={self.harga!r}, konsumsi_bbm={self.konsumsi_bbm!r}, kapasitas_mesin={self.kapasitas_mesin!r}, jumlah_kursi={self.jumlah_kursi!r}, kecepatan_maksimum={self.kecepatan_maksimum!r})"
