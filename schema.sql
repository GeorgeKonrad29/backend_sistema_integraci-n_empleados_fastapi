PRAGMA foreign_keys = ON;

-- Limpieza de tablas para pruebas (Opcional, comentar en producción)
-- DROP TABLE IF EXISTS HISTORIAL;
-- DROP TABLE IF EXISTS SOLICITUDES;
-- DROP TABLE IF EXISTS PUESTO_TRABAJO;
-- DROP TABLE IF EXISTS USUARIO;
-- DROP TABLE IF EXISTS CARGOS;

-- 1. Estructura Organizacional
CREATE TABLE CARGOS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_cargo TEXT NOT NULL,
    area TEXT NOT NULL, 
    id_jefe_inmediato INTEGER,
    FOREIGN KEY (id_jefe_inmediato) REFERENCES CARGOS(id)
);

-- 2. Usuarios y Empleados (Correo es UNIQUE)
CREATE TABLE USUARIO (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Correo TEXT UNIQUE NOT NULL,
    Contrasena TEXT NOT NULL, 
    rol_sistema TEXT CHECK(rol_sistema IN ('Root', 'Administrador', 'Jefe Inmediato', 'Operador')), 
    nombre TEXT NOT NULL,
    id_cargo INTEGER,
    estado_onboarding TEXT CHECK (estado_onboarding IN ('Finalizado', 'En Proceso', 'Pendiente')) DEFAULT 'Pendiente',
    FOREIGN KEY (id_cargo) REFERENCES CARGOS(id)
);

-- 3. Puestos de trabajo
CREATE TABLE PUESTO_TRABAJO (
    id_puesto INTEGER PRIMARY KEY AUTOINCREMENT,
    coordenadas TEXT NOT NULL, 
    id_empleado_asignado INTEGER UNIQUE,
    estado_ocupacion TEXT CHECK(estado_ocupacion IN ('Disponible', 'Ocupado')) DEFAULT 'Disponible',
    FOREIGN KEY (id_empleado_asignado) REFERENCES USUARIO(ID)
);

-- 4. Solicitudes (Control de SLA)
CREATE TABLE SOLICITUDES (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_empleado INTEGER NOT NULL,
    id_area_encargada TEXT NOT NULL, 
    fecha_creacion TEXT DEFAULT (datetime('now')),
    fecha_maxima_cumplimiento TEXT NOT NULL,
    fecha_fin TEXT,
    estado TEXT CHECK(estado IN ('Pendiente', 'En Proceso', 'Finalizado')) DEFAULT 'Pendiente',
    especificaciones TEXT, 
    FOREIGN KEY (id_empleado) REFERENCES USUARIO(ID)
);

-- 5. Historial
CREATE TABLE HISTORIAL (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_solicitud INTEGER,
    fecha_cambio TEXT DEFAULT (datetime('now')),
    estado_antiguo TEXT,
    nuevo_estado TEXT,
    comentario TEXT,
    FOREIGN KEY (id_solicitud) REFERENCES SOLICITUDES(id)
);

---
-- AUTOMATIZACIÓN: Trigger para el historial
---
CREATE TRIGGER IF NOT EXISTS trg_actualizar_historial
AFTER UPDATE OF estado ON SOLICITUDES
BEGIN
    INSERT INTO HISTORIAL (id_solicitud, estado_antiguo, nuevo_estado, comentario)
    VALUES (OLD.id, OLD.estado, NEW.estado, 'Cambio de estado automático');
END;