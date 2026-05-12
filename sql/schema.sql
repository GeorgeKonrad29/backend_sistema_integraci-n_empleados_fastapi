PRAGMA foreign_keys = ON;

-- 1. Estructura Organizacional
CREATE TABLE JERARQUIA (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_cargo TEXT NOT NULL,
    area TEXT NOT NULL,
    id_jefe_inmediato INTEGER,
    FOREIGN KEY (id_jefe_inmediato) REFERENCES JERARQUIA(id)
    );

-- 2. Usuario
CREATE TABLE USUARIO (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE,
    contrasena TEXT NOT NULL,
    rol TEXT CHECK(rol in ('Root', 'Administrador', 'Encargado de Area', 'Operador')) DEFAULT 'Operador',
    cargo INTEGER,
    estado_onboarding TEXT CHECK(estado_onboarding IN('Finalizado', 'En proceso', 'Pendiente')) DEFAULT 'Pendiente',
    FOREIGN KEYS (cargo) REFERENCES JERARQUIA (id)
    );

-- 3. Puesto de trabajo y su tipo
CREATE TABLE PUESTO_DE_TRABAJO (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coordenadas TEXT NOT NULL,
    id_empleado INTEGER,
    tipo_puesto TEXT,
    FOREIGN KEY (id_empleado) REFERENCES USUARIO(id)
    );

-- 4. dotacion (implementos y curso)
CREATE TABLE DOTACION (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    encargado TEXT,
    tipo TEXT,
    especificacion TEXT
    );

-- 5. Solicitudes de dotacion
CREATE TABLE SOLICITUDES (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_empleado INTEGER,
    fecha_creacion TEXT NOT NULL,
    fecha_fin TEXT NOT NULL,
    estado TEXT,
    especificaciones TEXT,
    destinatario TEXT,
    FOREIGN KEY (id_empleado) REFERENCES USUARIO(id)
    );

-- 6. Historial de solicitudes
CREATE TABLE HISTORIAL (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_solicitud INTEGER,
    fecha_cambio TEXT NOT NULL,
    tipo_cambio TEXT NOT NULL,
    estado_antiguo TEXT,
    nuevo_estado TEXT,
    FOREIGN KEY (id_solicitud) REFERENCES SOLICITUDES(id)
    );

