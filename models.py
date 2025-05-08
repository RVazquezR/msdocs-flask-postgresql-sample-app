from sqlalchemy import Column, DateTime, Integer, LargeBinary, String
from app import db

class ImagenProcesada(db.Model):
    __tablename__ = 'imagen_procesada'
    id = Column(Integer, primary_key=True)
    usuario = Column(String(50))
    nombre_archivo = Column(String(100))
    rojo = Column(Integer)
    verde = Column(Integer)
    azul = Column(Integer)
    fecha_hora = Column(DateTime)
 

    def __str__(self):
        return f"{self.usuario} - {self.nombre_archivo} ({self.fecha_hora})"
