import sqlite3
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_name='database/user_profiles.db'):
        self.db_path = Path(db_name)
        self._ensure_db_directory()
        
    def _ensure_db_directory(self):
        """Asegura que el directorio de la DB exista y sea escribible"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            # Verifica permisos de escritura
            test_file = self.db_path.parent / '.permission_test'
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except IOError as e:
                raise PermissionError(f"No hay permisos de escritura en {self.db_path.parent}: {e}")
        except Exception as e:
            logger.error(f"Error preparando directorio DB: {e}")
            raise

    def __enter__(self):
        """Abre conexión a la base de datos con detección de errores"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
            return self.conn.cursor()
        except sqlite3.Error as e:
            logger.error(f"Error al conectar a DB: {e}")
            raise RuntimeError(f"No se pudo conectar a la base de datos: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Manejo seguro del cierre de conexión"""
        if hasattr(self, 'conn'):
            try:
                if exc_type is None:
                    self.conn.commit()
                else:
                    logger.error(f"Rollback debido a: {exc_val}")
                    self.conn.rollback()
            finally:
                self.conn.close()

    def init_db(self):
        """Inicialización robusta de la base de datos"""
        try:
            with self as cursor:
                # Tabla de usuarios
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        age INTEGER CHECK (age > 0 AND age < 120),
                        weight REAL CHECK (weight > 0),
                        height REAL CHECK (height > 0),
                        activity_level TEXT CHECK (activity_level IN ('low', 'medium', 'high')),
                        health_goals TEXT,
                        sleep_time REAL CHECK (sleep_time > 0 AND sleep_time <= 24),
                        work_hours REAL CHECK (work_hours >= 0 AND work_hours <= 24),
                        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
                
                # Tabla de recordatorios
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        reminder_type TEXT NOT NULL,
                        interval_seconds INTEGER NOT NULL CHECK (interval_seconds > 0),
                        last_sent TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    )''')
                
                # Añadir índices para mejor performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminder_user ON reminders(user_id)')
                
            logger.info(f"Base de datos inicializada correctamente en {self.db_path}")
            return True
            
        except sqlite3.Error as e:
            logger.critical(f"Error al inicializar DB: {e}")
            return False
        except Exception as e:
            logger.critical(f"Error inesperado en init_db: {e}")
            return False