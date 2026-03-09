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

-- INSERCION DE JERARQUIA
-- -- 1. INSERCIÓN DE JERARQUIA DE ALTA GERENCIA (Reportan al Gerente General o Asamblea)
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (1, 'Gerente General', 'Gerencia General', NULL);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (2, 'Gerente Administrativo', 'Gerencia Administracion', 1);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (3, 'Gerente Comercial', 'Gerencia Comercial', 1);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (4, 'Gerente de Riesgo y Crédito', 'Gerencia Riesgo y Crédito', 1);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (5, 'Gerente de Finanzas', 'Gerencia Finanzas', 1);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (6, 'Gerente de TI', 'Gerencia TI', 1);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (7, 'Gerente de Talento Humano', 'Gerencia Talento Humano', 1);

-- 2. GERENCIA DE ADMINISTRACIÓN
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Coordinador de Servicios Corporativos', 'Servicios Generales', 2);
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Auxiliar de Mantenimiento', 'Mantenimiento', 8); -- Reporta al Coordinador

-- 3. GERENCIA COMERCIAL
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Jefe de Ventas', 'Ventas y Captación', 3);
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Asesor Comercial', 'Ventas y Captación', 10);
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Coordinador de Canales Digitales', 'Gestión de Canales', 3);

-- 4. GERENCIA DE RIESGO Y CRÉDITO
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Jefe de Análisis de Crédito', 'Análisis de crédito', 4);
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Analista de Crédito Senior', 'Análisis de crédito', 13);
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Oficial de Riesgo Operativo', 'Riesgo Operativo', 4);

-- 5. GERENCIA DE FINANZAS
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Coordinador de Tesorería', 'Tesorería', 5);
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Analista de Tesorería', 'Tesorería', 16);
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Contador General', 'Contabilidad', 5);
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Auxiliar Contable', 'Contabilidad', 18);

-- 6. GERENCIA DE TI
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Jefe de Infraestructura', 'Infraestructura y redes', 6);
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Ingeniero de Soporte', 'Soporte', 20);
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Líder de Desarrollo', 'Desarrollo', 6);
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Analista Programador', 'Desarrollo', 22);

-- 7. GERENCIA DE TALENTO HUMANO
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Jefe de Selección', 'Selección y reclutamiento', 7);
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Especialista de Formación', 'Formación y capacitación', 7);
INSERT INTO JERARQUIA (nombre_cargo, area, id_jefe_inmediato) VALUES ('Analista de Nómina', 'Nómina', 7);
